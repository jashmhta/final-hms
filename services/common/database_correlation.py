"""
Database correlation ID tracking utilities
Support for PostgreSQL, MySQL, and SQLite with query correlation
"""

import json
import logging
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .correlation_id import get_correlation_id, set_correlation_id
from .otel_config import get_tracer

logger = logging.getLogger(__name__)


class DatabaseCorrelationMixin:
    """Mixin to add correlation ID support to database operations"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._correlation_id = None

    def execute_with_correlation(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        """Execute query with correlation ID tracking"""
        # Get or generate correlation ID
        if not correlation_id:
            correlation_id = get_correlation_id() or str(uuid.uuid4())

        # Add correlation ID to params for logging
        if params is None:
            params = {}

        # Store correlation ID for later use
        self._correlation_id = correlation_id

        # Log query with correlation ID
        logger.info(
            "Executing database query",
            correlation_id=correlation_id,
            query=query[:200] + "..." if len(query) > 200 else query,
            params_type=type(params).__name__,
        )

        # Add correlation ID as comment for PostgreSQL
        if "postgresql" in str(type(self.cursor).lower()):
            query_with_correlation = f"/* correlation_id: {correlation_id} */ {query}"
        else:
            query_with_correlation = query

        # Execute query
        start_time = time.time()
        try:
            result = self.cursor.execute(query_with_correlation, params)
            duration = time.time() - start_time

            # Log successful execution
            logger.info(
                "Database query completed",
                correlation_id=correlation_id,
                duration_ms=duration * 1000,
                rows_affected=getattr(result, "rowcount", 0),
            )

            # Record metrics if OpenTelemetry is available
            tracer = get_tracer()
            if tracer:
                with tracer.start_as_current_span("database_execute") as span:
                    span.set_attribute("correlation.id", correlation_id)
                    span.set_attribute("db.statement", query[:200])
                    span.set_attribute("db.operation", self._extract_operation(query))
                    span.set_attribute("db.duration_ms", duration * 1000)

            return result

        except Exception as e:
            duration = time.time() - start_time

            # Log error with correlation ID
            logger.error(
                "Database query failed",
                correlation_id=correlation_id,
                error=str(e),
                duration_ms=duration * 1000,
            )

            # Record error in span if available
            tracer = get_tracer()
            if tracer:
                with tracer.start_as_current_span("database_error") as span:
                    span.set_attribute("correlation.id", correlation_id)
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    span.set_attribute("db.statement", query[:200])

            raise

    def _extract_operation(self, query: str) -> str:
        """Extract SQL operation from query"""
        query = query.strip().upper()
        if query.startswith(("SELECT", "INSERT", "UPDATE", "DELETE")):
            return query.split()[0]
        return "UNKNOWN"


class DjangoQuerySetCorrelation:
    """Django QuerySet mixin for correlation ID support"""

    @classmethod
    def inject_correlation(cls, queryset, correlation_id: Optional[str] = None):
        """Inject correlation ID into QuerySet"""
        if not correlation_id:
            correlation_id = get_correlation_id() or str(uuid.uuid4())

        # Store correlation ID on QuerySet
        queryset._correlation_id = correlation_id

        # Monkey patch query execution methods
        original_iter = queryset.__class__.__iter__
        original_count = queryset.__class__.count
        original_exists = queryset.__class__.exists
        original_first = queryset.__class__.first
        original_last = queryset.__class__.last

        def iter_with_correlation(self):
            correlation_id = (
                getattr(self, "_correlation_id", None) or get_correlation_id()
            )
            if correlation_id:
                logger.info(
                    "Executing QuerySet iteration", correlation_id=correlation_id
                )
                # Log the query
                query = str(self.query)
                logger.debug(
                    "QuerySet query", correlation_id=correlation_id, query=query
                )
            return original_iter(self)

        def count_with_correlation(self):
            correlation_id = (
                getattr(self, "_correlation_id", None) or get_correlation_id()
            )
            if correlation_id:
                logger.info("Executing QuerySet count", correlation_id=correlation_id)
            return original_count(self)

        def exists_with_correlation(self):
            correlation_id = (
                getattr(self, "_correlation_id", None) or get_correlation_id()
            )
            if correlation_id:
                logger.info("Executing QuerySet exists", correlation_id=correlation_id)
            return original_exists(self)

        def first_with_correlation(self):
            correlation_id = (
                getattr(self, "_correlation_id", None) or get_correlation_id()
            )
            if correlation_id:
                logger.info("Executing QuerySet first", correlation_id=correlation_id)
            return original_first(self)

        def last_with_correlation(self):
            correlation_id = (
                getattr(self, "_correlation_id", None) or get_correlation_id()
            )
            if correlation_id:
                logger.info("Executing QuerySet last", correlation_id=correlation_id)
            return original_last(self)

        # Apply monkey patches
        queryset.__class__.__iter__ = iter_with_correlation
        queryset.__class__.count = count_with_correlation
        queryset.__class__.exists = exists_with_correlation
        queryset.__class__.first = first_with_correlation
        queryset.__class__.last = last_with_correlation

        return queryset


class SQLAlchemyCorrelationExtension:
    """SQLAlchemy extension for correlation ID support"""

    def __init__(self, engine):
        self.engine = engine

    @contextmanager
    def connection_with_correlation(self, correlation_id: Optional[str] = None):
        """Get connection with correlation ID context"""
        if not correlation_id:
            correlation_id = get_correlation_id() or str(uuid.uuid4())

        # Store correlation ID in connection info
        conn = self.engine.connect()
        conn.info["correlation_id"] = correlation_id

        # Set correlation ID in context
        original_correlation = get_correlation_id()
        set_correlation_id(correlation_id)

        try:
            yield conn
        finally:
            # Restore original correlation ID
            if original_correlation:
                set_correlation_id(original_correlation)
            conn.close()


class DatabaseConnectionPool:
    """Database connection pool with correlation ID tracking"""

    def __init__(self, pool_size: int = 10, max_overflow: int = 20):
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.connections = {}
        self.active_connections = 0
        self.connection_stats = {}

    def get_connection(self, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Get connection with correlation ID"""
        if not correlation_id:
            correlation_id = get_correlation_id() or str(uuid.uuid4())

        # Check for available connection
        if (
            correlation_id in self.connections
            and self.connections[correlation_id]["available"]
        ):
            conn = self.connections[correlation_id]
            conn["available"] = False
            conn["last_used"] = time.time()
            conn["query_count"] = conn.get("query_count", 0) + 1
            return conn

        # Create new connection if under pool size
        if self.active_connections < self.pool_size:
            self.active_connections += 1
            conn = {
                "id": str(uuid.uuid4()),
                "correlation_id": correlation_id,
                "created_at": time.time(),
                "last_used": time.time(),
                "query_count": 0,
                "available": False,
                "connection": self._create_connection(),
            }
            self.connections[correlation_id] = conn
            return conn

        # Check for overflow
        if self.active_connections < self.pool_size + self.max_overflow:
            self.active_connections += 1
            correlation_id = f"overflow_{str(uuid.uuid4())}"
            conn = {
                "id": str(uuid.uuid4()),
                "correlation_id": correlation_id,
                "created_at": time.time(),
                "last_used": time.time(),
                "query_count": 0,
                "available": False,
                "overflow": True,
                "connection": self._create_connection(),
            }
            self.connections[correlation_id] = conn
            return conn

        # Wait for available connection
        raise Exception("Connection pool exhausted")

    def release_connection(self, correlation_id: str):
        """Release connection back to pool"""
        if correlation_id in self.connections:
            conn = self.connections[correlation_id]
            conn["available"] = True
            conn["last_used"] = time.time()

            # Log connection stats
            logger.info(
                "Released database connection",
                correlation_id=correlation_id,
                query_count=conn["query_count"],
                duration_ms=(time.time() - conn["created_at"]) * 1000,
            )

    def _create_connection(self):
        """Create actual database connection"""
        # This would be implemented with actual database driver
        return {"connection": "database_connection_object"}


