import time
import logging
import json
from typing import Dict, Any, Optional
from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from .enhanced_cache import enhanced_cache, CacheConfig
logger = logging.getLogger(__name__)
class PerformanceMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.cache = enhanced_cache
        self.config = CacheConfig()
    def process_request(self, request):
        request.start_time = time.time()
        request.META["HTTP_X_REQUEST_ID"] = request.META.get(
            "HTTP_X_REQUEST_ID", f"req_{int(time.time() * 1000)}"
        )
        if hasattr(request, "user") and request.user.is_authenticated:
            user_cache_key = self.cache.generate_cache_key(
                "user_session", request.user.id
            )
            user_data = self.cache.cache.get(user_cache_key)
            if user_data is None:
                user_data = {
                    "id": request.user.id,
                    "hospital_id": getattr(request.user, "hospital_id", None),
                    "role": getattr(request.user, "role", None),
                    "permissions": getattr(request.user, "permissions", []),
                }
                self.cache.set_with_tags(
                    user_cache_key,
                    user_data,
                    self.config.SHORT_TIMEOUT,
                    ["user_session", f"user_{request.user.id}"],
                )
            request.user_cache = user_data
    def process_response(self, request, response):
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            response["X-Response-Time"] = f"{duration:.3f}s"
            if duration > 2.0:
                logger.warning(f"Slow request: {request.path} took {duration:.3f}s")
        response["X-Frame-Options"] = "DENY"
        response["X-Content-Type-Options"] = "nosniff"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.path.startswith("/static/"):
            response["Cache-Control"] = "public, max-age=3600"
            response["Expires"] = "access plus 1 hour"
        elif request.path.startswith("/api/"):
            if request.method == "GET":
                response["Cache-Control"] = "public, max-age=300"
                response["Vary"] = "Authorization, Accept-Encoding"
        return response
class QueryOptimizationMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.slow_query_threshold = 0.5  
    def process_response(self, request, response):
        if hasattr(request, "queries"):
            slow_queries = [
                q
                for q in request.queries
                if float(q["time"]) > self.slow_query_threshold
            ]
            if slow_queries:
                logger.warning(
                    f"Slow queries detected for {request.path}: {len(slow_queries)} queries"
                )
                for query in slow_queries:
                    logger.warning(f"Slow query: {query['sql']} took {query['time']}s")
        return response
class CompressionMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if isinstance(response, HttpResponse):
            accept_encoding = request.META.get("HTTP_ACCEPT_ENCODING", "")
            if "gzip" in accept_encoding and not response.has_header(
                "Content-Encoding"
            ):
                content_type = response.get("Content-Type", "")
                if any(
                    ct in content_type
                    for ct in ["text/", "application/json", "application/xml"]
                ):
                    try:
                        import gzip
                        response.content = gzip.compress(response.content)
                        response["Content-Encoding"] = "gzip"
                        response["Content-Length"] = str(len(response.content))
                    except Exception as e:
                        logger.error(f"Compression failed: {e}")
        return response
class RateLimitingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.rate_limits = {
            "api": {"requests": 100, "window": 60},  
            "auth": {"requests": 5, "window": 60},  
        }
    def process_request(self, request):
        if request.path.startswith("/api/"):
            client_ip = self.get_client_ip(request)
            endpoint_type = "auth" if "auth" in request.path else "api"
            rate_key = f"rate_limit:{client_ip}:{endpoint_type}"
            current_count = self.cache.cache.get(rate_key, 0)
            limit = self.rate_limits[endpoint_type]
            if current_count >= limit["requests"]:
                logger.warning(
                    f"Rate limit exceeded for {client_ip} on {endpoint_type}"
                )
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    json.dumps({"error": "Rate limit exceeded"}),
                    content_type="application/json",
                )
            self.cache.cache.set(rate_key, current_count + 1, limit["window"])
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
class CachingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.cache = enhanced_cache
        self.cacheable_paths = ["/api/analytics/", "/api/dashboard/"]
    def process_request(self, request):
        if request.method == "GET" and any(
            request.path.startswith(path) for path in self.cacheable_paths
        ):
            cache_key = self.cache.generate_cache_key(
                "response_cache",
                request.path,
                request.GET.urlencode(),
                getattr(request.user, "hospital_id", None),
            )
            cached_response = self.cache.cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {request.path}")
                return cached_response
    def process_response(self, request, response):
        if (
            request.method == "GET"
            and any(request.path.startswith(path) for path in self.cacheable_paths)
            and response.status_code == 200
        ):
            cache_key = self.cache.generate_cache_key(
                "response_cache",
                request.path,
                request.GET.urlencode(),
                getattr(request.user, "hospital_id", None),
            )
            self.cache.set_with_tags(
                cache_key,
                response,
                CacheConfig.SHORT_TIMEOUT,
                ["api_response", f"path_{request.path}"],
            )
        return response