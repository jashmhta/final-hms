"""
Multi-Tier Caching Strategy for HMS
Redis + Database + Application Level Caching
"""

import hashlib
import json
import logging
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

import redis
from django_redis import get_redis_connection
from redis.connection import ConnectionPool

from django.conf import settings
from django.core.cache import cache, caches
from django.core.cache.backends.base import BaseCache

logger = logging.getLogger(__name__)


class CacheOptimizer:
    """Advanced caching optimization with multi-tier strategy"""

    def __init__(self):
        self.cache_config = getattr(settings, "CACHE_CONFIG", {})
        self.default_timeout = self.cache_config.get("default_timeout", 300)
        self.key_prefix = self.cache_config.get("key_prefix", "hms:")
        self.redis_client = None
        self._connection_pool = None
        self._lock = threading.RLock()
        self.redis_client = self._get_redis_connection()

    def _get_redis_connection(self) -> Optional[redis.Redis]:
        """Get Redis connection with connection pooling"""
        with self._lock:
            if self.redis_client is not None:
                return self.redis_client

            try:
                # Use connection pool for better performance
                if hasattr(settings, "CACHES") and "default" in settings.CACHES:
                    self._connection_pool = ConnectionPool.from_url(
                        settings.CACHES["default"]["LOCATION"],
                        max_connections=10,  # Reduced to prevent connection leaks
                        retry_on_timeout=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                    )
                else:
                    self._connection_pool = ConnectionPool(
                        host=getattr(settings, "REDIS_HOST", "localhost"),
                        port=getattr(settings, "REDIS_PORT", 6379),
                        max_connections=10,
                        retry_on_timeout=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                    )

                self.redis_client = redis.Redis(connection_pool=self._connection_pool)
                # Test connection
                self.redis_client.ping()
                return self.redis_client
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
                return None

    def cleanup(self):
        """Cleanup Redis connections"""
        with self._lock:
            if self._connection_pool:
                try:
                    self._connection_pool.disconnect()
                except Exception:
                    pass
                self._connection_pool = None
            self.redis_client = None

    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup()

    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache keys"""
        key_parts = [self.key_prefix, prefix]
        key_parts.extend(str(arg) for arg in args)
        if kwargs:
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        return hashlib.hashlib.sha256(key_string.encode()).hexdigest()

    def smart_cache(
        self,
        key: str,
        data_func: Callable,
        timeout: int = None,
        tier: str = "redis",
        compress: bool = True,
    ) -> Any:
        """
        Smart caching with automatic tier selection
        tier: 'redis' | 'local' | 'database'
        """
        timeout = timeout or self.default_timeout
        cache_key = f"{self.key_prefix}{key}"

        # Try to get from cache
        if tier == "redis" and self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return pickle.loads(cached_data)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        elif tier == "local":
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        # Execute function to get data
        data = data_func()

        # Store in cache
        serialized_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

        if tier == "redis" and self.redis_client:
            try:
                if compress and len(serialized_data) > 1024:  # Compress if > 1KB
                    import zlib

                    serialized_data = zlib.compress(serialized_data)
                self.redis_client.setex(cache_key, timeout, serialized_data)
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
        elif tier == "local":
            cache.set(cache_key, data, timeout)

        return data

    def cache_invalidate(self, pattern: str = None, keys: List[str] = None):
        """Invalidate cache entries"""
        if keys:
            for key in keys:
                cache_key = f"{self.key_prefix}{key}"
                cache.delete(cache_key)
                if self.redis_client:
                    self.redis_client.delete(cache_key)

        if pattern and self.redis_client:
            try:
                # Use SCAN for production safety
                for key in self.redis_client.scan_iter(
                    match=f"{self.key_prefix}{pattern}*"
                ):
                    self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")

    def bulk_cache_set(self, data_dict: Dict[str, Any], timeout: int = None):
        """Set multiple cache values efficiently"""
        timeout = timeout or self.default_timeout
        pipe = None

        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                for key, value in data_dict.items():
                    cache_key = f"{self.key_prefix}{key}"
                    pipe.setex(cache_key, timeout, pickle.dumps(value))
                pipe.execute()
            except Exception as e:
                logger.warning(f"Bulk cache set failed: {e}")

        # Fallback to local cache
        if not pipe:
            for key, value in data_dict.items():
                cache.set(f"{self.key_prefix}{key}", value, timeout)


class QueryCache:
    """Database query result caching"""

    def __init__(self, optimizer: CacheOptimizer):
        self.optimizer = optimizer

    def cache_queryset(self, queryset, timeout: int = 300):
        """Cache queryset results"""
        # Generate cache key from query
        query_string = str(queryset.query)
        cache_key = self.optimizer.generate_cache_key("query", query_string)

        return self.optimizer.smart_cache(
            cache_key, lambda: list(queryset), timeout=timeout
        )

    def cache_count(self, queryset, timeout: int = 60):
        """Cache count results"""
        query_string = str(queryset.query)
        cache_key = self.optimizer.generate_cache_key("count", query_string)

        return self.optimizer.smart_cache(cache_key, queryset.count, timeout=timeout)


class ApplicationCache:
    """Application-level caching strategies"""

    def __init__(self, optimizer: CacheOptimizer):
        self.optimizer = optimizer

    def cache_user_permissions(self, user_id: int, timeout: int = 300):
        """Cache user permissions"""
        cache_key = f"user_perms:{user_id}"

        def get_permissions():
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType

            # This would be customized based on your permission system
            return list(user.get_all_permissions())

        return self.optimizer.smart_cache(cache_key, get_permissions, timeout=timeout)

    def cache_hospital_config(self, hospital_id: int, timeout: int = 3600):
        """Cache hospital configuration"""
        cache_key = f"hospital_config:{hospital_id}"

        def get_config():
            from hospitals.models import Hospital

            hospital = Hospital.objects.select_related("plan").get(id=hospital_id)
            return {
                "settings": hospital.settings,
                "plan_features": hospital.plan.get_features(),
                "modules_enabled": hospital.get_enabled_modules(),
            }

        return self.optimizer.smart_cache(cache_key, get_config, timeout=timeout)


def cache_result(timeout: int = 300, tier: str = "redis", key_prefix: str = None):
    """Decorator for caching function results"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = key_prefix or f"{func.__name__}"
            if args or kwargs:
                cache_key += f":{hash(str(args) + str(sorted(kwargs.items())))}"

            optimizer = CacheOptimizer()
            return optimizer.smart_cache(
                cache_key, lambda: func(*args, **kwargs), timeout=timeout, tier=tier
            )

        return wrapper

    return decorator


class CacheWarmer:
    """Proactive cache warming for frequently accessed data"""

    def __init__(self):
        self.optimizer = CacheOptimizer()

    def warm_common_data(self):
        """Warm cache with commonly accessed data"""
        # Active patients
        self.optimizer.smart_cache(
            "active_patients_count",
            lambda: self._get_active_patients_count(),
            timeout=60,
        )

        # Today's appointments
        self.optimizer.smart_cache(
            "todays_appointments", lambda: self._get_todays_appointments(), timeout=300
        )

        # Hospital statistics
        self.optimizer.smart_cache(
            "hospital_stats", lambda: self._get_hospital_stats(), timeout=600
        )

    def _get_active_patients_count(self):
        from patients.models import Patient

        return Patient.objects.filter(status="ACTIVE").count()

    def _get_todays_appointments(self):
        from django.utils import timezone

        from appointments.models import Appointment

        today = timezone.now().date()
        return list(
            Appointment.objects.filter(
                appointment_date=today, status__in=["SCHEDULED", "CHECKED_IN"]
            ).values("id", "patient_id", "scheduled_time")
        )

    def _get_hospital_stats(self):
        from django.db.models import Count

        from hospitals.models import Hospital

        return list(
            Hospital.objects.annotate(
                patient_count=Count("patients"), appointment_count=Count("appointments")
            ).values("id", "name", "patient_count", "appointment_count")
        )


# Global cache optimizer instance
cache_optimizer = CacheOptimizer()
query_cache = QueryCache(cache_optimizer)
app_cache = ApplicationCache(cache_optimizer)
cache_warmer = CacheWarmer()
