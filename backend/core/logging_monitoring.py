"""
logging_monitoring module
"""

import json
import logging
import logging.config
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil
import redis
from prometheus_client import REGISTRY, Counter, Gauge, Histogram, generate_latest
from requests.exceptions import RequestException
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.response import Response
from rest_framework.views import exception_handler

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError
from django.http import HttpRequest, JsonResponse


# Custom formatters
class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }

        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "hospital_id"):
            log_entry["hospital_id"] = record.hospital_id
        if hasattr(record, "action"):
            log_entry["action"] = record.action
        if hasattr(record, "resource"):
            log_entry["resource"] = record.resource
        if hasattr(record, "ip_address"):
            log_entry["ip_address"] = record.ip_address
        if hasattr(record, "user_agent"):
            log_entry["user_agent"] = record.user_agent
        if hasattr(record, "response_time"):
            log_entry["response_time"] = record.response_time
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry)


# Prometheus metrics
REQUEST_COUNT = Counter(
    "hms_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "user_role"],
)

REQUEST_DURATION = Histogram(
    "hms_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint", "user_role"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

DB_QUERY_COUNT = Counter(
    "hms_db_queries_total",
    "Total database queries",
    ["model", "operation", "hospital_id"],
)

DB_QUERY_DURATION = Histogram(
    "hms_db_query_duration_seconds",
    "Database query duration",
    ["model", "operation", "hospital_id"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
)

CACHE_HIT_RATE = Gauge(
    "hms_cache_hit_rate", "Cache hit rate by type", ["cache_type", "hospital_id"]
)

ERROR_COUNT = Counter(
    "hms_errors_total", "Total errors", ["type", "module", "user_role"]
)

ACTIVE_USERS = Gauge("hms_active_users", "Active users", ["hospital_id", "user_role"])

SYSTEM_METRICS = {
    "cpu_usage": Gauge("hms_system_cpu_percent", "CPU usage percentage"),
    "memory_usage": Gauge("hms_system_memory_percent", "Memory usage percentage"),
    "disk_usage": Gauge("hms_system_disk_percent", "Disk usage percentage"),
    "redis_connections": Gauge("hms_redis_connections", "Active Redis connections"),
    "database_connections": Gauge(
        "hms_database_connections", "Active database connections"
    ),
}

# Loggers
access_logger = logging.getLogger("hms.access")
audit_logger = logging.getLogger("hms.audit")
security_logger = logging.getLogger("hms.security")
performance_logger = logging.getLogger("hms.performance")
error_logger = logging.getLogger("hms.error")
business_logger = logging.getLogger("hms.business")


class LoggingMiddleware:
    """Middleware for comprehensive request logging and monitoring"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.redis_client = self._get_redis_client()

    def _get_redis_client(self):
        try:
            if hasattr(settings, "CACHES") and "default" in settings.CACHES:
                import redis

                return redis.from_url(settings.CACHES["default"]["LOCATION"])
        except Exception:
            return None

    def __call__(self, request: HttpRequest):
        # Generate request ID
        request_id = self._generate_request_id()
        request.request_id = request_id

        # Start timing
        start_time = time.time()

        # Extract user info
        user = getattr(request, "user", None)
        user_id = getattr(user, "id", None) if user and user.is_authenticated else None
        user_role = (
            getattr(user, "role", None)
            if user and user.is_authenticated
            else "anonymous"
        )
        hospital_id = (
            getattr(user, "hospital_id", None)
            if user and user.is_authenticated
            else None
        )

        # Get client info
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Log request start
        self._log_request_start(
            request, request_id, user_id, user_role, hospital_id, ip_address, user_agent
        )

        try:
            response = self.get_response(request)

            # Calculate response time
            response_time = time.time() - start_time

            # Update Prometheus metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.path,
                status_code=response.status_code,
                user_role=user_role,
            ).inc()

            REQUEST_DURATION.labels(
                method=request.method, endpoint=request.path, user_role=user_role
            ).observe(response_time)

            # Log request completion
            self._log_request_end(
                request,
                response,
                request_id,
                user_id,
                user_role,
                hospital_id,
                ip_address,
                user_agent,
                response_time,
            )

            # Add request ID to response headers
            response["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate response time for errors
            response_time = time.time() - start_time

            # Log error
            self._log_error(
                e,
                request,
                request_id,
                user_id,
                user_role,
                hospital_id,
                ip_address,
                user_agent,
            )

            # Update error metrics
            ERROR_COUNT.labels(
                type=type(e).__name__, module="middleware", user_role=user_role
            ).inc()

            # Re-raise the exception
            raise

    def _generate_request_id(self):
        """Generate unique request ID"""
        import uuid

        return str(uuid.uuid4())

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def _log_request_start(
        self,
        request,
        request_id,
        user_id,
        user_role,
        hospital_id,
        ip_address,
        user_agent,
    ):
        """Log request start"""
        access_logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "user_role": user_role,
                "hospital_id": hospital_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "method": request.method,
                "path": request.path,
                "query_params": dict(request.GET),
                "action": "request_start",
            },
        )

    def _log_request_end(
        self,
        request,
        response,
        request_id,
        user_id,
        user_role,
        hospital_id,
        ip_address,
        user_agent,
        response_time,
    ):
        """Log request completion"""
        access_logger.info(
            f"Request completed: {request.method} {request.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "user_role": user_role,
                "hospital_id": hospital_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "response_time": response_time,
                "action": "request_end",
            },
        )

        # Log slow requests
        if response_time > 2.0:  # More than 2 seconds
            performance_logger.warning(
                f"Slow request detected: {request.method} {request.path}",
                extra={
                    "request_id": request_id,
                    "response_time": response_time,
                    "threshold": 2.0,
                    "method": request.method,
                    "path": request.path,
                    "action": "slow_request",
                },
            )

    def _log_error(
        self,
        error,
        request,
        request_id,
        user_id,
        user_role,
        hospital_id,
        ip_address,
        user_agent,
    ):
        """Log request error"""
        error_logger.error(
            f"Request error: {request.method} {request.path} - {type(error).__name__}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "user_role": user_role,
                "hospital_id": hospital_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "method": request.method,
                "path": request.path,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "action": "request_error",
            },
        )


class AuditLogger:
    """Comprehensive audit logging for compliance"""

    @staticmethod
    def log_action(
        user,
        action: str,
        resource: str = None,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        success: bool = True,
    ):
        """Log user actions for audit purposes"""

        user_id = getattr(user, "id", None) if user else None
        user_role = getattr(user, "role", None) if user else None
        hospital_id = getattr(user, "hospital_id", None) if user else None

        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "user_role": user_role,
            "hospital_id": hospital_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        if details:
            audit_data["details"] = details

        audit_logger.info(f"Audit log: {action} on {resource}", extra=audit_data)

    @staticmethod
    def log_data_access(
        user,
        data_type: str,
        operation: str,
        record_id: str = None,
        success: bool = True,
        ip_address: str = None,
    ):
        """Log sensitive data access for HIPAA compliance"""

        user_id = getattr(user, "id", None) if user else None
        user_role = getattr(user, "role", None) if user else None
        hospital_id = getattr(user, "hospital_id", None) if user else None

        security_logger.info(
            f"Data access: {operation} on {data_type}",
            extra={
                "user_id": user_id,
                "user_role": user_role,
                "hospital_id": hospital_id,
                "data_type": data_type,
                "operation": operation,
                "record_id": record_id,
                "success": success,
                "ip_address": ip_address,
                "action": "data_access",
                "resource": data_type,
            },
        )

    @staticmethod
    def log_security_event(
        event_type: str,
        severity: str = "medium",
        description: str = None,
        user=None,
        ip_address: str = None,
        details: Dict[str, Any] = None,
    ):
        """Log security events"""

        user_id = getattr(user, "id", None) if user else None
        user_role = getattr(user, "role", None) if user else None

        security_logger.warning(
            f"Security event: {event_type}",
            extra={
                "event_type": event_type,
                "severity": severity,
                "description": description,
                "user_id": user_id,
                "user_role": user_role,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
                "action": "security_event",
                "details": details,
            },
        )


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""

    @staticmethod
    @contextmanager
    def monitor_database_operation(
        model_name: str, operation: str, hospital_id: str = None
    ):
        """Monitor database operation performance"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time

            DB_QUERY_COUNT.labels(
                model=model_name,
                operation=operation,
                hospital_id=hospital_id or "unknown",
            ).inc()

            DB_QUERY_DURATION.labels(
                model=model_name,
                operation=operation,
                hospital_id=hospital_id or "unknown",
            ).observe(duration)

    @staticmethod
    def log_cache_operation(
        cache_type: str,
        operation: str,
        hit: bool = False,
        key: str = None,
        hospital_id: str = None,
    ):
        """Log cache operations"""
        performance_logger.info(
            f"Cache {operation}: {cache_type}",
            extra={
                "cache_type": cache_type,
                "operation": operation,
                "hit": hit,
                "key": key,
                "hospital_id": hospital_id,
                "action": "cache_operation",
            },
        )

    @staticmethod
    def update_system_metrics():
        """Update system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_METRICS["cpu_usage"].set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_METRICS["memory_usage"].set(memory.percent)

            # Disk usage
            disk = psutil.disk_usage("/")
            SYSTEM_METRICS["disk_usage"].set(disk.percent)

            # Redis connections (if available)
            try:
                if hasattr(settings, "CACHES") and "default" in settings.CACHES:
                    redis_client = redis.from_url(
                        settings.CACHES["default"]["LOCATION"]
                    )
                    info = redis_client.info()
                    SYSTEM_METRICS["redis_connections"].set(
                        info.get("connected_clients", 0)
                    )
            except Exception:
                pass

            performance_logger.debug(
                "System metrics updated",
                extra={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "action": "system_metrics",
                },
            )
        except Exception as e:
            error_logger.error(f"Error updating system metrics: {str(e)}")


class HealthChecker:
    """System health monitoring and alerts"""

    @staticmethod
    def check_database_health() -> Dict[str, Any]:
        """Check database health"""
        try:
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return {
                    "status": "healthy",
                    "response_time": cursor.connection.total_time,
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    def check_redis_health() -> Dict[str, Any]:
        """Check Redis health"""
        try:
            if hasattr(settings, "CACHES") and "default" in settings.CACHES:
                redis_client = redis.from_url(settings.CACHES["default"]["LOCATION"])
                redis_client.ping()
                return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
        return {"status": "not_configured"}

    @staticmethod
    def check_system_health() -> Dict[str, Any]:
        """Check overall system health"""
        health_status = {
            "database": HealthChecker.check_database_health(),
            "redis": HealthChecker.check_redis_health(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Overall health status
        unhealthy_services = [
            service
            for service, status in health_status.items()
            if isinstance(status, dict) and status.get("status") == "unhealthy"
        ]

        health_status["overall"] = "healthy" if not unhealthy_services else "unhealthy"
        health_status["unhealthy_services"] = unhealthy_services

        return health_status


# Custom exception handler with enhanced logging
def custom_exception_handler(exc, context):
    """Enhanced exception handler with comprehensive logging"""

    request = context.get("request")
    user = getattr(request, "user", None) if request else None

    # Extract request information
    request_id = getattr(request, "request_id", None) if request else None
    ip_address = LoggingMiddleware(None)._get_client_ip(request) if request else None
    user_agent = request.META.get("HTTP_USER_AGENT", "") if request else None

    # Get user information
    user_id = getattr(user, "id", None) if user and user.is_authenticated else None
    user_role = (
        getattr(user, "role", None) if user and user.is_authenticated else "anonymous"
    )
    hospital_id = (
        getattr(user, "hospital_id", None) if user and user.is_authenticated else None
    )

    # Log the exception
    error_logger.error(
        f"Exception occurred: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "user_role": user_role,
            "hospital_id": hospital_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "action": "exception",
            "request_path": request.path if request else None,
            "request_method": request.method if request else None,
        },
        exc_info=True,
    )

    # Update error metrics
    ERROR_COUNT.labels(
        type=type(exc).__name__,
        module=getattr(context.get("view"), "__module__", "unknown"),
        user_role=user_role,
    ).inc()

    # Log security events for certain exceptions
    if isinstance(exc, (AuthenticationFailed, PermissionDenied, DRFPermissionDenied)):
        AuditLogger.log_security_event(
            event_type=(
                "authentication_failure"
                if isinstance(exc, AuthenticationFailed)
                else "authorization_failure"
            ),
            severity="high",
            description=f"Security violation: {str(exc)}",
            user=user,
            ip_address=ip_address,
            details={"path": request.path if request else None},
        )

    # Call DRF's default exception handler
    response = exception_handler(exc, context)

    if response is None:
        # Handle unhandled exceptions
        error_data = {
            "status": "error",
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": request_id,
        }

        if settings.DEBUG:
            error_data["debug"] = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            }

        return JsonResponse(error_data, status=500)

    # Enhance response with additional information
    if isinstance(response.data, dict):
        response.data["request_id"] = request_id

        if settings.DEBUG:
            response.data["debug"] = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            }

    return response


# Business event logging
class BusinessEventLogger:
    """Logger for business-specific events"""

    @staticmethod
    def log_patient_event(
        event_type: str, patient_id: str, user, details: Dict[str, Any] = None
    ):
        """Log patient-related events"""
        user_id = getattr(user, "id", None) if user else None
        user_role = getattr(user, "role", None) if user else None
        hospital_id = getattr(user, "hospital_id", None) if user else None

        business_logger.info(
            f"Patient event: {event_type}",
            extra={
                "event_type": event_type,
                "patient_id": patient_id,
                "user_id": user_id,
                "user_role": user_role,
                "hospital_id": hospital_id,
                "details": details,
                "action": "patient_event",
                "resource": "patient",
            },
        )

    @staticmethod
    def log_appointment_event(
        event_type: str, appointment_id: str, user, details: Dict[str, Any] = None
    ):
        """Log appointment-related events"""
        user_id = getattr(user, "id", None) if user else None
        user_role = getattr(user, "role", None) if user else None
        hospital_id = getattr(user, "hospital_id", None) if user else None

        business_logger.info(
            f"Appointment event: {event_type}",
            extra={
                "event_type": event_type,
                "appointment_id": appointment_id,
                "user_id": user_id,
                "user_role": user_role,
                "hospital_id": hospital_id,
                "details": details,
                "action": "appointment_event",
                "resource": "appointment",
            },
        )

    @staticmethod
    def log_billing_event(
        event_type: str, bill_id: str, user, details: Dict[str, Any] = None
    ):
        """Log billing-related events"""
        user_id = getattr(user, "id", None) if user else None
        user_role = getattr(user, "role", None) if user else None
        hospital_id = getattr(user, "hospital_id", None) if user else None

        business_logger.info(
            f"Billing event: {event_type}",
            extra={
                "event_type": event_type,
                "bill_id": bill_id,
                "user_id": user_id,
                "user_role": user_role,
                "hospital_id": hospital_id,
                "details": details,
                "action": "billing_event",
                "resource": "billing",
            },
        )


# Setup logging configuration
def setup_logging():
    """Setup comprehensive logging configuration"""

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonFormatter,
            },
            "verbose": {
                "format": "[{levelname}] {asctime} {name} {process:d} {thread:d} {message}",
                "style": "{",
            },
            "simple": {
                "format": "{levelname} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if not settings.DEBUG else "verbose",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.BASE_DIR / "logs" / "hms.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json",
            },
            "audit_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.BASE_DIR / "logs" / "audit.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "formatter": "json",
            },
            "security_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.BASE_DIR / "logs" / "security.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "formatter": "json",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.BASE_DIR / "logs" / "error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json",
            },
        },
        "loggers": {
            "hms.access": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "hms.audit": {
                "handlers": ["console", "audit_file"],
                "level": "INFO",
                "propagate": False,
            },
            "hms.security": {
                "handlers": ["console", "security_file"],
                "level": "INFO",
                "propagate": False,
            },
            "hms.performance": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "hms.error": {
                "handlers": ["console", "error_file"],
                "level": "ERROR",
                "propagate": False,
            },
            "hms.business": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "django.db.backends": {
                "handlers": ["console"],
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "propagate": False,
            },
            "django": {
                "handlers": ["console", "file"],
                "level": "INFO" if not settings.DEBUG else "DEBUG",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }

    # Create logs directory if it doesn't exist
    log_dir = settings.BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)

    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)


# Initialize logging
setup_logging()

# Export for use in other modules
__all__ = [
    "AuditLogger",
    "PerformanceMonitor",
    "HealthChecker",
    "BusinessEventLogger",
    "custom_exception_handler",
    "LoggingMiddleware",
    "SYSTEM_METRICS",
    "generate_latest",
]
