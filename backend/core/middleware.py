"""
middleware module
"""

import logging
import threading
import time
import uuid
from typing import Optional

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

_request_local = threading.local()


def get_request_id() -> Optional[str]:
    return getattr(_request_local, "request_id", None)


class RequestIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        rid = request.META.get("HTTP_X_REQUEST_ID") or str(uuid.uuid4())
        _request_local.request_id = rid
        request.request_id = rid

    def process_response(self, request, response):
        rid = getattr(request, "request_id", None) or get_request_id()
        if rid:
            response["X-Request-ID"] = rid
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.setdefault("Content-Security-Policy", csp)
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-Frame-Options", "DENY")
        response.setdefault("X-XSS-Protection", "1; mode=block")
        response.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), magnetometer=(), gyroscope=(), accelerometer=()",
        )
        return response


class SecurityAuditMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("security.audit")

    def __call__(self, request):
        self.log_request(request)
        response = self.get_response(request)
        self.log_response(request, response)
        return response

    def log_request(self, request):
        user = getattr(request, "user", None)
        user_id = user.id if user and user.is_authenticated else None
        self.logger.info(
            "Request received",
            extra={
                "request_id": getattr(request, "request_id", None),
                "user_id": user_id,
                "method": request.method,
                "path": request.path,
                "ip": self.get_client_ip(request),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "query_params": dict(request.GET),
            },
        )

    def log_response(self, request, response):
        user = getattr(request, "user", None)
        user_id = user.id if user and user.is_authenticated else None
        if response.status_code >= 400:
            self.logger.warning(
                f"Response {response.status_code}",
                extra={
                    "request_id": getattr(request, "request_id", None),
                    "user_id": user_id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "ip": self.get_client_ip(request),
                },
            )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class RateLimitMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.burst_limits = {
            "login": (5, 300),
            "api": (100, 60),
            "search": (20, 60),
        }

    def __call__(self, request):
        if not self.check_rate_limit(request):
            from django.http import HttpResponseTooManyRequests

            return HttpResponseTooManyRequests("Rate limit exceeded")
        response = self.get_response(request)
        return response

    def check_rate_limit(self, request):
        from django.core.cache import cache

        ip = self.get_client_ip(request)
        path = request.path
        if "/login" in path or "/auth" in path:
            limit_type = "login"
        elif "/search" in path:
            limit_type = "search"
        else:
            limit_type = "api"
        max_requests, window = self.burst_limits[limit_type]
        cache_key = f"ratelimit:{ip}:{limit_type}"
        current = cache.get(cache_key, 0)
        if current >= max_requests:
            return False
        cache.set(cache_key, current + 1, window)
        return True

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class APICacheMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("api.cache")
        self.cacheable_methods = ["GET", "HEAD"]
        self.cache_timeout = 300
        self.cache_prefix = "api_cache"

    def __call__(self, request):
        if request.method not in self.cacheable_methods:
            return self.get_response(request)
        if hasattr(request, "user") and request.user.is_authenticated:
            return self.get_response(request)
        if self.should_skip_cache(request):
            return self.get_response(request)
        cache_key = self.generate_cache_key(request)
        cached_response = cache.get(cache_key)
        if cached_response:
            self.logger.debug(f"Cache hit for {request.path}")
            return cached_response
        response = self.get_response(request)
        if response.status_code == 200 and hasattr(response, "content"):
            cache.set(cache_key, response, self.cache_timeout)
            self.logger.debug(f"Cached response for {request.path}")
        return response

    def should_skip_cache(self, request):
        skip_paths = ["/api/auth/", "/api/login/", "/api/logout/", "/admin/"]
        return any(request.path.startswith(path) for path in skip_paths)

    def generate_cache_key(self, request):
        from urllib.parse import urlencode

        key_data = {
            "path": request.path,
            "query": urlencode(request.GET),
            "accept": request.META.get("HTTP_ACCEPT", ""),
        }
        key_string = f"{self.cache_prefix}:{hash(str(key_data))}"
        return key_string


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("performance.monitor")

    def __call__(self, request):
        start_time = time.time()
        request.start_time = start_time
        response = self.get_response(request)
        duration = time.time() - start_time
        response["X-Response-Time"] = f"{duration:.3f}s"
        if duration > 1.0:
            self.logger.warning(
                f"Slow request: {request.method} {request.path} took {duration:.3f}s",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "duration": duration,
                    "status_code": response.status_code,
                    "user_id": (
                        getattr(request.user, "id", None)
                        if hasattr(request, "user")
                        else None
                    ),
                },
            )
        return response
