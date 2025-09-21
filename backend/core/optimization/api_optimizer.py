"""
API Response Optimization Utilities
Advanced pagination, efficient serialization, and response caching
"""

import json
import logging
import pickle
import zlib
from functools import wraps
from typing import Any, Dict, List, Optional, Type, Union

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import EmptyPage, Paginator
from django.db import models
from django.db.models import QuerySet
from django.http import Http404, JsonResponse

logger = logging.getLogger(__name__)


class OptimizedPageNumberPagination(PageNumberPagination):
    """High-performance pagination with caching and metadata"""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 1000
    page_query_param = "page"

    def get_paginated_response(self, data):
        """Override to include performance metadata"""
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "has_next": self.page.has_next(),
                "has_previous": self.page.has_previous(),
                "next_page_number": self.page.next_page_number() if self.page.has_next() else None,
                "previous_page_number": self.page.previous_page_number() if self.page.has_previous() else None,
                "results": data,
                "performance": {
                    "query_time": getattr(self.request, "query_time", 0),
                    "serialization_time": getattr(self.request, "serialization_time", 0),
                    "cache_hit": getattr(self.request, "cache_hit", False),
                    "cached_at": getattr(self.request, "cached_at", None),
                },
            }
        )


class CursorPagination:
    """Cursor-based pagination for large datasets"""

    def __init__(self, page_size=50, ordering="-id"):
        self.page_size = page_size
        self.ordering = ordering

    def paginate_queryset(self, queryset, request):
        """Paginate using cursor-based approach"""
        cursor = request.query_params.get("cursor")
        direction = request.query_params.get("direction", "next")

        if cursor:
            # Decode cursor (base64 encoded)
            try:
                import base64

                cursor_data = json.loads(base64.b64decode(cursor.encode()).decode())
                last_id = cursor_data["id"]
                last_value = cursor_data.get("value")
            except:
                cursor = None

        # Apply ordering
        queryset = queryset.order_by(self.ordering)

        # Filter based on cursor
        if cursor:
            field_name = self.ordering.lstrip("-")
            if direction == "next":
                if self.ordering.startswith("-"):
                    queryset = queryset.filter(**{f"{field_name}__lt": last_value})
                else:
                    queryset = queryset.filter(**{f"{field_name}__gt": last_value})
            else:
                if self.ordering.startswith("-"):
                    queryset = queryset.filter(**{f"{field_name}__gt": last_value})
                else:
                    queryset = queryset.filter(**{f"{field_name}__lt": last_value})

        # Limit page size
        queryset = queryset[: self.page_size + 1]  # Get one extra to check if more exists

        # Get results and check if more pages exist
        results = list(queryset[: self.page_size])
        has_more = len(queryset) > self.page_size

        # Create next/previous cursors
        next_cursor = None
        prev_cursor = None

        if results:
            last_item = results[-1]
            field_name = self.ordering.lstrip("-")
            cursor_data = {"id": last_item.id, "value": getattr(last_item, field_name)}

            if has_more or direction == "next":
                import base64

                next_cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()

            if cursor and direction == "next":
                prev_cursor = cursor

        return {"results": results, "next_cursor": next_cursor, "prev_cursor": prev_cursor, "has_more": has_more}


class StreamingJSONResponse(JsonResponse):
    """Streaming JSON response for large datasets"""

    def __init__(self, generator, status=200, **kwargs):
        super().__init__({}, status=status, **kwargs)
        self.generator = generator
        self.streaming = True

    def render(self):
        """Stream the response"""
        response = {"results": self.generator, "count": getattr(self, "_count", None), "streaming": True}
        return json.dumps(response, cls=self._JSONEncoder)

    class _JSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, models.Model):
                return obj.pk
            elif hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)


