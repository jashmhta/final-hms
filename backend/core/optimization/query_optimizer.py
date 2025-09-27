"""
Django ORM Performance Optimization Utilities
Eliminates N+1 queries and optimizes database access patterns
"""

import logging
import time
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, TypeVar

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import EmptyPage, Paginator
from django.db import models, transaction
from django.db.models import Avg, Count, Max, Min, Prefetch, Q, Sum
from django.db.models.functions import Coalesce

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=models.Model)


class QueryOptimizer:
    """Advanced query optimization utilities"""

    @staticmethod
    def get_optimized_queryset(
        model_class: type[T],
        select_related: List[str] = None,
        prefetch_related: List[str] = None,
        annotations: Dict[str, Any] = None,
        filters: Q = None,
        exclude: Q = None,
        only_fields: List[str] = None,
        defer_fields: List[str] = None,
    ) -> models.QuerySet[T]:
        """
        Generate optimized queryset with all optimizations applied
        """
        queryset = model_class.objects.all()

        # Apply select_related for foreign key relationships
        if select_related:
            queryset = queryset.select_related(*select_related)

        # Apply prefetch_related for many-to-many and reverse relationships
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)

        # Apply annotations for computed fields
        if annotations:
            queryset = queryset.annotate(**annotations)

        # Apply filters
        if filters:
            queryset = queryset.filter(filters)

        # Apply exclusions
        if exclude:
            queryset = queryset.exclude(exclude)

        # Optimize field selection
        if only_fields:
            queryset = queryset.only(*only_fields)
        elif defer_fields:
            queryset = queryset.defer(*defer_fields)

        return queryset

    @staticmethod
    def bulk_optimized_create(
        model_class: type[T], data_list: List[Dict[str, Any]], batch_size: int = 1000
    ) -> List[T]:
        """Optimized bulk create with batching"""
        created_objects = []

        for i in range(0, len(data_list), batch_size):
            batch = data_list[i : i + batch_size]
            objects = model_class.objects.bulk_create(
                [model_class(**data) for data in batch], batch_size=batch_size
            )
            created_objects.extend(objects)

        return created_objects

    @staticmethod
    def bulk_optimized_update(
        model_class: type[T],
        queryset: models.QuerySet[T],
        updates: Dict[str, Any],
        batch_size: int = 1000,
    ) -> int:
        """Optimized bulk update with batching"""
        total_updated = 0
        total_count = queryset.count()

        for i in range(0, total_count, batch_size):
            batch_queryset = queryset[i : i + batch_size]
            updated_count = batch_queryset.update(**updates)
            total_updated += updated_count

        return total_updated


class SmartPaginator:
    """Intelligent pagination with optimization"""

    def __init__(
        self,
        queryset: models.QuerySet,
        per_page: int = 20,
        max_page_size: int = 100,
        cache_timeout: int = 300,
    ):
        self.queryset = queryset
        self.per_page = min(per_page, max_page_size)
        self.cache_timeout = cache_timeout

    def get_page(self, page_number: int) -> Tuple[List[Any], Dict[str, Any]]:
        """Get paginated results with metadata"""
        cache_key = f"page_{hash(str(self.queryset.query))}_{page_number}"

        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data["results"], cached_data["meta"]

        # Execute query with optimizations
        paginator = Paginator(self.queryset, self.per_page)

        try:
            page = paginator.page(page_number)
        except EmptyPage:
            return [], {
                "total_items": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_number,
                "per_page": self.per_page,
                "has_next": False,
                "has_previous": page_number > 1,
            }

        # Optimize query for pagination
        if hasattr(self.queryset.model, "get_optimized_queryset"):
            optimized_queryset = self.queryset.model.get_optimized_queryset()
        else:
            optimized_queryset = self.queryset

        results = list(optimized_queryset[page.start_index() : page.end_index()])

        metadata = {
            "total_items": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page_number,
            "per_page": self.per_page,
            "has_next": page.has_next(),
            "has_previous": page.has_previous(),
        }

        # Cache results
        cache.set(cache_key, {"results": results, "meta": metadata}, self.cache_timeout)

        return results, metadata


