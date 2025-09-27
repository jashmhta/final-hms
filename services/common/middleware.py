"""
Common middleware for HMS microservices
Performance monitoring, authentication, and request handling
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from typing import Any, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from .correlation_id import CorrelationIDMiddleware, get_correlation_id
from .otel_config import get_meter, get_otel_config, get_tracer

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "service"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint", "service"],
    buckets=[
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
    ],
)

ACTIVE_REQUESTS = Gauge("http_active_requests", "Active HTTP requests", ["service"])

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "status_code", "error_type", "service"],
)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and metrics collection"""

    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        self.request_times = defaultdict(list)
        self.error_counts = defaultdict(int)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Increment active requests
        ACTIVE_REQUESTS.labels(service=self.service_name).inc()

        # Get correlation ID
        correlation_id = get_correlation_id()

        # Start timing
        start_time = time.time()

        # Get OpenTelemetry tracer
        tracer = get_tracer()
        span = None

        if tracer:
            span = tracer.start_span(
                f"{request.method} {request.url.path}",
                attributes={
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "http.scheme": request.url.scheme,
                    "http.host": request.url.hostname,
                    "correlation.id": correlation_id,
                    "service.name": self.service_name,
                },
            )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                service=self.service_name,
            ).inc()

            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path,
                service=self.service_name,
            ).observe(duration)

            # Record in OpenTelemetry
            if span:
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute(
                    "http.response.size", response.headers.get("content-length", 0)
                )
                span.set_attribute("response.duration_ms", duration * 1000)

            # Check for slow requests
            if duration > 1.0:  # Slow request threshold
                logger.warning(
                    "Slow request detected",
                    method=request.method,
                    path=request.url.path,
                    duration=duration,
                    correlation_id=correlation_id,
                )

            return response

        except Exception as e:
            # Calculate duration even on error
            duration = time.time() - start_time

            # Record error metrics
            ERROR_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                error_type=type(e).__name__,
                service=self.service_name,
            ).inc()

            # Log error with correlation ID
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                correlation_id=correlation_id,
                duration=duration,
            )

            # Record in OpenTelemetry
            if span:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("http.status_code", 500)

            # Return error response
            return JSONResponse(
                {"error": "Internal server error", "correlation_id": correlation_id},
                status_code=500,
            )

        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.labels(service=self.service_name).dec()

            # End span
            if span:
                span.end()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with different strategies"""

    def __init__(
        self,
        app,
        rate_limit: int = 100,  # requests per minute
        window_size: int = 60,  # seconds
        strategies: list = None,
    ):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_size = window_size
        self.strategies = strategies or ["ip", "user", "endpoint"]
        self.requests = defaultdict(list)
        self.cleanup_task = asyncio.create_task(self._cleanup_old_requests())

    async def _cleanup_old_requests(self):
        """Clean up old request timestamps"""
        while True:
            await asyncio.sleep(self.window_size)
            now = time.time()
            for key, timestamps in self.requests.items():
                self.requests[key] = [
                    t for t in timestamps if now - t < self.window_size
                ]

    def _get_rate_limit_key(self, request: Request) -> str:
        """Get rate limit key based on strategies"""
        key_parts = []

        if "ip" in self.strategies:
            key_parts.append(request.client.host)

        if "user" in self.strategies:
            # Extract user ID from request (implementation depends on auth)
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                key_parts.append(f"user:{user_id}")

        if "endpoint" in self.strategies:
            key_parts.append(request.url.path)

        return ":".join(key_parts) if key_parts else request.client.host

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get rate limit key
        key = self._get_rate_limit_key(request)

        # Check rate limit
        now = time.time()
        recent_requests = [t for t in self.requests[key] if now - t < self.window_size]

        if len(recent_requests) >= self.rate_limit:
            return JSONResponse(
                {"error": "Rate limit exceeded", "retry_after": self.window_size},
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "X-RateLimit-Limit": str(self.rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + self.window_size)),
                },
            )

        # Record request
        self.requests[key].append(now)

        # Add rate limit headers
        remaining = self.rate_limit - len(recent_requests) - 1
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_size))

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Add security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' wss: https:;"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache control headers"""

    def __init__(self, app, default_max_age: int = 3600):
        super().__init__(app)
        self.default_max_age = default_max_age
        self.no_cache_paths = ["/api/", "/auth/", "/health"]

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Skip cache control for certain paths
        if any(request.url.path.startswith(path) for path in self.no_cache_paths):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        else:
            # Default cache control
            response.headers["Cache-Control"] = (
                f"public, max-age={self.default_max_age}"
            )

        return response


class ResponseSizeMiddleware(BaseHTTPMiddleware):
    """Monitor response sizes"""

    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Log large responses
        content_length = response.headers.get("content-length")
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > 10:  # Large response threshold
                logger.warning(
                    "Large response detected",
                    method=request.method,
                    path=request.url.path,
                    size_mb=size_mb,
                    correlation_id=get_correlation_id(),
                )

        return response


class RequestBodyLoggingMiddleware(BaseHTTPMiddleware):
    """Log request bodies for debugging"""

    def __init__(self, app, exclude_paths: list = None, max_body_size: int = 1024):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip logging for certain paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Log request details
        body = await request.body()
        if body:
            try:
                body_str = body.decode()[: self.max_body_size]
                logger.info(
                    "Request received",
                    method=request.method,
                    path=request.url.path,
                    body=body_str,
                    correlation_id=get_correlation_id(),
                )
            except Exception:
                pass

        return await call_next(request)


# Combined middleware factory
def create_middleware_stack(
    app,
    service_name: str,
    enable_rate_limit: bool = True,
    rate_limit_config: dict = None,
    enable_security_headers: bool = True,
    enable_cache_control: bool = True,
    enable_body_logging: bool = False,
):
    """Create a complete middleware stack"""
    middleware = app

    # Add middlewares in order
    middleware = CorrelationIDMiddleware(middleware)
    middleware = PerformanceMonitoringMiddleware(middleware, service_name)

    if enable_rate_limit:
        rate_limit_config = rate_limit_config or {}
        middleware = RateLimitMiddleware(middleware, **rate_limit_config)

    if enable_security_headers:
        middleware = SecurityHeadersMiddleware(middleware)

    if enable_cache_control:
        middleware = CacheControlMiddleware(middleware)

    middleware = ResponseSizeMiddleware(middleware, service_name)

    if enable_body_logging:
        middleware = RequestBodyLoggingMiddleware(middleware)

    return middleware


# Django middleware class
class DjangoCommonMiddleware:
    """Django version of the common middleware"""

    def __init__(self, get_response, service_name: str = "hms-backend"):
        self.get_response = get_response
        self.service_name = service_name

    def __call__(self, request):
        # Add correlation ID
        correlation_id = getattr(request, "correlation_id", None)
        if not correlation_id:
            from .correlation_id import generate_correlation_id

            correlation_id = generate_correlation_id()
            request.correlation_id = correlation_id

        # Start timing
        start_time = time.time()

        response = self.get_response(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status_code=response.status_code,
            service=self.service_name,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method, endpoint=request.path, service=self.service_name
        ).observe(duration)

        # Add correlation ID header
        response["X-Correlation-ID"] = correlation_id

        return response
