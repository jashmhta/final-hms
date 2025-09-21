"""
Performance optimization middleware for API responses
Implements response compression, caching, and query optimization
"""

import gzip
import json
import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.middleware.cache import FetchFromCacheMiddleware
from django.middleware.common import CommonMiddleware
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

logger = logging.getLogger(__name__)


class PerformanceMiddleware:
    """Middleware to optimize API performance"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timing
        start_time = time.time()
        query_count_start = len(connection.queries)

        # Process request
        response = self.get_response(request)

        # Calculate performance metrics
        duration = time.time() - start_time
        query_count = len(connection.queries) - query_count_start

        # Add performance headers
        response["X-Response-Time"] = f"{duration:.3f}s"
        response["X-Query-Count"] = str(query_count)

        # Log slow requests (>500ms)
        if duration > 0.5:
            logger.warning(f"Slow request: {request.path} took {duration:.3f}s with {query_count} queries")

        # Compress response if eligible
        if self.should_compress(request, response):
            response = self.compress_response(response)

        return response

    def should_compress(self, request, response):
        """Check if response should be compressed"""
        if not getattr(settings, "ENABLE_COMPRESSION", True):
            return False

        # Only compress JSON responses
        if not response.get("Content-Type", "").startswith("application/json"):
            return False

        # Don't compress small responses
        if hasattr(response, "content"):
            content_length = len(response.content)
            return content_length > 1024  # Compress if > 1KB

        return False

    def compress_response(self, response):
        """Compress response using gzip"""
        if not hasattr(response, "content"):
            return response

        # Compress content
        compressed_content = gzip.compress(response.content)

        # Update response
        response.content = compressed_content
        response["Content-Encoding"] = "gzip"
        response["Content-Length"] = str(len(compressed_content))

        # Remove ETag since content changed
        if "ETag" in response:
            del response["ETag"]

        return response


class CacheControlMiddleware:
    """Middleware for cache control headers"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add cache headers based on response type
        if request.path.startswith("/api/"):
            if request.method == "GET":
                # Cache GET requests for 5 minutes by default
                response["Cache-Control"] = "public, max-age=300"
                response["Vary"] = "Authorization, Accept-Encoding"
            else:
                # Don't cache non-GET requests
                response["Cache-Control"] = "no-store, no-cache, must-revalidate"
                response["Pragma"] = "no-cache"
                response["Expires"] = "0"

        return response


class DatabaseOptimizationMiddleware:
    """Middleware for database query optimization"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.query_threshold = getattr(settings, "QUERY_THRESHOLD", 50)

    def __call__(self, request):
        # Reset queries before processing
        if hasattr(connection, "queries"):
            initial_query_count = len(connection.queries)

        response = self.get_response(request)

        # Check for query optimization opportunities
        if hasattr(connection, "queries"):
            final_query_count = len(connection.queries)
            queries_executed = connection.queries[initial_query_count:]

            # Log query count warnings
            if len(queries_executed) > self.query_threshold:
                logger.warning(f"High query count on {request.path}: {len(queries_executed)} queries")

                # Log slow queries (>100ms)
                slow_queries = [q for q in queries_executed if float(q.get("time", 0)) > 0.1]

                if slow_queries:
                    logger.warning(f"Slow queries detected on {request.path}:")
                    for query in slow_queries[:5]:  # Log first 5 slow queries
                        logger.warning(f"  {query['time']}s: {query['sql'][:200]}...")

        return response


class RateLimitMiddleware:
    """Rate limiting middleware for API protection"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        # Get client identifier
        client_id = self.get_client_id(request)

        # Check rate limit
        if self.is_rate_limited(client_id, request.path):
            return JsonResponse({"error": "Rate limit exceeded"}, status=429)

        return self.get_response(request)

    def get_client_id(self, request):
        """Get client identifier for rate limiting"""
        # Use user ID if authenticated, otherwise IP
        if request.user.is_authenticated:
            return f"user_{request.user.id}"
        return f"ip_{self.get_client_ip(request)}"

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def is_rate_limited(self, client_id, path):
        """Check if client is rate limited"""
        # Default rate limits
        limits = {
            "/api/patients/": 100,  # 100 requests per minute
            "/api/appointments/": 200,
            "/api/ehr/": 150,
            "/api/lab/": 100,
            "/default": 50,  # Default limit
        }

        # Find matching limit
        limit = limits.get("default")
        for endpoint, endpoint_limit in limits.items():
            if endpoint != "default" and path.startswith(endpoint):
                limit = endpoint_limit
                break

        # Check cache for current count
        cache_key = f"rate_limit:{client_id}:{path}"
        current_count = cache.get(cache_key, 0)

        if current_count >= limit:
            return True

        # Increment counter
        cache.set(cache_key, current_count + 1, 60)  # 1 minute window

        return False
