"""
Django ORM Query Optimization Suite for HMS Enterprise System
Advanced query optimization, N+1 prevention, and performance monitoring
"""

import functools
import logging
import time
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Set, Type

from django_prometheus import metrics

from django.core.cache import cache
from django.db import connection, models, reset_queries
from django.db.models import (
    ForeignKey,
    Manager,
    ManyToManyField,
    OneToOneField,
    QuerySet,
)
from django.db.models.signals import post_find, pre_find
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# Prometheus metrics for ORM monitoring
orm_metrics = {
    "query_count": metrics.Counter(
        "hms_orm_query_count_total",
        "Total number of ORM queries executed",
        ["model", "operation"],
    ),
    "query_duration": metrics.Histogram(
        "hms_orm_query_duration_seconds",
        "ORM query duration in seconds",
        ["model", "operation", "query_type"],
    ),
    "n_plus_one_detected": metrics.Counter(
        "hms_orm_n_plus_one_detected_total",
        "Total number of N+1 query patterns detected",
        ["model", "field"],
    ),
    "select_related_usage": metrics.Counter(
        "hms_orm_select_related_total",
        "Total number of select_related optimizations applied",
        ["model", "fields_count"],
    ),
    "prefetch_related_usage": metrics.Counter(
        "hms_orm_prefetch_related_total",
        "Total number of prefetch_related optimizations applied",
        ["model", "fields_count"],
    ),
    "cache_hits": metrics.Counter(
        "hms_orm_cache_hits_total",
        "Total number of ORM cache hits",
        ["model", "cache_type"],
    ),
    "cache_misses": metrics.Counter(
        "hms_orm_cache_misses_total",
        "Total number of ORM cache misses",
        ["model", "cache_type"],
    ),
}


