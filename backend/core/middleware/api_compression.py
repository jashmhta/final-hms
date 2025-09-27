"""
API Response Compression Middleware
Efficient compression with support for Gzip, Brotli, and custom algorithms
"""

import gzip
import io
import zlib

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

try:
    import brotli

    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False


class APIResponseCompressor(MiddlewareMixin):
    """Middleware for compressing API responses"""

    def __init__(self, get_response):
        super().__init__(get_response)
        self.compression_level = getattr(settings, "API_COMPRESSION_LEVEL", 6)
        self.min_size = getattr(settings, "API_COMPRESSION_MIN_SIZE", 1024)
        self.content_types = getattr(
            settings,
            "API_COMPRESSION_CONTENT_TYPES",
            [
                "application/json",
                "application/xml",
                "text/xml",
                "text/html",
                "text/css",
                "text/javascript",
                "application/javascript",
            ],
        )
        self.blacklist = getattr(
            settings,
            "API_COMPRESSION_BLACKLIST",
            [
                "/health/",
                "/metrics/",
            ],
        )

    def process_response(self, request, response):
        """Compress response if applicable"""

        # Don't compress if:
        # - Response is already compressed
        # - Response is streaming
        # - Response is too small
        # - Content type not in list
        # - URL in blacklist
        # - Request is from a bot/crawler
        if (
            hasattr(response, "streaming")
            and response.streaming
            or response.status_code < 200
            or response.status_code >= 300
            or "Content-Encoding" in response
            or len(response.content) < self.min_size
            or not self._should_compress_type(response.get("Content-Type", ""))
            or any(url in request.path for url in self.blacklist)
            or self._is_bot_request(request)
        ):
            return response

        # Get accepted encodings
        accept_encoding = request.META.get("HTTP_ACCEPT_ENCODING", "").lower()
        if not accept_encoding:
            return response

        # Try Brotli first (most efficient)
        if HAS_BROTLI and "br" in accept_encoding:
            return self._compress_with_brotli(response)

        # Try Gzip
        if "gzip" in accept_encoding:
            return self._compress_with_gzip(response)

        # Try Deflate
        if "deflate" in accept_encoding:
            return self._compress_with_deflate(response)

        return response

    def _should_compress_type(self, content_type):
        """Check if content type should be compressed"""
        if not content_type:
            return False
        return any(ct in content_type for ct in self.content_types)

    def _is_bot_request(self, request):
        """Check if request is from a bot"""
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        bot_patterns = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "curl",
            "wget",
            "python-requests",
        ]
        return any(pattern in user_agent for pattern in bot_patterns)

    def _compress_with_brotli(self, response):
        """Compress response with Brotli"""
        compressed_content = brotli.compress(
            response.content, quality=self.compression_level
        )

        # Create new response with compressed content
        compressed_response = HttpResponse(
            compressed_content,
            content_type=response.get("Content-Type"),
            status=response.status_code,
        )

        # Copy headers
        for header, value in response.items():
            if header not in ["Content-Length", "Content-Encoding"]:
                compressed_response[header] = value

        # Set compression headers
        compressed_response["Content-Encoding"] = "br"
        compressed_response["Content-Length"] = str(len(compressed_content))
        compressed_response["Vary"] = "Accept-Encoding"

        # Add performance metrics
        if hasattr(response, "performance_metrics"):
            original_size = len(response.content)
            compressed_size = len(compressed_content)
            compression_ratio = (
                (original_size - compressed_size) / original_size
            ) * 100
            compressed_response.performance_metrics = {
                **response.performance_metrics,
                "compression_ratio": compression_ratio,
                "compression_algorithm": "brotli",
                "original_size": original_size,
                "compressed_size": compressed_size,
            }

        return compressed_response

    def _compress_with_gzip(self, response):
        """Compress response with Gzip"""
        # Use GzipFile for better compression
        zbuf = io.BytesIO()
        with gzip.GzipFile(
            mode="wb", compresslevel=self.compression_level, fileobj=zbuf
        ) as zfile:
            zfile.write(response.content)

        compressed_content = zbuf.getvalue()

        # Create new response
        compressed_response = HttpResponse(
            compressed_content,
            content_type=response.get("Content-Type"),
            status=response.status_code,
        )

        # Copy headers
        for header, value in response.items():
            if header not in ["Content-Length", "Content-Encoding"]:
                compressed_response[header] = value

        # Set compression headers
        compressed_response["Content-Encoding"] = "gzip"
        compressed_response["Content-Length"] = str(len(compressed_content))
        compressed_response["Vary"] = "Accept-Encoding"

        # Add performance metrics
        if hasattr(response, "performance_metrics"):
            original_size = len(response.content)
            compressed_size = len(compressed_content)
            compression_ratio = (
                (original_size - compressed_size) / original_size
            ) * 100
            compressed_response.performance_metrics = {
                **response.performance_metrics,
                "compression_ratio": compression_ratio,
                "compression_algorithm": "gzip",
                "original_size": original_size,
                "compressed_size": compressed_size,
            }

        return compressed_response

    def _compress_with_deflate(self, response):
        """Compress response with Deflate"""
        compressed_content = zlib.compress(
            response.content, level=self.compression_level
        )

        # Create new response
        compressed_response = HttpResponse(
            compressed_content,
            content_type=response.get("Content-Type"),
            status=response.status_code,
        )

        # Copy headers
        for header, value in response.items():
            if header not in ["Content-Length", "Content-Encoding"]:
                compressed_response[header] = value

        # Set compression headers
        compressed_response["Content-Encoding"] = "deflate"
        compressed_response["Content-Length"] = str(len(compressed_content))
        compressed_response["Vary"] = "Accept-Encoding"

        # Add performance metrics
        if hasattr(response, "performance_metrics"):
            original_size = len(response.content)
            compressed_size = len(compressed_content)
            compression_ratio = (
                (original_size - compressed_size) / original_size
            ) * 100
            compressed_response.performance_metrics = {
                **response.performance_metrics,
                "compression_ratio": compression_ratio,
                "compression_algorithm": "deflate",
                "original_size": original_size,
                "compressed_size": compressed_size,
            }

        return compressed_response