class QueryCorrelationLogger:
    """Log all database queries with correlation IDs"""

    def __init__(
        self,
        log_queries: bool = True,
        log_slow_queries: bool = True,
        slow_threshold: float = 0.1,
    ):
        self.log_queries = log_queries
        self.log_slow_queries = log_slow_queries
        self.slow_threshold = slow_threshold
        self.query_stats = {}

    def log_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        duration: Optional[float] = None,
        success: bool = True,
    ):
        """Log query execution with correlation ID"""
        if not correlation_id:
            correlation_id = get_correlation_id() or str(uuid.uuid4())

        # Prepare log data
        log_data = {
            "correlation_id": correlation_id,
            "query": query[:500] + "..." if len(query) > 500 else query,
            "params": params,
            "duration_ms": duration * 1000 if duration else None,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Log based on configuration
        if self.log_queries:
            if success:
                logger.info("Database query executed", **log_data)
            else:
                logger.error("Database query failed", **log_data)

        # Log slow queries separately
        if self.log_slow_queries and duration and duration > self.slow_threshold:
            logger.warning(
                "Slow database query detected",
                correlation_id=correlation_id,
                query=query[:200],
                duration_ms=duration * 1000,
                threshold_ms=self.slow_threshold * 1000,
            )

        # Update query statistics
        self._update_query_stats(query, duration, success)

    def _update_query_stats(self, query: str, duration: Optional[float], success: bool):
        """Update query execution statistics"""
        query_hash = hash(query)

        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                "query": query,
                "count": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "success_count": 0,
                "failure_count": 0,
            }

        stats = self.query_stats[query_hash]
        stats["count"] += 1

        if duration:
            stats["total_duration"] += duration
            stats["avg_duration"] = stats["total_duration"] / stats["count"]

        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1

    def get_query_stats(self) -> Dict[str, Any]:
        """Get query execution statistics"""
        return {
            "total_queries": sum(stats["count"] for stats in self.query_stats.values()),
            "queries_by_frequency": sorted(
                self.query_stats.values(), key=lambda x: x["count"], reverse=True
            )[:10],
            "slowest_queries": sorted(
                self.query_stats.values(), key=lambda x: x["avg_duration"], reverse=True
            )[:10],
            "error_rate": sum(
                stats["failure_count"] for stats in self.query_stats.values()
            )
            / max(sum(stats["count"] for stats in self.query_stats.values()), 1),
        }