class QueryOptimizer:
    """Advanced Django ORM query optimization tools"""

    def __init__(self):
        self.query_patterns = {}
        self.slow_query_threshold = 0.1  # seconds
        self.cache_ttl = 3600  # 1 hour

    @contextmanager
    def query_timer(self, model_name: str, operation: str):
        """Context manager for timing queries"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            orm_metrics["query_duration"].labels(
                model=model_name, operation=operation, query_type="orm"
            ).observe(duration)

            if duration > self.slow_query_threshold:
                logger.warning(
                    f"Slow ORM query detected: {model_name}.{operation} took {duration:.3f}s"
                )

    def detect_n_plus_one(self, queryset: QuerySet) -> List[str]:
        """Detect potential N+1 query patterns"""
        warnings = []
        model = queryset.model
        model_name = model.__name__

        # Check for missing select_related on foreign keys
        for field in model._meta.fields:
            if isinstance(field, (ForeignKey, OneToOneField)):
                field_name = field.name
                if field_name not in str(queryset.query):
                    warnings.append(
                        f"Potential N+1: {model_name}.{field_name} - "
                        f"Consider using select_related('{field_name}')"
                    )
                    orm_metrics["n_plus_one_detected"].labels(
                        model=model_name, field=field_name
                    ).inc()

        # Check for missing prefetch_related on many-to-many
        for field in model._meta.many_to_many:
            field_name = field.name
            if field_name not in str(queryset.query):
                warnings.append(
                    f"Potential N+1: {model_name}.{field_name} - "
                    f"Consider using prefetch_related('{field_name}')"
                )
                orm_metrics["n_plus_one_detected"].labels(
                    model=model_name, field=field_name
                ).inc()

        return warnings

    def optimize_queryset(self, queryset: QuerySet, **kwargs) -> QuerySet:
        """Apply intelligent optimizations to a queryset"""
        model = queryset.model
        model_name = model.__name__

        with self.query_timer(model_name, "optimize_queryset"):
            # Apply select_related for foreign keys if not already present
            if "select_related" not in kwargs:
                fk_fields = self._get_frequently_accessed_foreign_keys(model)
                if fk_fields:
                    queryset = queryset.select_related(*fk_fields)
                    orm_metrics["select_related_usage"].labels(
                        model=model_name, fields_count=str(len(fk_fields))
                    ).inc()

            # Apply prefetch_related for many-to-many if not already present
            if "prefetch_related" not in kwargs:
                m2m_fields = self._get_frequently_accessed_m2m_fields(model)
                if m2m_fields:
                    queryset = queryset.prefetch_related(*m2m_fields)
                    orm_metrics["prefetch_related_usage"].labels(
                        model=model_name, fields_count=str(len(m2m_fields))
                    ).inc()

            # Apply field optimization
            if "only" in kwargs:
                queryset = queryset.only(*kwargs["only"])
            elif "defer" in kwargs:
                queryset = queryset.defer(*kwargs["defer"])

            # Apply ordering optimization
            if queryset.query.order_by and len(queryset.query.order_by) > 1:
                # Check if we have an index that covers the ordering
                optimal_order = self._optimize_ordering(queryset)
                if optimal_order:
                    queryset = queryset.order_by(*optimal_order)

        return queryset

    def _get_frequently_accessed_foreign_keys(
        self, model: Type[models.Model]
    ) -> List[str]:
        """Get foreign keys that are frequently accessed"""
        # This would normally be determined by query analysis
        # For now, return common patterns
        fk_fields = []
        for field in model._meta.fields:
            if isinstance(field, (ForeignKey, OneToOneField)):
                # Include if field name suggests it's commonly accessed
                common_patterns = [
                    "user",
                    "created_by",
                    "updated_by",
                    "hospital",
                    "patient",
                ]
                if any(pattern in field.name.lower() for pattern in common_patterns):
                    fk_fields.append(field.name)
        return fk_fields

    def _get_frequently_accessed_m2m_fields(
        self, model: Type[models.Model]
    ) -> List[str]:
        """Get many-to-many fields that are frequently accessed"""
        m2m_fields = []
        for field in model._meta.many_to_many:
            # Include if field name suggests it's commonly accessed
            common_patterns = ["tags", "categories", "groups", "permissions"]
            if any(pattern in field.name.lower() for pattern in common_patterns):
                m2m_fields.append(field.name)
        return m2m_fields

    def _optimize_ordering(self, queryset: QuerySet) -> Optional[List[str]]:
        """Optimize query ordering based on available indexes"""
        model = queryset.model
        current_order = queryset.query.order_by

        # Check if we have an index that matches or partially matches the ordering
        for index in model._meta.indexes:
            if hasattr(index, "fields"):
                index_fields = index.fields
                if all(field in current_order for field in index_fields):
                    # Use the index order if it covers our needs
                    return list(index_fields)

        return None

    def cached_queryset(self, queryset: QuerySet, timeout: int = None) -> QuerySet:
        """Create a cached version of a queryset"""
        model = queryset.model
        model_name = model.__name__
        cache_key = self._generate_cache_key(queryset)

        # Try to get from cache
        result = cache.get(cache_key)
        if result is not None:
            orm_metrics["cache_hits"].labels(
                model=model_name, cache_type="queryset"
            ).inc()
            return result

        # Execute and cache
        orm_metrics["cache_misses"].labels(
            model=model_name, cache_type="queryset"
        ).inc()

        # Convert to list to force evaluation
        result = list(queryset)
        cache.set(cache_key, result, timeout or self.cache_ttl)
        return result

    def _generate_cache_key(self, queryset: QuerySet) -> str:
        """Generate a unique cache key for a queryset"""
        model = queryset.model
        sql, params = queryset.query.sql_with_params()
        key = f"orm:{model.__name__}:{hash(sql + str(params))}"
        return key

    def bulk_operations(
        self,
        model: Type[models.Model],
        objects: List[Dict[str, Any]],
        operation: str = "create",
        batch_size: int = 1000,
    ) -> Dict[str, Any]:
        """Optimized bulk operations"""
        model_name = model.__name__
        results = {"created": 0, "errors": []}

        with self.query_timer(model_name, f"bulk_{operation}"):
            try:
                if operation == "create":
                    model.objects.bulk_create(
                        [model(**obj) for obj in objects],
                        batch_size=batch_size,
                        ignore_conflicts=True,
                    )
                    results["created"] = len(objects)

                elif operation == "update":
                    # For bulk updates, we need to identify objects first
                    primary_keys = [obj.get("id") for obj in objects if "id" in obj]
                    if primary_keys:
                        existing = model.objects.filter(id__in=primary_keys)
                        updated_count = 0
                        for obj in objects:
                            if "id" in obj:
                                existing.filter(id=obj["id"]).update(
                                    **{k: v for k, v in obj.items() if k != "id"}
                                )
                                updated_count += 1
                        results["updated"] = updated_count

            except Exception as e:
                logger.error(f"Error in bulk {operation} for {model_name}: {e}")
                results["errors"].append(str(e))

        return results


class OptimizedQuerySet(models.QuerySet):
    """Optimized QuerySet with automatic optimizations"""

    def __init__(self, model=None, query=None, using=None, hints=None):
        super().__init__(model, query, using, hints)
        self._optimizer = QueryOptimizer()

    def optimized(self, **kwargs):
        """Apply intelligent optimizations"""
        return self._optimizer.optimize_queryset(self, **kwargs)

    def cached(self, timeout=None):
        """Return cached version of queryset"""
        return self._optimizer.cached_queryset(self, timeout)

    def bulk_create_optimized(self, objects, batch_size=1000):
        """Optimized bulk create with monitoring"""
        return self._optimizer.bulk_operations(
            self.model, objects, "create", batch_size
        )

    def detect_n_plus_one(self):
        """Detect and warn about potential N+1 patterns"""
        warnings = self._optimizer.detect_n_plus_one(self)
        if warnings:
            logger.warning("N+1 Query Patterns Detected:\n" + "\n".join(warnings))
        return warnings


class OptimizedManager(models.Manager):
    """Manager with optimized query methods"""

    def get_queryset(self):
        return OptimizedQuerySet(self.model, using=self._db)

    def get_optimized(self, **kwargs):
        """Get single object with optimizations"""
        return self.get_queryset().optimized(**kwargs).get(**kwargs)

    def filter_optimized(self, **kwargs):
        """Filter with optimizations"""
        return self.get_queryset().optimized(**kwargs).filter(**kwargs)

    def all_optimized(self, **kwargs):
        """All with optimizations"""
        return self.get_queryset().optimized(**kwargs).all()

    def bulk_create_optimized(self, objects, batch_size=1000):
        """Optimized bulk create"""
        return self.get_queryset().bulk_create_optimized(objects, batch_size)


class QueryProfiler:
    """Advanced query profiling and analysis"""

    def __init__(self):
        self.profiles = {}
        self.current_profile = None

    @contextmanager
    def profile_queries(self, profile_name: str):
        """Profile all queries within a context"""
        self.current_profile = profile_name
        reset_queries()
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            queries = connection.queries
            self.profiles[profile_name] = {
                "total_queries": len(queries),
                "total_time": end_time - start_time,
                "queries": queries,
                "slow_queries": [q for q in queries if float(q["time"]) > 0.1],
            }
            self.current_profile = None
            self._analyze_profile(profile_name)

    def _analyze_profile(self, profile_name: str):
        """Analyze query profile and provide recommendations"""
        profile = self.profiles[profile_name]

        # Check for duplicate queries
        query_counts = {}
        for query in profile["queries"]:
            sql = query["sql"]
            query_counts[sql] = query_counts.get(sql, 0) + 1

        duplicates = {sql: count for sql, count in query_counts.items() if count > 1}

        # Analyze recommendations
        recommendations = []

        if duplicates:
            recommendations.append(
                f"Found {len(duplicates)} duplicate queries. Consider caching or bulk operations."
            )

        if profile["slow_queries"]:
            recommendations.append(
                f"Found {len(profile['slow_queries'])} slow queries (>100ms). "
                "Consider adding indexes or optimizing queries."
            )

        if profile["total_queries"] > 50:
            recommendations.append(
                f"High number of queries ({profile['total_queries']}). "
                "Consider using select_related/prefetch_related."
            )

        profile["recommendations"] = recommendations
        profile["duplicate_queries"] = duplicates

    def get_profile_report(self, profile_name: str) -> Dict[str, Any]:
        """Get detailed report for a profile"""
        if profile_name not in self.profiles:
            return {"error": "Profile not found"}

        profile = self.profiles[profile_name]
        return {
            "profile_name": profile_name,
            "total_queries": profile["total_queries"],
            "total_time": round(profile["total_time"], 3),
            "average_query_time": (
                round(
                    sum(float(q["time"]) for q in profile["queries"])
                    / len(profile["queries"]),
                    3,
                )
                if profile["queries"]
                else 0
            ),
            "slow_queries_count": len(profile["slow_queries"]),
            "duplicate_queries_count": len(profile.get("duplicate_queries", {})),
            "recommendations": profile.get("recommendations", []),
            "slowest_queries": sorted(
                profile["queries"], key=lambda x: float(x["time"]), reverse=True
            )[:5],
        }


# Global profiler instance
query_profiler = QueryProfiler()


def profile_queries(func):
    """Decorator to profile queries in a function"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with query_profiler.profile_queries(func.__name__):
            return func(*args, **kwargs)

    return wrapper