class QueryProfiler:
    """Query profiling and analysis"""

    def __init__(self):
        self.query_count = 0
        self.query_time = 0
        self.slow_queries = []

    def __enter__(self):
        from django.db import connection

        self.connection = connection
        self.initial_queries = len(self.connection.queries)
        self.initial_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        final_time = time.time()
        final_queries = len(self.connection.queries)

        self.query_count = final_queries - self.initial_queries
        self.query_time = final_time - self.initial_time

        # Analyze slow queries
        for query in self.connection.queries[self.initial_queries :]:
            query_time = float(query["time"])
            if query_time > 0.1:  # Slow query threshold
                self.slow_queries.append(
                    {
                        "sql": query["sql"],
                        "time": query_time,
                        "stack": query.get("stack_trace", ""),
                    }
                )

        # Log profiling results
        logger.info(
            f"Query Profile: {self.query_count} queries in {self.query_time:.3f}s"
        )

        if self.slow_queries:
            logger.warning(f"Found {len(self.slow_queries)} slow queries")
            for slow_query in self.slow_queries[:5]:  # Log top 5
                logger.warning(
                    f"Slow query ({slow_query['time']:.3f}s): {slow_query['sql'][:200]}..."
                )


def profile_queries(func):
    """Decorator to profile database queries in a function"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with QueryProfiler() as profiler:
            result = func(*args, **kwargs)

        # Add profiling info to result if it's a dict
        if isinstance(result, dict):
            result["_query_profile"] = {
                "query_count": profiler.query_count,
                "query_time": profiler.query_time,
                "slow_queries": len(profiler.slow_queries),
            }

        return result

    return wrapper


class IndexOptimizer:
    """Database index optimization utilities"""

    @staticmethod
    def suggest_indexes(model_class: type[T]) -> List[Dict[str, Any]]:
        """Suggest optimal indexes based on query patterns"""
        suggestions = []

        # Analyze model fields
        for field in model_class._meta.fields:
            # Suggest index for foreign keys
            if field.is_relation and field.concrete:
                suggestions.append(
                    {
                        "field": field.name,
                        "type": "btree",
                        "reason": f"Foreign key to {field.related_model.__name__}",
                    }
                )

            # Suggest index for fields with db_index=True
            if field.db_index and not field.unique:
                suggestions.append(
                    {
                        "field": field.name,
                        "type": "btree",
                        "reason": "Explicit index requested",
                    }
                )

        # Analyze common query patterns (this would require query logging)
        # For now, suggest composite indexes for common patterns
        if hasattr(model_class, "get_common_query_patterns"):
            for pattern in model_class.get_common_query_patterns():
                suggestions.append(
                    {
                        "fields": pattern["fields"],
                        "type": "composite",
                        "reason": pattern["reason"],
                    }
                )

        return suggestions


class CachingManager(models.Manager):
    """Manager with built-in caching"""

    def get_cached(self, pk, timeout=300):
        """Get object from cache or database"""
        cache_key = f"{self.model.__name__}_{pk}"
        obj = cache.get(cache_key)

        if obj is None:
            obj = self.get_queryset().get(pk=pk)
            cache.set(cache_key, obj, timeout)

        return obj

    def invalidate_cache(self, pk):
        """Invalidate cache for an object"""
        cache_key = f"{self.model.__name__}_{pk}"
        cache.delete(cache_key)


# Common query patterns for healthcare data
HEALTHCARE_QUERY_PATTERNS = {
    "Patient": [
        {
            "fields": ["hospital", "status", "last_name"],
            "reason": "Common patient listing by hospital and status",
        },
        {
            "fields": ["hospital", "date_of_birth"],
            "reason": "Age-based queries within hospital",
        },
    ],
    "Appointment": [
        {
            "fields": ["hospital", "appointment_date", "status"],
            "reason": "Daily appointment schedules by hospital",
        },
        {
            "fields": ["patient", "appointment_date"],
            "reason": "Patient appointment history",
        },
    ],
    "MedicalRecord": [
        {
            "fields": ["patient", "record_date"],
            "reason": "Chronological patient records",
        },
        {
            "fields": ["hospital", "record_type", "record_date"],
            "reason": "Hospital record type filtering",
        },
    ],
}