# Database middleware for Django
class DatabaseCorrelationMiddleware:
    """Django middleware for database correlation ID tracking"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.query_logger = QueryCorrelationLogger()

    def __call__(self, request):
        # Get correlation ID from request
        correlation_id = (
            getattr(request, "correlation_id", None) or get_correlation_id()
        )

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Set correlation ID for database operations
        set_correlation_id(correlation_id)

        # Monkey patch django.db connection
        from django.db import connection

        original_execute = connection.cursor

        def execute_with_correlation():
            cursor = original_execute()
            original_execute_wrapper = cursor.execute

            def execute_wrapper(query, params=None):
                start_time = time.time()
                try:
                    result = original_execute_wrapper(query, params)
                    duration = time.time() - start_time
                    self.query_logger.log_query(
                        query, params, correlation_id, duration, True
                    )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.query_logger.log_query(
                        query, params, correlation_id, duration, False
                    )
                    raise

            cursor.execute = execute_wrapper
            return cursor

        connection.cursor = execute_with_correlation

        # Process request
        response = self.get_response(request)

        # Log database stats for request
        stats = self.query_logger.get_query_stats()
        logger.info(
            "Request database statistics",
            correlation_id=correlation_id,
            path=request.path,
            **stats,
        )

        return response


# Context manager for database operations
@contextmanager
def database_operation_context(
    operation_name: str, correlation_id: Optional[str] = None, log_params: bool = False
):
    """Context manager for database operations with correlation ID"""
    if not correlation_id:
        correlation_id = get_correlation_id() or str(uuid.uuid4())

    # Set correlation ID in context
    original_correlation = get_correlation_id()
    set_correlation_id(correlation_id)

    logger.info(
        "Starting database operation",
        correlation_id=correlation_id,
        operation=operation_name,
    )

    start_time = time.time()
    query_count = 0

    try:
        yield {"correlation_id": correlation_id, "operation_name": operation_name}

    except Exception as e:
        duration = time.time() - start_time

        logger.error(
            "Database operation failed",
            correlation_id=correlation_id,
            operation=operation_name,
            error=str(e),
            duration_ms=duration * 1000,
            query_count=query_count,
        )

        # Record in OpenTelemetry if available
        tracer = get_tracer()
        if tracer:
            with tracer.start_as_current_span("database_operation_error") as span:
                span.set_attribute("correlation.id", correlation_id)
                span.set_attribute("operation.name", operation_name)
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                span.set_attribute("duration_ms", duration * 1000)

        raise

    finally:
        duration = time.time() - start_time

        # Restore original correlation ID
        if original_correlation:
            set_correlation_id(original_correlation)

        logger.info(
            "Database operation completed",
            correlation_id=correlation_id,
            operation=operation_name,
            duration_ms=duration * 1000,
            query_count=query_count,
        )


# Decorator for database functions
def with_database_correlation(func):
    """Decorator to add correlation ID to database functions"""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract correlation ID from kwargs or generate new one
        correlation_id = kwargs.pop("correlation_id", None)
        if not correlation_id:
            correlation_id = get_correlation_id() or str(uuid.uuid4())

        # Execute with correlation context
        with database_operation_context(func.__name__, correlation_id):
            # Add correlation ID to kwargs
            kwargs["correlation_id"] = correlation_id

            # Execute function
            return func(*args, **kwargs)

    return wrapper


# PostgreSQL specific correlation ID functions
def postgresql_setup_correlation(connection):
    """Setup PostgreSQL functions for correlation ID tracking"""
    # Create function to get current correlation ID
    setup_query = """
    CREATE OR REPLACE FUNCTION get_correlation_id()
    RETURNS TEXT AS $$
    BEGIN
        -- This would be set by the application
        RETURN current_setting('app.correlation_id', true);
    EXCEPTION WHEN undefined_object THEN
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    """

    # Create trigger function to log operations
    trigger_query = """
    CREATE OR REPLACE FUNCTION log_operation_with_correlation()
    RETURNS TRIGGER AS $$
    DECLARE
        correlation_id TEXT;
    BEGIN
        -- Get correlation ID
        SELECT INTO correlation_id get_correlation_id();

        -- Log operation with correlation ID
        INSERT INTO operation_log (table_name, operation_type, row_id, correlation_id, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.id, correlation_id, NOW());

        RETURN COALESCE(NEW, OLD);
    END;
    $$ LANGUAGE plpgsql;
    """

    with connection.cursor() as cursor:
        cursor.execute(setup_query)
        cursor.execute(trigger_query)