class QueryCache:
    """Advanced query caching system"""

    def __init__(self):
        self.cache_prefix = "orm_cache:"
        self.default_timeout = 3600  # 1 hour

    def get_cache_key(
        self, model: Type[models.Model], query_type: str, params: Dict[str, Any]
    ) -> str:
        """Generate cache key for a query"""
        import hashlib

        param_str = str(sorted(params.items()))
        key_str = f"{self.cache_prefix}{model.__name__}:{query_type}:{param_str}"
        return hashlib.hashlib.sha256(key_str.encode()).hexdigest()

    def get_or_set(
        self,
        model: Type[models.Model],
        query_type: str,
        params: Dict[str, Any],
        query_func: Callable,
        timeout: int = None,
    ) -> Any:
        """Get from cache or execute and cache query"""
        cache_key = self.get_cache_key(model, query_type, params)
        result = cache.get(cache_key)

        if result is not None:
            orm_metrics["cache_hits"].labels(
                model=model.__name__, cache_type="custom"
            ).inc()
            return result

        # Execute query
        result = query_func(**params)

        # Cache result
        cache.set(cache_key, result, timeout or self.default_timeout)
        orm_metrics["cache_misses"].labels(
            model=model.__name__, cache_type="custom"
        ).inc()

        return result

    def invalidate(self, model: Type[models.Model], instance_pk: Any = None):
        """Invalidate cache for a model or specific instance"""
        pattern = f"{self.cache_prefix}{model.__name__}:*"
        keys = cache.keys(pattern)

        if instance_pk:
            # Only invalidate specific instance-related keys
            keys = [k for k in keys if str(instance_pk) in k]

        cache.delete_many(keys)


