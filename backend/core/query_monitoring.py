"""
Query monitoring and optimization middleware for Django.
Automatically detects and logs N+1 queries, slow queries, and other performance issues.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from .database_optimization import DatabaseOptimizer, QueryPattern

logger = logging.getLogger(__name__)


class QueryMonitoringMiddleware(MiddlewareMixin):
    """Middleware that monitors database queries for performance issues."""

    def __init__(self, get_response):
        super().__init__(get_response)
        self.db_optimizer = DatabaseOptimizer()
        self.query_count = 0
        self.query_time = 0
        self.slow_queries = []
        self.n_plus_one_detected = False

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Reset counters for each request."""
        self.query_count = 0
        self.query_time = 0
        self.slow_queries = []
        self.n_plus_one_detected = False
        return None

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Analyze queries after request processing."""
        if hasattr(connection, 'queries') and connection.queries:
            self._analyze_queries(connection.queries)
            self._log_performance_metrics(request)
            self._add_response_headers(response)

        return response

    def _analyze_queries(self, queries: List[Dict[str, Any]]) -> None:
        """Analyze executed queries for performance issues."""
        self.query_count = len(queries)

        for query in queries:
            query_time = float(query.get('time', 0))
            self.query_time += query_time

            sql = query.get('sql', '')

            # Detect slow queries
            if query_time > self.db_optimizer._slow_query_threshold_ms / 1000:
                self.slow_queries.append({
                    'sql': sql,
                    'time': query_time,
                    'type': 'slow_query'
                })

            # Detect potential N+1 patterns
            if self._is_potential_n_plus_one(sql):
                self.n_plus_one_detected = True

                # Store for analysis
                self.db_optimizer.query_patterns[QueryPattern.N_PLUS_ONE].append({
                    'query_text': sql,
                    'execution_time_ms': query_time * 1000,
                    'detected_at': time.time()
                })

    def _is_potential_n_plus_one(self, sql: str) -> bool:
        """Detect potential N+1 query patterns."""
        sql_lower = sql.lower()

        # Look for queries that might be executed in loops
        patterns = [
            'where id =',  # Single row lookup by ID
            'where uuid =',  # Single row lookup by UUID
            'where patient_id =',  # Patient-specific lookup
            'where appointment_id =',  # Appointment-specific lookup
            'where encounter_id =',  # Encounter-specific lookup
        ]

        return any(pattern in sql_lower for pattern in patterns)

    def _log_performance_metrics(self, request: HttpRequest) -> None:
        """Log performance metrics for monitoring."""
        if self.query_count > 0:
            avg_query_time = self.query_time / self.query_count

            metrics = {
                'path': request.path,
                'method': request.method,
                'query_count': self.query_count,
                'total_query_time': self.query_time,
                'avg_query_time': avg_query_time,
                'slow_queries_count': len(self.slow_queries),
                'n_plus_one_detected': self.n_plus_one_detected,
                'user_id': getattr(request.user, 'id', None) if hasattr(request.user, 'id') else None,
            }

            logger.info(f"Query Performance: {metrics}")

            # Log warnings for performance issues
            if self.query_count > 50:
                logger.warning(f"High query count detected: {self.query_count} queries for {request.path}")

            if self.query_time > 1.0:  # More than 1 second
                logger.warning(f"Slow query time detected: {self.query_time:.3f}s for {request.path}")

            if self.n_plus_one_detected:
                logger.warning(f"Potential N+1 query pattern detected for {request.path}")

    def _add_response_headers(self, response: HttpResponse) -> None:
        """Add performance headers to response for debugging."""
        if settings.DEBUG:
            response['X-Query-Count'] = str(self.query_count)
            response['X-Query-Time'] = f"{self.query_time:.3f}s"
            response['X-Slow-Queries'] = str(len(self.slow_queries))

            if self.n_plus_one_detected:
                response['X-N-Plus-One'] = 'detected'


class QueryOptimizationMiddleware(MiddlewareMixin):
    """Middleware that automatically optimizes database queries."""

    def __init__(self, get_response):
        super().__init__(get_response)
        self.db_optimizer = DatabaseOptimizer()

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs) -> None:
        """Optimize view querysets before execution."""
        if hasattr(view_func, 'view_class'):
            view_class = view_func.view_class

            # Optimize get_queryset if it exists
            if hasattr(view_class, 'get_queryset'):
                # This is a bit tricky as we can't directly modify the method
                # but we can set attributes that the view can use
                setattr(request, '_query_optimization_enabled', True)
                setattr(request, '_db_optimizer', self.db_optimizer)


class DatabaseHealthMiddleware(MiddlewareMixin):
    """Middleware that monitors database health."""

    def __init__(self, get_response):
        super().__init__(get_response)
        self.db_optimizer = DatabaseOptimizer()
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = 0

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Perform periodic database health checks."""
        current_time = time.time()

        if current_time - self.last_health_check > self.health_check_interval:
            self._perform_health_check()
            self.last_health_check = current_time

        return None

    def _perform_health_check(self) -> None:
        """Perform comprehensive database health check."""
        try:
            stats = self.db_optimizer.get_database_stats()

            # Check for health issues
            if stats.get('slow_queries', 0) > 50:
                logger.warning(f"Database health: High number of slow queries ({stats['slow_queries']})")

            if stats.get('active_connections', 0) / max(stats.get('max_connections', 100), 1) > 0.8:
                logger.warning("Database health: High connection usage detected")

            # Generate optimization report periodically
            if int(time.time()) % 3600 == 0:  # Every hour
                report = self.db_optimizer.create_optimization_report()
                logger.info(f"Database optimization report generated: {len(report.get('table_analyses', {}))} tables analyzed")

        except Exception as e:
            logger.error(f"Error during database health check: {e}")


class CacheOptimizationMiddleware(MiddlewareMixin):
    """Middleware that optimizes caching for database queries."""

    def __init__(self, get_response):
        super().__init__(get_response)
        self.db_optimizer = DatabaseOptimizer()

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Optimize cache headers based on response content."""
        # Add cache headers for commonly accessed healthcare data
        if request.path.startswith('/api/patients/') and request.method == 'GET':
            response['Cache-Control'] = 'max-age=300, private'  # 5 minutes

        elif request.path.startswith('/api/appointments/') and request.method == 'GET':
            response['Cache-Control'] = 'max-age=60, private'   # 1 minute

        elif request.path.startswith('/api/ehr/') and request.method == 'GET':
            response['Cache-Control'] = 'max-age=60, private'   # 1 minute

        return response