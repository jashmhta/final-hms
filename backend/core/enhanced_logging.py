import json
import logging
import logging.config
import time
from datetime import datetime
from typing import Any, Dict, Optional

from django.conf import settings
from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "hospital_id"):
            log_entry["hospital_id"] = record.hospital_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "duration"):
            log_entry["duration_ms"] = record.duration
        if hasattr(record, "extra"):
            log_entry.update(record.extra)
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }
        return json.dumps(log_entry, default=str)


class PerformanceLogger:
    def __init__(self, logger_name="hms.performance"):
        self.logger = logging.getLogger(logger_name)

    def log_query_performance(self, query: str, duration: float, context: Dict[str, Any]):
        self.logger.info(
            f"Database query executed",
            extra={
                "query": query[:1000],
                "duration_ms": duration * 1000,
                "context": context,
            },
        )

    def log_api_call(
        self,
        method: str,
        endpoint: str,
        duration: float,
        status_code: int,
        user_id: Optional[int] = None,
    ):
        self.logger.info(
            f"API call completed",
            extra={
                "method": method,
                "endpoint": endpoint,
                "duration_ms": duration * 1000,
                "status_code": status_code,
                "user_id": user_id,
            },
        )

    def log_cache_operation(self, operation: str, key: str, hit: bool, duration: float):
        self.logger.debug(
            f"Cache operation",
            extra={
                "operation": operation,
                "key": key,
                "hit": hit,
                "duration_ms": duration * 1000,
            },
        )


class RequestLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.performance_logger = PerformanceLogger()

    def process_request(self, request: HttpRequest):
        request.start_time = time.time()
        request.request_id = request.META.get("HTTP_X_REQUEST_ID", f"req_{int(time.time() * 1000)}")
        logger = logging.getLogger("hms.requests")
        logger.info(
            f"Request started",
            extra={
                "request_id": request.request_id,
                "method": request.method,
                "path": request.path,
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "ip": self.get_client_ip(request),
                "user_id": (getattr(request.user, "id", None) if hasattr(request.user, "id") else None),
            },
        )

    def process_response(self, request: HttpRequest, response):
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            self.performance_logger.log_api_call(
                method=request.method,
                endpoint=request.path,
                duration=duration,
                status_code=response.status_code,
                user_id=(getattr(request.user, "id", None) if hasattr(request.user, "id") else None),
            )
            response["X-Response-Time"] = f"{duration:.3f}s"
            response["X-Request-ID"] = request.request_id
            logger = logging.getLogger("hms.requests")
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request.request_id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": duration * 1000,
                    "response_size": (len(response.content) if hasattr(response, "content") else 0),
                },
            )
        return response

    def get_client_ip(self, request: HttpRequest) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class QueryLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.performance_logger = PerformanceLogger()
        self.slow_query_threshold = 0.5

    def process_response(self, request: HttpRequest, response):
        if hasattr(request, "queries"):
            for query in request.queries:
                duration = float(query["time"])
                if duration > self.slow_query_threshold:
                    self.performance_logger.log_query_performance(
                        query["sql"],
                        duration,
                        {
                            "request_id": getattr(request, "request_id", None),
                            "path": request.path,
                            "method": request.method,
                        },
                    )
        return response


def setup_logging():
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "verbose": {
                "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if settings.DEBUG else "json",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "/app/logs/hms.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "json",
            },
            "performance": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "/app/logs/performance.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "json",
            },
            "security": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "/app/logs/security.log",
                "maxBytes": 10485760,
                "backupCount": 10,
                "formatter": "json",
            },
        },
        "loggers": {
            "hms": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "hms.performance": {
                "handlers": ["performance"],
                "level": "INFO",
                "propagate": False,
            },
            "hms.requests": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False,
            },
            "hms.security": {
                "handlers": ["security"],
                "level": "WARNING",
                "propagate": False,
            },
            "django": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
            "django.db.backends": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False,
            },
            "django.security": {
                "handlers": ["security"],
                "level": "WARNING",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)


performance_logger = PerformanceLogger()
if not settings.DEBUG:
    setup_logging()