class APICacheMiddleware:
    """Middleware for caching API responses"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_timeout = getattr(settings, "API_CACHE_TIMEOUT", 300)  # 5 minutes
        self.cache_prefix = getattr(settings, "API_CACHE_PREFIX", "api_")

    def __call__(self, request):
        # Only cache GET requests
        if request.method != "GET" or not request.path.startswith("/api/"):
            return self.get_response(request)

        # Generate cache key
        cache_key = self._get_cache_key(request)

        # Check cache
        cached_response = cache.get(cache_key)
        if cached_response:
            response = JsonResponse(cached_response)
            response["X-Cache"] = "HIT"
            response["X-Cached-At"] = cached_response.get("cached_at")
            return response

        # Get response
        response = self.get_response(request)

        # Cache successful responses
        if response.status_code == 200 and hasattr(response, "data"):
            cache_data = {"data": response.data, "cached_at": timezone.now().isoformat()}
            cache.set(cache_key, cache_data, self.cache_timeout)
            response["X-Cache"] = "MISS"

        return response

    def _get_cache_key(self, request):
        """Generate cache key for request"""
        from urllib.parse import urlencode

        query_string = urlencode(request.GET)
        return f"{self.cache_prefix}{request.path}_{hashlib.md5(query_string.encode()).hexdigest()}"


def cache_api_response(timeout=None, key_func=None):
    """Decorator for caching API responses"""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(view, request, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                cache_key = (
                    f"api_{view.__class__.__name__}_{hashlib.md5(request.build_absolute_uri().encode()).hexdigest()}"
                )

            # Check cache
            cached_data = cache.get(cache_key)
            if cached_data:
                request.cache_hit = True
                request.cached_at = cached_data.get("cached_at")
                return Response(cached_data["data"])

            # Execute view
            response = view_func(view, request, *args, **kwargs)

            # Cache successful responses
            if response.status_code == 200 and hasattr(response, "data"):
                cache_data = {"data": response.data, "cached_at": timezone.now().isoformat()}
                cache.set(cache_key, cache_data, timeout or settings.API_CACHE_TIMEOUT)

            return response

        return wrapper

    return decorator


def stream_queryset(queryset, serializer_class, batch_size=1000):
    """Stream large querysets efficiently"""

    def generator():
        offset = 0
        while True:
            batch = queryset[offset : offset + batch_size]
            if not batch:
                break

            serializer = serializer_class(batch, many=True)
            for item in serializer.data:
                yield item

            offset += batch_size

    return generator()


class BulkOperationMixin:
    """Mixin for efficient bulk operations"""

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """Efficient bulk create operation"""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # Use bulk_create for efficiency
        instances = self.get_queryset().model.objects.bulk_create(
            [self.get_queryset().model(**item) for item in serializer.validated_data], batch_size=1000
        )

        # Serialize created instances
        response_serializer = self.get_serializer(instances, many=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["patch"])
    def bulk_update(self, request):
        """Efficient bulk update operation"""
        if not isinstance(request.data, list):
            return Response({"error": "Expected list of objects"}, status=400)

        # Get IDs from request
        ids = [item.get("id") for item in request.data if item.get("id")]
        if not ids:
            return Response({"error": "No valid IDs provided"}, status=400)

        # Get instances
        instances = list(self.get_queryset().filter(id__in=ids))
        instance_map = {str(inst.id): inst for inst in instances}

        # Update instances
        updates = []
        for item in request.data:
            instance = instance_map.get(str(item.get("id")))
            if instance:
                for field, value in item.items():
                    if field != "id":
                        setattr(instance, field, value)
                updates.append(instance)

        # Bulk update
        self.get_queryset().model.objects.bulk_update(
            updates, batch_size=1000, fields=[field for field in request.data[0].keys() if field != "id"]
        )

        # Return updated instances
        serializer = self.get_serializer(instances, many=True)
        return Response(serializer.data)


class OptimizedModelViewSet(ModelViewSet):
    """High-performance model viewset with all optimizations"""

    pagination_class = OptimizedPageNumberPagination
    optimizer = None

    def get_queryset(self):
        """Get optimized queryset"""
        queryset = super().get_queryset()

        # Apply query optimizations
        if hasattr(self, "select_related_fields"):
            queryset = queryset.select_related(*self.select_related_fields)

        if hasattr(self, "prefetch_related_fields"):
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)

        # Apply filters efficiently
        for backend in self.filter_backends:
            queryset = backend().filter_queryset(self.request, queryset, self)

        return queryset

    def list(self, request, *args, **kwargs):
        """Optimized list view with caching"""
        # Check if streaming is requested
        if request.GET.get("stream") == "true":
            return self._stream_response(request)

        # Check if cursor pagination is requested
        if request.GET.get("pagination") == "cursor":
            return self._cursor_paginate(request)

        # Standard pagination with caching
        return super().list(request, *args, **kwargs)

    def _stream_response(self, request):
        """Stream large datasets"""
        queryset = self.filter_queryset(self.get_queryset())

        # Use streaming response
        generator = stream_queryset(queryset, self.get_serializer_class())
        response = StreamingJSONResponse(generator)
        response._count = queryset.count()
        return response

    def _cursor_paginate(self, request):
        """Cursor-based pagination"""
        queryset = self.filter_queryset(self.get_queryset())

        # Get ordering field
        ordering = request.GET.get("ordering", "-id")
        page_size = int(request.GET.get("page_size", 50))

        paginator = CursorPagination(page_size=page_size, ordering=ordering)
        paginated_data = paginator.paginate_queryset(queryset, request)

        # Serialize results
        serializer = self.get_serializer(paginated_data["results"], many=True)

        return Response(
            {
                "results": serializer.data,
                "next_cursor": paginated_data["next_cursor"],
                "prev_cursor": paginated_data["prev_cursor"],
                "has_more": paginated_data["has_more"],
            }
        )

    def retrieve(self, request, *args, **kwargs):
        """Optimized retrieve with individual object caching"""
        # Try to get from cache first
        cache_key = f"{self.get_queryset().model.__name__}_{kwargs['pk']}"
        cached_data = cache.get(cache_key)

        if cached_data:
            request.cache_hit = True
            return Response(cached_data)

        # Get instance
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Cache response
        cache.set(cache_key, serializer.data, timeout=settings.API_CACHE_TIMEOUT)

        return Response(serializer.data)

    def perform_update(self, serializer):
        """Update with cache invalidation"""
        instance = serializer.save()

        # Invalidate cache
        model_name = instance.__class__.__name__
        cache_keys = [f"{model_name}_{instance.pk}", f"{model_name}_list_*"]  # Pattern for list caches
        cache.delete_many(cache_keys)

    def perform_destroy(self, instance):
        """Destroy with cache invalidation"""
        model_name = instance.__class__.__name__
        cache_keys = [f"{model_name}_{instance.pk}", f"{model_name}_list_*"]
        cache.delete_many(cache_keys)

        super().perform_destroy(instance)


# Utility functions
def optimize_serializer_fields(serializer, requested_fields=None):
    """Optimize serializer by only including requested fields"""
    if not requested_fields:
        return serializer

    # Limit fields
    if hasattr(serializer, "fields"):
        fields_to_include = set(requested_fields) & set(serializer.fields.keys())
        serializer.fields = {k: v for k, v in serializer.fields.items() if k in fields_to_include}

    return serializer


def calculate_query_efficiency(queryset):
    """Calculate query efficiency metrics"""
    from django.db import connection
    from django.db.utils import OperationalError

    # Reset query log
    initial_queries = len(connection.queries)

    # Force query execution
    list(queryset)

    # Analyze queries
    queries_executed = len(connection.queries) - initial_queries
    total_time = sum(float(q["time"]) for q in connection.queries[initial_queries:])

    return {
        "queries_executed": queries_executed,
        "total_time_ms": total_time * 1000,
        "avg_time_per_query_ms": (total_time / queries_executed) * 1000 if queries_executed > 0 else 0,
        "query_count_score": 1 / (1 + queries_executed),  # Lower is better
        "time_score": 1 / (1 + total_time * 1000),  # Lower is better
    }


# Global API optimization settings
API_OPTIMIZATION_SETTINGS = {
    "DEFAULT_PAGE_SIZE": 50,
    "MAX_PAGE_SIZE": 1000,
    "CACHE_TIMEOUT": 300,  # 5 minutes
    "BATCH_SIZE": 1000,
    "STREAM_THRESHOLD": 1000,  # Stream responses larger than this
    "COMPRESSION_THRESHOLD": 1024,  # Compress responses larger than this
    "ENABLE_ETAG": True,
    "ENABLE_CONDITIONAL_GET": True,
    "ENABLE_GZIP": True,
    "ENABLE_BR": True,  # Brotli compression
}