# Global cache instance
query_cache = QueryCache()


# Model mixins for automatic optimization
class OptimizedModelMixin:
    """Mixin to add optimization features to models"""

    objects = OptimizedManager()

    class Meta:
        abstract = True

    @classmethod
    def get_cached(cls, pk):
        """Get cached instance by primary key"""
        cache_key = f"model:{cls.__name__}:{pk}"
        instance = cache.get(cache_key)

        if instance is None:
            instance = cls.objects.get(pk=pk)
            cache.set(cache_key, instance, 3600)  # 1 hour cache

        return instance

    def save(self, *args, **kwargs):
        """Override save to invalidate cache"""
        super().save(*args, **kwargs)
        # Invalidate cache for this model
        query_cache.invalidate(self.__class__, self.pk)

    def delete(self, *args, **kwargs):
        """Override delete to invalidate cache"""
        pk = self.pk
        super().delete(*args, **kwargs)
        # Invalidate cache for this model
        query_cache.invalidate(self.__class__, pk)


# Signal receivers for automatic optimization
@receiver(pre_find)
def pre_find_receiver(sender, **kwargs):
    """Called before a find operation"""
    logger.debug(f"Pre-find signal for {sender.__name__}")


@receiver(post_find)
def post_find_receiver(sender, **kwargs):
    """Called after a find operation"""
    logger.debug(f"Post-find signal for {sender.__name__}")
    # Update query patterns for analysis
    if "queryset" in kwargs:
        queryset = kwargs["queryset"]
        # Store query pattern for future optimization suggestions
