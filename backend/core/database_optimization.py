"""
database_optimization module
"""

import asyncio
import logging
import os
import threading
import time
import weakref
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import redis
from rest_framework import serializers

from django.conf import settings
from django.core.cache import cache
from django.db import connections, models, transaction
from django.db.backends.postgresql.base import DatabaseWrapper
from django.db.models import QuerySet
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone


class DatabaseOptimizationLevel(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"


class DatabaseStrategy(Enum):
    SINGLE_INSTANCE = "single_instance"
    READ_REPLICAS = "read_replicas"
    SHARDING = "sharding"
    MULTI_TENANT = "multi_tenant"
    HYBRID = "hybrid"


class QueryPattern(Enum):
    N_PLUS_ONE = "n_plus_one"
    CARTESIAN_PRODUCT = "cartesian_product"
    MISSING_INDEX = "missing_index"
    INEFFICIENT_JOIN = "inefficient_join"
    LARGE_RESULT_SET = "large_result_set"
    SLOW_QUERY = "slow_query"
    UNBOUNDED_QUERY = "unbounded_query"
    SEQUENTIAL_SCAN = "sequential_scan"


class CacheStrategy(Enum):
    NONE = "none"
    SIMPLE = "simple"
    QUERYSET = "queryset"
    HEALTHCARE_AWARE = "healthcare_aware"
    INTELLIGENT = "intelligent"


@dataclass
class QueryAnalysisResult:
    query_text: str
    execution_time_ms: float
    rows_returned: int
    table_name: str
    pattern_detected: QueryPattern
    severity: str  # "low", "medium", "high", "critical"
    recommendation: str
    estimated_impact: str
    detected_at: datetime = field(default_factory=timezone.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexRecommendation:
    table_name: str
    column_name: str
    index_type: str  # "btree", "hash", "gin", "gist"
    estimated_benefit: float  # 0.0 to 1.0
    current_queries_affected: int
    recommendation_reason: str
    priority: str  # "low", "medium", "high", "critical"


@dataclass
class DatabaseMetrics:
    query_time_ms: float
    rows_affected: int
    connection_time_ms: float
    cache_hit_rate: float
    index_usage: float
    memory_usage_mb: float
    disk_usage_mb: float
    active_connections: int
    max_connections: int
    slow_query_count: int
    total_query_count: int
    avg_query_time_ms: float = 0.0
    health_score: float = 100.0
    n_plus_one_count: int = 0
    cache_efficiency: float = 0.0


class DatabaseOptimizer:
    """Enterprise-grade database optimization with cross-database compatibility."""

    _instances = weakref.WeakSet()

    def __new__(cls, *args, **kwargs):
        # Singleton pattern with weak references to prevent memory leaks
        instance = super().__new__(cls)
        cls._instances.add(instance)
        return instance

    def __init__(
        self,
        optimization_level: DatabaseOptimizationLevel = DatabaseOptimizationLevel.ENTERPRISE,
    ):
        self.optimization_level = optimization_level
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.connection_pool = {}
        self.query_cache = {}
        self.index_stats = {}
        self.query_patterns = defaultdict(list)
        self.slow_queries = []
        self.index_recommendations = []
        self.is_postgres = self._detect_database_backend()
        self._connection_lock = threading.RLock()
        self._cache_lock = threading.RLock()
        self._redis_connection_count = 0
        self._max_cache_size = 10000  # Prevent unbounded cache growth
        self._query_analysis_enabled = (
            os.getenv("QUERY_ANALYSIS_ENABLED", "true").lower() == "true"
        )
        self._healthcare_optimization_enabled = (
            os.getenv("HEALTHCARE_OPTIMIZATION_ENABLED", "true").lower() == "true"
        )
        self._n_plus_one_threshold = int(os.getenv("N_PLUS_ONE_THRESHOLD", "5"))
        self._slow_query_threshold_ms = int(
            os.getenv("SLOW_QUERY_THRESHOLD_MS", "1000")
        )
        self._large_result_threshold = int(os.getenv("LARGE_RESULT_THRESHOLD", "1000"))

        if os.getenv("REDIS_URL"):
            try:
                self.redis_client = redis.ConnectionPool.from_url(
                    os.getenv("REDIS_URL"), decode_responses=True, max_connections=10
                )
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None

    def _detect_database_backend(self) -> bool:
        """Detect if using PostgreSQL backend."""
        try:
            db_config = settings.DATABASES["default"]
            return "postgresql" in db_config["ENGINE"]
        except (KeyError, AttributeError):
            return False

    def get_database_backend(self) -> str:
        """Get the current database backend name."""
        if self.is_postgres:
            return "PostgreSQL"
        else:
            return "SQLite"

    @contextmanager
    def get_database_connection(self, db_alias: str = "default"):
        """Context manager for database connections with automatic cleanup."""
        with self._connection_lock:
            connection = connections[db_alias]
            try:
                yield connection
            finally:
                # Ensure connection is returned to pool
                if hasattr(connection, "close") and not connection.connection:
                    connection.close()

    def _get_redis_connection(self):
        """Get Redis connection with proper connection management."""
        if not self.redis_client:
            return None

        try:
            return redis.Redis(connection_pool=self.redis_client)
        except Exception as e:
            self.logger.error(f"Redis connection error: {e}")
            return None

    def _cleanup_cache(self):
        """Prevent cache from growing unbounded."""
        with self._cache_lock:
            if len(self.query_cache) > self._max_cache_size:
                # Remove oldest 20% of entries
                items_to_remove = int(self._max_cache_size * 0.2)
                oldest_keys = sorted(self.query_cache.keys())[:items_to_remove]
                for key in oldest_keys:
                    del self.query_cache[key]
                self.logger.info(f"Cleaned up {items_to_remove} old cache entries")

    def analyze_n_plus_one_patterns(
        self, queryset: QuerySet
    ) -> List[QueryAnalysisResult]:
        """Analyze queryset for N+1 query patterns."""
        results = []

        if not self._query_analysis_enabled:
            return results

        # Get the query and analyze it
        query = str(queryset.query)
        table_name = queryset.model._meta.db_table

        # Detect common N+1 patterns
        if "SELECT" in query and queryset.count() > self._n_plus_one_threshold:
            # Check for missing select_related/prefetch_related
            has_joins = "JOIN" in query.upper()
            has_many_relationships = any(
                field.many_to_many or field.one_to_many
                for field in queryset.model._meta.get_fields()
                if hasattr(field, "many_to_many")
            )

            if has_many_relationships and not has_joins:
                results.append(
                    QueryAnalysisResult(
                        query_text=query,
                        execution_time_ms=0,
                        rows_returned=queryset.count(),
                        table_name=table_name,
                        pattern_detected=QueryPattern.N_PLUS_ONE,
                        severity="high",
                        recommendation="Add select_related() or prefetch_related() to avoid N+1 queries",
                        estimated_impact="High - significant performance improvement expected",
                        context={
                            "model": queryset.model.__name__,
                            "count": queryset.count(),
                        },
                    )
                )

        return results

    def optimize_queryset(
        self, queryset: QuerySet, use_healthcare_optimization: bool = True
    ) -> QuerySet:
        """Automatically optimize queryset based on analysis."""
        if not self._query_analysis_enabled:
            return queryset

        model = queryset.model

        # Get all foreign key and many-to-many relationships
        select_fields = []
        prefetch_fields = []

        for field in model._meta.get_fields():
            if field.is_relation and field.concrete:
                if field.many_to_one or field.one_to_one:
                    select_fields.append(field.name)
                elif field.one_to_many or field.many_to_many:
                    prefetch_fields.append(field.name)

        # Apply healthcare-specific optimizations
        if use_healthcare_optimization and self._healthcare_optimization_enabled:
            # Common healthcare fields that should be optimized
            healthcare_fields = [
                "hospital",
                "patient",
                "doctor",
                "encounter",
                "appointment",
            ]
            for field in healthcare_fields:
                if hasattr(model, field) and field not in select_fields:
                    select_fields.append(field)

        # Apply optimizations
        if select_fields:
            queryset = queryset.select_related(*select_fields)
        if prefetch_fields:
            queryset = queryset.prefetch_related(*prefetch_fields)

        return queryset

    def analyze_serializer_performance(
        self, serializer_class
    ) -> List[QueryAnalysisResult]:
        """Analyze Django REST Framework serializer for N+1 query patterns."""
        results = []

        if not hasattr(serializer_class, "Meta") or not hasattr(
            serializer_class.Meta, "model"
        ):
            return results

        model = serializer_class.Meta.model

        # Check for nested serializers that might cause N+1 queries
        for field_name, field in serializer_class._declared_fields.items():
            if isinstance(field, serializers.ModelSerializer):
                if (
                    hasattr(field.Meta, "model")
                    and hasattr(field.Meta, "many")
                    and field.many
                ):
                    # This is a nested serializer with many=True - potential N+1
                    results.append(
                        QueryAnalysisResult(
                            query_text=f"Serializer: {serializer_class.__name__}.{field_name}",
                            execution_time_ms=0,
                            rows_returned=0,
                            table_name=model._meta.db_table,
                            pattern_detected=QueryPattern.N_PLUS_ONE,
                            severity="high",
                            recommendation=f"Add prefetch_related for '{field_name}' in view",
                            estimated_impact="High - eliminates N+1 queries in API responses",
                            context={
                                "serializer": serializer_class.__name__,
                                "field": field_name,
                                "nested_model": field.Meta.model.__name__,
                            },
                        )
                    )

        return results

    def get_healthcare_query_optimizations(self) -> Dict[str, Any]:
        """Get healthcare-specific query optimization strategies."""
        return {
            "patient_query_patterns": {
                "common_filters": ["hospital", "status", "date_of_birth"],
                "recommended_indexes": [
                    "(hospital_id, status, created_at)",
                    "(hospital_id, last_name, first_name)",
                    "(hospital_id, date_of_birth)",
                    "(medical_record_number)",
                    "(uuid)",
                ],
                "cache_strategies": {
                    "patient_demographics": "1_hour",
                    "patient_medical_history": "5_minutes",
                    "patient_active_medications": "30_minutes",
                },
            },
            "appointment_query_patterns": {
                "common_filters": ["hospital", "doctor", "patient", "date", "status"],
                "recommended_indexes": [
                    "(hospital_id, doctor_id, appointment_date)",
                    "(hospital_id, patient_id, appointment_date)",
                    "(hospital_id, status, appointment_date)",
                    "(appointment_number)",
                ],
                "cache_strategies": {
                    "today_appointments": "5_minutes",
                    "doctor_schedule": "15_minutes",
                    "patient_upcoming": "30_minutes",
                },
            },
            "ehr_query_patterns": {
                "common_filters": ["hospital", "patient", "encounter_type", "date"],
                "recommended_indexes": [
                    "(hospital_id, patient_id, encounter_date)",
                    "(hospital_id, encounter_type, created_at)",
                    "(hospital_id, doctor_id, created_at)",
                ],
                "cache_strategies": {
                    "active_encounters": "5_minutes",
                    "patient_history": "1_hour",
                    "recent_vitals": "15_minutes",
                },
            },
        }

    def recommend_healthcare_indexes(self) -> List[IndexRecommendation]:
        """Generate healthcare-specific index recommendations."""
        recommendations = []

        try:
            with self.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    if self.is_postgres:
                        # Check for missing healthcare-related indexes
                        healthcare_tables = [
                            "patients_patient",
                            "appointments_appointment",
                            "ehr_encounter",
                            "pharmacy_prescription",
                            "lab_laborder",
                        ]

                        for table in healthcare_tables:
                            # Check if table exists
                            cursor.execute(
                                """
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables
                                    WHERE table_name = %s
                                )
                            """,
                                (table,),
                            )

                            if cursor.fetchone()[0]:
                                # Analyze table for missing indexes
                                cursor.execute(
                                    f"""
                                    SELECT
                                        schemaname,
                                        tablename,
                                        indexname,
                                        indexdef
                                    FROM pg_indexes
                                    WHERE tablename = %s
                                """,
                                    (table,),
                                )

                                existing_indexes = [row[2] for row in cursor.fetchall()]

                                # Recommend common healthcare indexes
                                if (
                                    table == "patients_patient"
                                    and "patients_patient_hospital_idx"
                                    not in existing_indexes
                                ):
                                    recommendations.append(
                                        IndexRecommendation(
                                            table_name=table,
                                            column_name="hospital_id",
                                            index_type="btree",
                                            estimated_benefit=0.9,
                                            current_queries_affected=self._estimate_queries_affected(
                                                table, "hospital_id"
                                            ),
                                            recommendation_reason="Critical for multi-tenant healthcare system",
                                            priority="critical",
                                        )
                                    )

        except Exception as e:
            self.logger.error(f"Error generating healthcare index recommendations: {e}")

        return recommendations

    def _estimate_queries_affected(self, table_name: str, column_name: str) -> int:
        """Estimate number of queries affected by an index."""
        try:
            with self.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    if self.is_postgres:
                        cursor.execute(
                            f"""
                            SELECT SUM(seq_scan)
                            FROM pg_stat_user_tables
                            WHERE relname = %s
                        """,
                            (table_name,),
                        )
                        result = cursor.fetchone()
                        return result[0] if result[0] else 0
        except Exception:
            pass
        return 0

    def get_query_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive query performance report."""
        report = {
            "timestamp": timezone.now().isoformat(),
            "backend": self.get_database_backend(),
            "query_patterns": dict(self.query_patterns),
            "slow_queries_count": len(self.slow_queries),
            "n_plus_one_count": sum(
                len(patterns)
                for patterns in self.query_patterns.values()
                if any(p.pattern_detected == QueryPattern.N_PLUS_ONE for p in patterns)
            ),
            "index_recommendations": len(self.index_recommendations),
            "health_score": self._calculate_health_score(),
            "optimization_suggestions": [],
        }

        # Generate optimization suggestions
        if report["n_plus_one_count"] > 0:
            report["optimization_suggestions"].append(
                f"Found {report['n_plus_one_count']} N+1 query patterns - optimize serializers and views"
            )

        if report["slow_queries_count"] > 10:
            report["optimization_suggestions"].append(
                f"High number of slow queries ({report['slow_queries_count']}) - review query optimization"
            )

        if report["index_recommendations"] > 5:
            report["optimization_suggestions"].append(
                f"Multiple index recommendations ({report['index_recommendations']}) - consider adding missing indexes"
            )

        return report

    def _calculate_health_score(self) -> float:
        """Calculate overall database health score."""
        score = 100.0

        # Deduct points for N+1 queries
        n_plus_one_count = sum(
            len(patterns)
            for patterns in self.query_patterns.values()
            if any(p.pattern_detected == QueryPattern.N_PLUS_ONE for p in patterns)
        )
        score -= min(n_plus_one_count * 5, 30)  # Max 30 point deduction

        # Deduct points for slow queries
        score -= min(len(self.slow_queries) * 2, 20)  # Max 20 point deduction

        # Deduct points for missing indexes
        score -= min(len(self.index_recommendations) * 3, 25)  # Max 25 point deduction

        return max(score, 0.0)

    def __del__(self):
        """Cleanup resources when object is destroyed."""
        try:
            if self.redis_client:
                self.redis_client.disconnect()
            self.connection_pool.clear()
            self.query_cache.clear()
            self.query_patterns.clear()
            self.slow_queries.clear()
        except:
            pass  # Ignore errors during cleanup

    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics - cross-database compatible."""
        stats = {
            "backend": self.get_database_backend(),
            "database_name": settings.DATABASES["default"].get("NAME", "unknown"),
            "tables": 0,
            "total_indexes": 0,
            "database_size_mb": 0,
            "active_connections": 0,
            "max_connections": 100,  # Default for SQLite
            "slow_queries": 0,
            "total_queries": 0,
        }

        try:
            with self.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    if self.is_postgres:
                        # PostgreSQL specific queries
                        cursor.execute(
                            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                        )
                        stats["tables"] = cursor.fetchone()[0]

                        cursor.execute(
                            "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'"
                        )
                        stats["total_indexes"] = cursor.fetchone()[0]

                        cursor.execute("SELECT pg_database_size(current_database())")
                        stats["database_size_mb"] = cursor.fetchone()[0] / (1024 * 1024)

                        cursor.execute(
                            "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'"
                        )
                        stats["active_connections"] = cursor.fetchone()[0]

                        cursor.execute("SHOW max_connections")
                        stats["max_connections"] = int(cursor.fetchone()[0])

                        cursor.execute(
                            "SELECT COUNT(*) FROM pg_stat_statements WHERE total_time > 1000"
                        )
                        stats["slow_queries"] = cursor.fetchone()[0]

                        cursor.execute("SELECT SUM(calls) FROM pg_stat_statements")
                        result = cursor.fetchone()
                        stats["total_queries"] = result[0] if result[0] else 0
                    else:
                        # SQLite specific queries
                        cursor.execute(
                            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                        )
                        stats["tables"] = cursor.fetchone()[0]

                        cursor.execute(
                            "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
                        )
                        stats["total_indexes"] = cursor.fetchone()[0]

                        # Get database file size for SQLite
                        db_path = settings.DATABASES["default"]["NAME"]
                        if os.path.exists(db_path):
                            stats["database_size_mb"] = os.path.getsize(db_path) / (
                                1024 * 1024
                            )

                        # SQLite doesn't have connection limits or query stats
                        stats["active_connections"] = 1
                        stats["slow_queries"] = 0
                        stats["total_queries"] = 0

        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")

        return stats

    def analyze_table_performance(self, table_name: str) -> Dict[str, Any]:
        """Analyze performance metrics for a specific table."""
        analysis = {
            "table_name": table_name,
            "row_count": 0,
            "table_size_mb": 0,
            "indexes": [],
            "slow_queries": 0,
            "avg_query_time_ms": 0,
            "recommendations": [],
        }

        try:
            with self.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    if self.is_postgres:
                        # PostgreSQL table analysis
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        analysis["row_count"] = cursor.fetchone()[0]

                        cursor.execute(
                            f"""
                            SELECT
                                pg_total_relation_size('{table_name}') as size,
                                pg_indexes_size('{table_name}') as index_size
                        """
                        )
                        result = cursor.fetchone()
                        if result:
                            analysis["table_size_mb"] = result[0] / (1024 * 1024)

                        cursor.execute(
                            f"""
                            SELECT indexname, indexdef
                            FROM pg_indexes
                            WHERE tablename = %s
                        """,
                            (table_name,),
                        )
                        analysis["indexes"] = cursor.fetchall()

                        # Check for slow queries on this table
                        cursor.execute(
                            f"""
                            SELECT COUNT(*)
                            FROM pg_stat_statements
                            WHERE query LIKE '%{table_name}%'
                            AND total_time > 1000
                        """
                        )
                        analysis["slow_queries"] = cursor.fetchone()[0]

                    else:
                        # SQLite table analysis
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        analysis["row_count"] = cursor.fetchone()[0]

                        # Get indexes for SQLite
                        cursor.execute(
                            f"""
                            SELECT name, sql
                            FROM sqlite_master
                            WHERE type='index'
                            AND tbl_name='{table_name}'
                        """
                        )
                        analysis["indexes"] = cursor.fetchall()

                        # SQLite doesn't have detailed performance stats
                        analysis["slow_queries"] = 0
                        analysis["avg_query_time_ms"] = 0

            # Generate recommendations
            analysis["recommendations"] = self._generate_table_recommendations(analysis)

        except Exception as e:
            self.logger.error(f"Error analyzing table {table_name}: {e}")
            analysis["error"] = str(e)

        return analysis

    def _generate_table_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations for a table."""
        recommendations = []

        if analysis["row_count"] > 100000 and len(analysis["indexes"]) < 3:
            recommendations.append("Consider adding more indexes for large tables")

        if analysis["table_size_mb"] > 1000:
            recommendations.append("Consider table partitioning for very large tables")

        if analysis["slow_queries"] > 10:
            recommendations.append(
                "High number of slow queries detected - review query optimization"
            )

        if not analysis["indexes"]:
            recommendations.append(
                "No indexes found - consider adding primary key and commonly queried columns"
            )

        return recommendations

    def optimize_database(self, dry_run: bool = True) -> Dict[str, Any]:
        """Run comprehensive database optimization."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "backend": self.get_database_backend(),
            "tables_optimized": 0,
            "indexes_created": 0,
            "indexes_dropped": 0,
            "space_reclaimed_mb": 0,
            "performance_improvement": 0,
            "actions": [],
            "recommendations": [],
        }

        try:
            with self.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    if self.is_postgres:
                        # PostgreSQL optimization
                        if not dry_run:
                            cursor.execute("VACUUM ANALYZE")
                            results["actions"].append("VACUUM ANALYZE executed")

                            cursor.execute("REINDEX DATABASE")
                            results["actions"].append("REINDEX DATABASE executed")

                        # Update statistics
                        cursor.execute("ANALYZE")
                        results["actions"].append("Statistics updated")

                    else:
                        # SQLite optimization
                        if not dry_run:
                            cursor.execute("VACUUM")
                            results["actions"].append("VACUUM executed")

                        cursor.execute("ANALYZE")
                        results["actions"].append("Statistics updated")

            # Get optimization results
            stats_after = self.get_database_stats()
            results["final_stats"] = stats_after

        except Exception as e:
            self.logger.error(f"Error during database optimization: {e}")
            results["error"] = str(e)

        return results

    def create_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive database optimization report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "backend": self.get_database_backend(),
            "database_stats": self.get_database_stats(),
            "table_analyses": {},
            "optimization_level": self.optimization_level.value,
            "recommendations": [],
        }

        # Get list of tables
        try:
            with self.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    if self.is_postgres:
                        cursor.execute(
                            """
                            SELECT tablename
                            FROM pg_tables
                            WHERE schemaname = 'public'
                            ORDER BY tablename
                        """
                        )
                    else:
                        cursor.execute(
                            """
                            SELECT name
                            FROM sqlite_master
                            WHERE type='table'
                            AND name NOT LIKE 'sqlite_%'
                            ORDER BY name
                        """
                        )

                    tables = [row[0] for row in cursor.fetchall()]

                    # Analyze each table (limit to first 10 for performance)
                    for table in tables[:10]:
                        report["table_analyses"][table] = (
                            self.analyze_table_performance(table)
                        )

        except Exception as e:
            self.logger.error(f"Error generating optimization report: {e}")
            report["error"] = str(e)

        # Generate overall recommendations
        report["recommendations"] = self._generate_overall_recommendations(report)

        return report

    def _generate_overall_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate overall database optimization recommendations."""
        recommendations = []

        stats = report.get("database_stats", {})

        if stats.get("slow_queries", 0) > 50:
            recommendations.append(
                "High number of slow queries - consider query optimization and indexing"
            )

        if stats.get("database_size_mb", 0) > 10000:
            recommendations.append(
                "Large database size - consider archiving old data or partitioning"
            )

        if (
            stats.get("active_connections", 0)
            / max(stats.get("max_connections", 100), 1)
            > 0.8
        ):
            recommendations.append(
                "High connection usage - consider connection pooling optimization"
            )

        if self.optimization_level == DatabaseOptimizationLevel.ENTERPRISE:
            recommendations.extend(
                [
                    "Consider implementing read replicas for better performance",
                    "Implement regular database maintenance schedule",
                    "Consider upgrading to PostgreSQL for enterprise features",
                ]
            )

        return recommendations


# Singleton instance for easy access
database_optimizer = DatabaseOptimizer()
