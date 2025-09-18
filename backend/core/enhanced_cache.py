import json
import pickle
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, Callable
from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django.core.cache.backends.base import BaseCache
from django_redis import get_redis_connection
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
        return hashlib.md5(key_data.encode()).hexdigest()
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
def cache_result(timeout: int = None, key_prefix: str = "", tags: list = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            enhanced_cache = EnhancedCache()
            cache_key = enhanced_cache.generate_cache_key(
                f"{key_prefix}:{func.__name__}", *args, **kwargs
            )
            result = enhanced_cache.cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            result = func(*args, **kwargs)
            enhanced_cache.set_with_tags(
                cache_key, result, timeout or CacheConfig.MEDIUM_TIMEOUT, tags
            )
            logger.debug(f"Cache miss and set for {cache_key}")
            return result
        return wrapper
    return decorator
def cache_patient_view(timeout: int = CacheConfig.LONG_TIMEOUT):
    return cache_result(
        timeout=timeout, key_prefix="patient_view", tags=["patient_data"]
    )
def cache_analytics_view(timeout: int = CacheConfig.SHORT_TIMEOUT):
    return cache_result(
        timeout=timeout, key_prefix="analytics_view", tags=["analytics_data"]
    )
try:
    enhanced_cache = EnhancedCache()
except Exception:
    enhanced_cache = None
def cache_result(timeout: int = None, key_prefix: str = "", tags: list = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if enhanced_cache is None:
                return func(*args, **kwargs)
            cache_instance = EnhancedCache()
            cache_key = cache_instance.generate_cache_key(
                f"{key_prefix}:{func.__name__}", *args, **kwargs
            )
            result = cache_instance.cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            result = func(*args, **kwargs)
            cache_instance.set_with_tags(
                cache_key, result, timeout or CacheConfig.MEDIUM_TIMEOUT, tags
            )
            logger.debug(f"Cache miss and set for {cache_key}")
            return result
        return wrapper
    return decorator