class APIResponseOptimizer(MiddlewareMixin):
    """Middleware for optimizing API responses"""

    def __init__(self, get_response):
        super().__init__(get_response)
        self.enable_etag = getattr(settings, "API_ENABLE_ETAG", True)
        self.enable_conditional_get = getattr(
            settings, "API_ENABLE_CONDITIONAL_GET", True
        )

    def process_response(self, request, response):
        """Optimize API response"""

        # Only process API responses
        if not request.path.startswith("/api/"):
            return response

        # Add performance headers
        self._add_performance_headers(request, response)

        # Handle ETag
        if self.enable_etag and self._should_add_etag(response):
            etag = self._generate_etag(response)
            response["ETag"] = etag

            # Check for conditional GET
            if self.enable_conditional_get and "HTTP_IF_NONE_MATCH" in request.META:
                if_none_match = request.META["HTTP_IF_NONE_MATCH"]
                if if_none_match == etag or if_none_match == f"W/{etag}":
                    return HttpResponse(status=304)  # Not Modified

        # Add caching headers
        self._add_caching_headers(request, response)

        return response

    def _add_performance_headers(self, request, response):
        """Add performance-related headers"""
        # Add server timing
        if hasattr(request, "start_time"):
            duration = (request.start_time - request.start_time).total_seconds() * 1000
            response["Server-Timing"] = f"total;dur={duration:.2f}"

        # Add API version
        response["X-API-Version"] = getattr(settings, "API_VERSION", "v1")

        # Add request ID
        request_id = getattr(request, "request_id", None)
        if request_id:
            response["X-Request-ID"] = request_id

    def _should_add_etag(self, response):
        """Check if ETag should be added"""
        return (
            response.status_code == 200
            and not response.streaming
            and response.get("Content-Type", "").startswith("application/json")
        )

    def _generate_etag(self, response):
        """Generate ETag for response"""
        import hashlib

        content = response.content
        return hashlib.hashlib.sha256(content).hexdigest()

    def _add_caching_headers(self, request, response):
        """Add appropriate caching headers"""
        # Don't cache POST/PUT/DELETE responses
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            response["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
            return

        # Cache GET responses based on content type
        content_type = response.get("Content-Type", "")

        if content_type.startswith("application/json"):
            # Cache API responses for 5 minutes by default
            max_age = getattr(settings, "API_CACHE_MAX_AGE", 300)
            response["Cache-Control"] = f"public, max-age={max_age}"
        else:
            # Don't cache other content types
            response["Cache-Control"] = "no-store"


class APIThrottlingMiddleware(MiddlewareMixin):
    """Middleware for API rate limiting and throttling"""

    def __init__(self, get_response):
        super().__init__(get_response)
        from django.core.cache import cache

        self.cache = cache

    def process_request(self, request):
        """Check rate limits before processing"""
        if not request.path.startswith("/api/"):
            return

        # Get client identifier
        client_id = self._get_client_id(request)

        # Check rate limits
        if not self._check_rate_limit(client_id, request):
            from rest_framework.exceptions import Throttled

            raise Throttled(detail="Rate limit exceeded")

    def _get_client_id(self, request):
        """Get unique client identifier"""
        # Use API key if available
        api_key = request.META.get("HTTP_API_KEY")
        if api_key:
            return f"api_key_{api_key}"

        # Use authenticated user
        if request.user.is_authenticated:
            return f"user_{request.user.id}"

        # Fall back to IP address
        ip_address = self._get_client_ip(request)
        return f"ip_{ip_address}"

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def _check_rate_limit(self, client_id, request):
        """Check if client has exceeded rate limits"""
        import time

        from django.utils import timezone

        # Get rate limit settings
        endpoint = request.path_info
        method = request.method.lower()

        # Different limits for different endpoints
        limits = {
            ("/api/patients/", "get"): ("1000/hour", "100/minute"),
            ("/api/patients/", "post"): ("100/hour", "10/minute"),
            ("/api/appointments/", "get"): ("500/hour", "50/minute"),
            ("default", "get"): ("5000/hour", "500/minute"),
            ("default", "post"): ("500/hour", "50/minute"),
        }

        # Find appropriate limit
        rate_limits = limits.get(
            (endpoint, method),
            limits.get(("default", method), ("500/hour", "50/minute")),
        )

        # Check each limit
        for limit in rate_limits:
            if not self._check_single_limit(client_id, endpoint, limit):
                return False

        return True

    def _check_single_limit(self, client_id, endpoint, limit):
        """Check a single rate limit"""
        count, period = limit.split("/")
        count = int(count)

        # Convert period to seconds
        if period == "second":
            window = 1
        elif period == "minute":
            window = 60
        elif period == "hour":
            window = 3600
        elif period == "day":
            window = 86400
        else:
            return True  # Unknown period, skip

        # Create cache key
        import time

        now = int(time.time())
        key = f"rate_limit_{client_id}_{endpoint}_{count}/{period}"

        # Use Redis atomic increment if available
        try:
            from django_redis import get_redis_connection

            redis = get_redis_connection("default")
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            current = pipe.execute()[0]
        except:
            # Fallback to Django cache
            import time

            current = self.cache.get_or_set(key, lambda: 0, window)
            current += 1
            self.cache.set(key, current, window)

        return current <= count


# Factory function for easy middleware configuration
def get_api_middleware():
    """Get configured API middleware stack"""
    middleware = []

    # Add compression first
    middleware.append("core.middleware.api_compression.APIResponseCompressor")

    # Add response optimizer
    middleware.append("core.middleware.api_compression.APIResponseOptimizer")

    # Add throttling
    middleware.append("core.middleware.api_compression.APIThrottlingMiddleware")

    return middleware
