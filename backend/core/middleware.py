import logging
import threading
import uuid
from typing import Optional

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
        # Content Security Policy - strict for XSS prevention
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

        # Additional security headers
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-Frame-Options", "DENY")
        response.setdefault("X-XSS-Protection", "1; mode=block")

        # Permissions policy for additional restrictions
        response.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), magnetometer=(), gyroscope=(), accelerometer=()"
        )

        return response


class SecurityAuditMiddleware(MiddlewareMixin):
    """Middleware for comprehensive security auditing"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('security.audit')

    def __call__(self, request):
        # Log request details for security monitoring
        self.log_request(request)

        response = self.get_response(request)

        # Log response details
        self.log_response(request, response)

        return response

    def log_request(self, request):
        """Log incoming request details"""
        user = getattr(request, 'user', None)
        user_id = user.id if user and user.is_authenticated else None

        self.logger.info(
            'Request received',
            extra={
                'request_id': getattr(request, 'request_id', None),
                'user_id': user_id,
                'method': request.method,
                'path': request.path,
                'ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'query_params': dict(request.GET),
            }
        )

    def log_response(self, request, response):
        """Log response details"""
        user = getattr(request, 'user', None)
        user_id = user.id if user and user.is_authenticated else None

        # Log security-relevant responses
        if response.status_code >= 400:
            self.logger.warning(
                f'Response {response.status_code}',
                extra={
                    'request_id': getattr(request, 'request_id', None),
                    'user_id': user_id,
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'ip': self.get_client_ip(request),
                }
            )

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RateLimitMiddleware(MiddlewareMixin):
    """Advanced rate limiting middleware"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.burst_limits = {
            'login': (5, 300),  # 5 requests per 5 minutes
            'api': (100, 60),   # 100 requests per minute
            'search': (20, 60), # 20 searches per minute
        }

    def __call__(self, request):
        # Check rate limits
        if not self.check_rate_limit(request):
            from django.http import HttpResponseTooManyRequests
            return HttpResponseTooManyRequests("Rate limit exceeded")

        response = self.get_response(request)
        return response

    def check_rate_limit(self, request):
        """Check if request is within rate limits"""
        from django.core.cache import cache

        ip = self.get_client_ip(request)
        path = request.path

        # Determine limit type
        if '/login' in path or '/auth' in path:
            limit_type = 'login'
        elif '/search' in path:
            limit_type = 'search'
        else:
            limit_type = 'api'

        max_requests, window = self.burst_limits[limit_type]
        cache_key = f"ratelimit:{ip}:{limit_type}"

        # Get current request count
        current = cache.get(cache_key, 0)

        if current >= max_requests:
            return False

        # Increment counter
        cache.set(cache_key, current + 1, window)
        return True

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip