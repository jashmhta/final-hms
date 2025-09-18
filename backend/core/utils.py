import requests
import time
import logging
from pybreaker import CircuitBreaker
from tenacity import retry, stop_after_attempt, wait_exponential
from django.db import models
from django.db.models import QuerySet
logger = logging.getLogger(__name__)
api_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)
class PerformanceTracker:
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    def __enter__(self):
        self.start_time = time.time()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"Operation '{self.operation_name}' took {duration:.3f} seconds")
    def get_duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
@api_breaker
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_api_call(url, method="GET", **kwargs):
    return requests.request(method, url, **kwargs)
def optimize_queryset(queryset: QuerySet) -> QuerySet:
    if hasattr(queryset.model, 'hospital'):
        queryset = queryset.select_related('hospital')
    if hasattr(queryset.model, 'user'):
        queryset = queryset.select_related('user')
    if hasattr(queryset.model, 'patient'):
        queryset = queryset.select_related('patient')
    return queryset
def custom_exception_handler(exc, context):
    from rest_framework.views import exception_handler
    from rest_framework.response import Response
    response = exception_handler(exc, context)
    if response is None:
        response = Response({
            'error': 'Internal server error',
            'detail': str(exc)
        }, status=500)
    response.data['operation'] = context.get('view').__class__.__name__ if context.get('view') else 'unknown'
    response.data['timestamp'] = time.time()
    return response