"""
Enhanced caching decorators for performance optimization
"""

import hashlib
import json
import logging
from functools import wraps

from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie, vary_on_headers

logger = logging.getLogger(__name__)


def cache_result(timeout=DEFAULT_TIMEOUT, key_prefix=None, tags=None):
    """
    Enhanced caching decorator with tag support
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_prefix:
                cache_key = f"{key_prefix}:{func.__name__}"
            else:
                cache_key = f"cache:{func.__name__}"

            # Add args to cache key
            if args:
                args_str = hashlib.hashlib.sha256(str(args).encode()).hexdigest()
                cache_key += f":args_{args_str}"

            # Add kwargs to cache key
            if kwargs:
                kwargs_str = hashlib.hashlib.sha256(
                    json.dumps(kwargs, sort_keys=True).encode()
                ).hexdigest()
                cache_key += f":kwargs_{kwargs_str}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result

            # Execute function and cache result
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache with tags
            cache.set(cache_key, result, timeout)
            if tags:
                for tag in tags:
                    tag_key = f"tag:{tag}"
                    tag_values = cache.get(tag_key, set())
                    tag_values.add(cache_key)
                    cache.set(tag_key, tag_values, timeout)

            return result

        return wrapper

    return decorator


def invalidate_cache_tag(tag):
    """
    Invalidate all cache entries with a specific tag
    """
    tag_key = f"tag:{tag}"
    cache_keys = cache.get(tag_key, set())

    deleted_count = 0
    for cache_key in cache_keys:
        if cache.delete(cache_key):
            deleted_count += 1

    # Delete the tag itself
    cache.delete(tag_key)

    logger.info(f"Invalidated {deleted_count} cache entries for tag '{tag}'")
    return deleted_count


def api_cache(timeout=300, vary_on=None):
    """
    API response caching decorator
    """

    def decorator(view_func):
        # Apply cache_page decorator
        cached_view = cache_page(timeout)(view_func)

        # Add vary headers if specified
        if vary_on:
            if "headers" in vary_on:
                cached_view = vary_on_headers(*vary_on["headers"])(cached_view)
            if "cookie" in vary_on and vary_on["cookie"]:
                cached_view = vary_on_cookie(cached_view)

        return cached_view

    return decorator


def conditional_cache(condition_func, timeout=DEFAULT_TIMEOUT):
    """
    Conditional caching based on a function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if condition_func(*args, **kwargs):
                # Use cache_result with default behavior
                return cache_result(timeout)(func)(*args, **kwargs)
            return func(*args, **kwargs)

        return wrapper

    return decorator


class CacheMixin:
    """
    Mixin class for DRF ViewSet caching
    """

    cache_timeout = 300  # 5 minutes default
    cache_tags = []

    def get_cache_key(self, request):
        """Generate cache key for list views"""
        params = request.GET.copy()
        params.pop("page", None)  # Don't cache pagination
        params.pop("format", None)

        key_parts = [
            self.__class__.__name__,
            self.action or "list",
            request.user.id if request.user.is_authenticated else "anonymous",
            str(sorted(params.items())),
        ]

        return hashlib.hashlib.sha256(":".join(key_parts).encode()).hexdigest()

    def list(self, request, *args, **kwargs):
        """Override list with caching"""
        cache_key = self.get_cache_key(request)

        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"ViewSet cache hit: {cache_key}")
            return JsonResponse(cached_data)

        # Execute and cache
        response = super().list(request, *args, **kwargs)

        # Only cache successful responses
        if response.status_code == 200:
            cache.set(
                cache_key,
                response.data,
                self.cache_timeout,
                version=getattr(self, "cache_version", 1),
            )

            # Add tags
            for tag in self.cache_tags:
                tag_key = f"tag:{tag}"
                tag_values = cache.get(tag_key, set())
                tag_values.add(cache_key)
                cache.set(tag_key, tag_values, self.cache_timeout)

        return response

    def perform_destroy(self, instance):
        """Invalidate cache on delete"""
        super().perform_destroy(instance)

        # Invalidate related cache tags
        for tag in self.cache_tags:
            invalidate_cache_tag(tag)

    def perform_update(self, serializer):
        """Invalidate cache on update"""
        super().perform_update(serializer)

        # Invalidate related cache tags
        for tag in self.cache_tags:
            invalidate_cache_tag(tag)


def query_cache(timeout=DEFAULT_TIMEOUT, query_func=None):
    """
    Cache expensive database queries
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate query hash
            if query_func:
                query = query_func(*args, **kwargs)
            else:
                query = str(func.__code__.co_code) + str(args) + str(kwargs)

            query_hash = hashlib.hashlib.sha256(query.encode()).hexdigest()
            cache_key = f"query_cache:{func.__name__}:{query_hash}"

            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator
