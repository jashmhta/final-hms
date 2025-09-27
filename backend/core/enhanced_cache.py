"""
enhanced_cache module
"""

import hashlib
import json
import logging
import pickle
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from django_redis import get_redis_connection

from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import BaseCache
from django.core.signals import request_finished, request_started
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class CacheConfig:
    SHORT_TIMEOUT = 300
    MEDIUM_TIMEOUT = 1800
    LONG_TIMEOUT = 3600
    VERY_LONG_TIMEOUT = 86400
    PATIENT_CACHE_PREFIX = "patient:"
    APPOINTMENT_CACHE_PREFIX = "appt:"
    BILLING_CACHE_PREFIX = "bill:"
    ANALYTICS_CACHE_PREFIX = "analytics:"
    USER_CACHE_PREFIX = "user:"
    HOSPITAL_CACHE_PREFIX = "hospital:"
    CACHE_STRATEGIES = {
        "write_through": "write_through",
        "write_behind": "write_behind",
        "cache_aside": "cache_aside",
        "refresh_ahead": "refresh_ahead",
    }


class EnhancedCache:
    def __init__(self, cache_backend: Optional[BaseCache] = None):
        self.cache = cache_backend or cache
        self.config = CacheConfig()
        try:
            self.redis = get_redis_connection("default")
        except (NotImplementedError, ImportError, Exception):
            self.redis = None

    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        if kwargs:
            key_data += f":{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.hashlib.sha256(key_data.encode()).hexdigest()

    def get_with_fallback(
        self, key: str, fallback_func: Callable, timeout: int = None
    ) -> Any:
        result = self.cache.get(key)
        if result is None:
            result = fallback_func()
            self.cache.set(key, result, timeout or self.config.MEDIUM_TIMEOUT)
        return result

    def set_with_tags(
        self, key: str, value: Any, timeout: int, tags: list = None
    ) -> None:
        self.cache.set(key, value, timeout)
        if tags and self.redis:
            for tag in tags:
                tag_key = f"tag:{tag}"
                self.redis.sadd(tag_key, key)
                self.redis.expire(tag_key, timeout)

    def invalidate_by_tag(self, tag: str) -> None:
        if self.redis:
            tag_key = f"tag:{tag}"
            keys = self.redis.smembers(tag_key)
            if keys:
                self.cache.delete_many(keys)
                self.redis.delete(tag_key)

    def cache_patient_data(self, patient_id: Union[str, int], data: Dict) -> None:
        patient_key = self.generate_cache_key(
            self.config.PATIENT_CACHE_PREFIX, patient_id
        )
        self.set_with_tags(
            patient_key,
            data,
            self.config.LONG_TIMEOUT,
            [f"patient_{patient_id}", "patient_data"],
        )
        if "hospital_id" in data:
            hospital_key = self.generate_cache_key(
                self.config.HOSPITAL_CACHE_PREFIX,
                data["hospital_id"],
                "patient",
                patient_id,
            )
            self.cache.set(hospital_key, data, self.config.LONG_TIMEOUT)

    def cache_analytics_data(self, hospital_id: Union[str, int], data: Dict) -> None:
        analytics_key = self.generate_cache_key(
            self.config.ANALYTICS_CACHE_PREFIX,
            hospital_id,
            datetime.now().strftime("%Y-%m-%d"),
        )
        self.set_with_tags(
            analytics_key,
            data,
            self.config.SHORT_TIMEOUT,
            [f"analytics_{hospital_id}", "analytics_data"],
        )
        next_hour_key = self.generate_cache_key(
            self.config.ANALYTICS_CACHE_PREFIX,
            hospital_id,
            (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d-%H"),
        )
        self.cache.set(next_hour_key, data, self.config.VERY_LONG_TIMEOUT)

    def cache_queryset(
        self,
        queryset_key: str,
        queryset_data: List[Dict],
        timeout: int = None,
        tags: List[str] = None,
    ) -> None:
        """Cache queryset results with optimized serialization"""
        if not queryset_data:
            return

        try:
            # Optimize for large datasets
            serialized_data = json.dumps(
                {
                    "count": len(queryset_data),
                    "data": queryset_data,
                    "timestamp": datetime.now().isoformat(),
                    "cached_by": "enhanced_cache",
                },
                separators=(",", ":"),
            )  # Compact JSON

            cache_key = f"qs:{self.generate_cache_key(queryset_key)}"
            self.cache.set(
                cache_key, serialized_data, timeout or self.config.MEDIUM_TIMEOUT
            )

            if tags and self.redis:
                for tag in tags:
                    tag_key = f"tag:{tag}"
                    self.redis.sadd(tag_key, cache_key)
                    self.redis.expire(tag_key, timeout or self.config.MEDIUM_TIMEOUT)

            logger.debug(
                f"Cached queryset: {queryset_key} ({len(queryset_data)} items)"
            )
        except Exception as e:
            logger.error(f"Error caching queryset {queryset_key}: {str(e)}")

    def get_cached_queryset(self, queryset_key: str) -> Optional[List[Dict]]:
        """Retrieve cached queryset data"""
        try:
            cache_key = f"qs:{self.generate_cache_key(queryset_key)}"
            cached_data = self.cache.get(cache_key)

            if cached_data:
                parsed_data = json.loads(cached_data)
                logger.debug(f"Cache hit for queryset: {queryset_key}")
                return parsed_data.get("data")
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached queryset {queryset_key}: {str(e)}")
            return None

    def bulk_invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate multiple cache entries by tags"""
        if not self.redis:
            return 0

        invalidated_count = 0
        for tag in tags:
            invalidated_count += self.invalidate_by_tag(tag)
        return invalidated_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        stats = {
            "redis_available": self.redis is not None,
            "total_keys": 0,
            "memory_usage": 0,
            "hit_rate": 0,
            "cache_keys_by_tag": {},
        }

        try:
            if self.redis:
                info = self.redis.info()
                stats["total_keys"] = info.get("keyspace_hits", 0) + info.get(
                    "keyspace_misses", 0
                )
                stats["memory_usage"] = info.get("used_memory_human", "N/A")

                hits = info.get("keyspace_hits", 0)
                misses = info.get("keyspace_misses", 0)
                total = hits + misses
                stats["hit_rate"] = round((hits / total * 100), 2) if total > 0 else 0

                # Get cache keys by tag (sample)
                for prefix in [
                    "patient:",
                    "appt:",
                    "bill:",
                    "analytics:",
                    "user:",
                    "hospital:",
                ]:
                    keys = self.redis.keys(f"tag:{prefix}*")
                    stats["cache_keys_by_tag"][prefix] = len(keys)

        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")

        return stats

    def warm_up_cache(self, cache_type: str = "all") -> Dict[str, int]:
        """Warm up cache with frequently accessed data"""
        warmed_up = {}

        try:
            if cache_type in ["all", "patients"]:
                # Cache active patients
                from patients.models import Patient

                active_patients = Patient.objects.filter(
                    status="ACTIVE"
                ).select_related("hospital")[:100]
                for patient in active_patients:
                    patient_data = {
                        "id": patient.id,
                        "first_name": patient.first_name,
                        "last_name": patient.last_name,
                        "hospital_id": patient.hospital_id,
                        "status": patient.status,
                    }
                    self.cache_patient_data(patient.id, patient_data)
                warmed_up["patients"] = len(active_patients)

            if cache_type in ["all", "hospitals"]:
                # Cache hospital information
                from hospitals.models import Hospital

                hospitals = Hospital.objects.filter(status="ACTIVE")[:50]
                for hospital in hospitals:
                    hospital_data = {
                        "id": hospital.id,
                        "name": hospital.name,
                        "code": hospital.code,
                        "status": hospital.status,
                        "capacity": hospital.capacity,
                    }
                    analytics_key = self.generate_cache_key(
                        self.config.HOSPITAL_CACHE_PREFIX, hospital.id, "basic_info"
                    )
                    self.set_with_tags(
                        analytics_key,
                        hospital_data,
                        self.config.LONG_TIMEOUT,
                        [f"hospital_{hospital.code}", "hospital_data"],
                    )
                warmed_up["hospitals"] = len(hospitals)

            if cache_type in ["all", "analytics"]:
                # Cache basic analytics for active hospitals
                from hospitals.models import Hospital

                hospitals = Hospital.objects.filter(status="ACTIVE")[:20]
                for hospital in hospitals:
                    analytics_data = {
                        "hospital_id": hospital.id,
                        "hospital_name": hospital.name,
                        "patient_count": 0,  # Placeholder
                        "active_appointments": 0,  # Placeholder
                        "last_updated": datetime.now().isoformat(),
                    }
                    self.cache_analytics_data(hospital.id, analytics_data)
                warmed_up["analytics"] = len(hospitals)

            logger.info(f"Cache warm-up completed: {warmed_up}")
            return warmed_up

        except Exception as e:
            logger.error(f"Error during cache warm-up: {str(e)}")
            return warmed_up

    def implement_cache_strategy(
        self, strategy: str, key: str, value: Any, timeout: int = None
    ) -> bool:
        """Implement different caching strategies"""
        try:
            if strategy == "write_through":
                # Write to cache and database simultaneously
                self.cache.set(key, value, timeout)
                return True

            elif strategy == "write_behind":
                # Write to cache immediately, queue for database write
                self.cache.set(key, value, timeout)
                if self.redis:
                    self.redis.lpush(
                        "write_behind_queue",
                        json.dumps(
                            {
                                "key": key,
                                "value": value,
                                "timeout": timeout,
                                "timestamp": datetime.now().isoformat(),
                            }
                        ),
                    )
                return True

            elif strategy == "cache_aside":
                # Lazy loading - only cache on first miss
                if self.cache.get(key) is None:
                    self.cache.set(key, value, timeout)
                return True

            elif strategy == "refresh_ahead":
                # Pre-emptively refresh cache before expiration
                current_ttl = self.cache.ttl(key)
                if current_ttl and current_ttl < 300:  # Less than 5 minutes
                    self.cache.set(key, value, timeout)
                    logger.debug(f"Refresh-ahead cache update for key: {key}")
                return True

            else:
                logger.warning(f"Unknown cache strategy: {strategy}")
                return False

        except Exception as e:
            logger.error(f"Error implementing cache strategy {strategy}: {str(e)}")
            return False


class CacheInvalidationManager:
    """Automatic cache invalidation based on model changes"""

    def __init__(self):
        self.enhanced_cache = EnhancedCache()

    def register_model_signals(self, model_class, cache_tags_func):
        """Register Django model signals for automatic cache invalidation"""
        post_save.connect(self._handle_model_save, sender=model_class, weak=False)
        post_delete.connect(self._handle_model_delete, sender=model_class, weak=False)
        self.cache_tags_func = cache_tags_func

    def _handle_model_save(self, sender, instance, created, **kwargs):
        """Handle model save events"""
        try:
            tags = self.cache_tags_func(instance, created=created)
            if tags:
                self.enhanced_cache.bulk_invalidate_by_tags(tags)
                logger.info(
                    f"Cache invalidated for {sender.__name__} instance {instance.id}: {tags}"
                )
        except Exception as e:
            logger.error(
                f"Error handling cache invalidation for {sender.__name__}: {str(e)}"
            )

    def _handle_model_delete(self, sender, instance, **kwargs):
        """Handle model delete events"""
        try:
            tags = self.cache_tags_func(instance, deleted=True)
            if tags:
                self.enhanced_cache.bulk_invalidate_by_tags(tags)
                logger.info(
                    f"Cache invalidated for deleted {sender.__name__} instance {instance.id}: {tags}"
                )
        except Exception as e:
            logger.error(
                f"Error handling cache invalidation for deleted {sender.__name__}: {str(e)}"
            )


# Global cache invalidation manager
cache_invalidation_manager = CacheInvalidationManager()


def get_patient_cache_tags(patient, created=False, deleted=False):
    """Get cache tags for patient model changes"""
    tags = [f"patient_{patient.id}", "patient_data"]
    if hasattr(patient, "hospital_id") and patient.hospital_id:
        tags.append(f"hospital_patient_{patient.hospital_id}")
    return tags


def get_hospital_cache_tags(hospital, created=False, deleted=False):
    """Get cache tags for hospital model changes"""
    tags = [f"hospital_{hospital.code}", "hospital_data", f"analytics_{hospital.id}"]
    if not created and not deleted:
        tags.append("hospitals_list")
    return tags


def get_appointment_cache_tags(appointment, created=False, deleted=False):
    """Get cache tags for appointment model changes"""
    tags = [f"appointment_{appointment.id}", "appointment_data"]
    if hasattr(appointment, "patient_id") and appointment.patient_id:
        tags.append(f"patient_appointments_{appointment.patient_id}")
    if hasattr(appointment, "hospital_id") and appointment.hospital_id:
        tags.append(f"hospital_appointments_{appointment.hospital_id}")
    return tags


# Advanced cache decorators
def cache_with_strategy(
    strategy: str = "cache_aside",
    timeout: int = None,
    key_prefix: str = "",
    tags: list = None,
):
    """Cache decorator with configurable strategy"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            enhanced_cache = EnhancedCache()
            cache_key = enhanced_cache.generate_cache_key(
                f"{key_prefix}:{func.__name__}", *args, **kwargs
            )

            # Try to get from cache first
            result = enhanced_cache.cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key} (strategy: {strategy})")
                return result

            # Execute function
            result = func(*args, **kwargs)

            # Apply caching strategy
            enhanced_cache.implement_cache_strategy(
                strategy, cache_key, result, timeout or CacheConfig.MEDIUM_TIMEOUT
            )

            # Set tags if available
            if tags and enhanced_cache.redis:
                for tag in tags:
                    tag_key = f"tag:{tag}"
                    enhanced_cache.redis.sadd(tag_key, cache_key)
                    enhanced_cache.redis.expire(
                        tag_key, timeout or CacheConfig.MEDIUM_TIMEOUT
                    )

            logger.debug(f"Cache miss and set for {cache_key} (strategy: {strategy})")
            return result

        return wrapper

    return decorator


def cache_queryset_results(
    timeout: int = CacheConfig.MEDIUM_TIMEOUT, tags: list = None
):
    """Decorator for caching queryset results"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            enhanced_cache = EnhancedCache()
            cache_key = enhanced_cache.generate_cache_key(
                f"qs:{func.__name__}", *args, **kwargs
            )

            # Try to get cached queryset
            cached_result = enhanced_cache.get_cached_queryset(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Cache the result
            if isinstance(result, list):
                enhanced_cache.cache_queryset(cache_key, result, timeout, tags)

            return result

        return wrapper

    return decorator


# Register model signals for automatic cache invalidation
def setup_cache_invalidation():
    """Setup automatic cache invalidation for models"""
    try:
        # Lazy imports to avoid circular dependencies
        from appointments.models import Appointment  # noqa: F401
        from hospitals.models import Hospital  # noqa: F401
        from patients.models import Patient  # noqa: F401

        cache_invalidation_manager.register_model_signals(
            Patient, get_patient_cache_tags
        )
        cache_invalidation_manager.register_model_signals(
            Hospital, get_hospital_cache_tags
        )
        cache_invalidation_manager.register_model_signals(
            Appointment, get_appointment_cache_tags
        )

        logger.info(
            "Cache invalidation signals registered for Patient, Hospital, and Appointment models"
        )
    except ImportError as e:
        logger.warning(f"Could not register cache invalidation signals: {str(e)}")


# Enhanced cache decorators with better defaults
def cache_result(
    timeout: int = None,
    key_prefix: str = "",
    tags: list = None,
    strategy: str = "cache_aside",
):
    """Enhanced cache result decorator with strategy support"""
    return cache_with_strategy(
        strategy=strategy, timeout=timeout, key_prefix=key_prefix, tags=tags
    )


def cache_patient_view(timeout: int = CacheConfig.LONG_TIMEOUT):
    return cache_result(
        timeout=timeout,
        key_prefix="patient_view",
        tags=["patient_data"],
        strategy="write_through",
    )


def cache_analytics_view(timeout: int = CacheConfig.SHORT_TIMEOUT):
    return cache_result(
        timeout=timeout,
        key_prefix="analytics_view",
        tags=["analytics_data"],
        strategy="refresh_ahead",
    )


# Cache invalidation setup is deferred to avoid circular imports
# It will be called when the apps are ready


# Global enhanced cache instance
enhanced_cache = EnhancedCache()
