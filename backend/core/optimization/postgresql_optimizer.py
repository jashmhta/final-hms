"""
PostgreSQL Performance Optimization Utilities
Advanced indexing, query optimization, and configuration tuning
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db import connection, connections, transaction

logger = logging.getLogger(__name__)


class PostgresOptimizer:
    """PostgreSQL performance optimization utilities"""

    def __init__(self):
        self.connection = connections["default"]

    def analyze_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Analyze existing indexes on a table"""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    indexname as name,
                    indexdef as definition,
                    pg_size_pretty(pg_relation_size(indexname::text)) as size,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_indexes
                LEFT JOIN pg_stat_user_indexes ON
                    pg_indexes.indexname = pg_stat_user_indexes.indexrelname
                WHERE tablename = %s
                ORDER BY pg_relation_size(indexname::text) DESC;
            """,
                [table_name],
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def suggest_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Suggest optimal indexes based on query patterns"""
        suggestions = []

        # Get slow queries for this table
        slow_queries = self.get_slow_queries(table_name)

        # Analyze WHERE clause patterns
        for query in slow_queries[:10]:  # Top 10 slow queries
            conditions = self.extract_where_conditions(query["query"])
            for condition in conditions:
                suggestion = {
                    "table": table_name,
                    "fields": condition["fields"],
                    "type": self.determine_index_type(condition["fields"]),
                    "reason": f"Slow query (avg {query['mean_time']:.3f}ms) with condition: {condition['raw']}",
                    "estimated_gain": self.estimate_performance_gain(query["mean_time"]),
                }
                suggestions.append(suggestion)

        # Get foreign key relationships
        fk_suggestions = self.get_foreign_key_suggestions(table_name)
        suggestions.extend(fk_suggestions)

        return suggestions

    def get_slow_queries(self, table_name: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get slow queries from PostgreSQL statistics"""
        with self.connection.cursor() as cursor:
            query = """
                SELECT
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    rows,
                    100.0 * shared_blks_hit /
                           nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements
                WHERE query LIKE %s
                ORDER BY mean_exec_time DESC
                LIMIT %s;
            """
            like_pattern = f"%{table_name}%" if table_name else "%"
            cursor.execute(query, [like_pattern, limit])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def extract_where_conditions(self, query: str) -> List[Dict[str, Any]]:
        """Extract WHERE clause conditions from SQL query"""
        # This is a simplified version - in production, use a SQL parser
        conditions = []
        query_lower = query.lower()

        # Simple pattern matching for common conditions
        if " where " in query_lower:
            where_part = query_lower.split(" where ")[1].split(" group by ")[0].split(" order by ")[0]

            # Look for equality conditions
            import re

            equality_matches = re.findall(r'(\w+)\s*=\s*[\'"]?([^\'"\s]+)[\'"]?', where_part)
            for match in equality_matches:
                conditions.append({"fields": [match[0]], "type": "equality", "raw": f"{match[0]} = {match[1]}"})

        return conditions

    def determine_index_type(self, fields: List[str]) -> str:
        """Determine optimal index type"""
        if len(fields) == 1:
            return "btree"
        elif len(fields) <= 5:
            return "composite"
        else:
            return "gin"  # For complex multi-column queries

    def estimate_performance_gain(self, current_time: float) -> str:
        """Estimate potential performance improvement"""
        if current_time > 1000:  # > 1 second
            return "90-95%"
        elif current_time > 500:  # > 500ms
            return "70-85%"
        elif current_time > 100:  # > 100ms
            return "50-70%"
        else:
            return "20-40%"

    def get_foreign_key_suggestions(self, table_name: str) -> List[Dict[str, Any]]:
        """Suggest indexes for foreign key columns"""
        suggestions = []

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM
                    information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
            """,
                [table_name],
            )

            for row in cursor.fetchall():
                suggestions.append(
                    {
                        "table": table_name,
                        "fields": [row[1]],
                        "type": "btree",
                        "reason": f"Foreign key to {row[2]}.{row[3]}",
                        "estimated_gain": "80-90%",
                    }
                )

        return suggestions

    def create_index(
        self, table_name: str, fields: List[str], index_type: str = "btree", name: str = None, concurrently: bool = True
    ) -> bool:
        """Create an index with specified parameters"""
        if not name:
            field_str = "_".join(fields)
            name = f"idx_{table_name}_{field_str}"

        try:
            with self.connection.cursor() as cursor:
                if concurrently:
                    cursor.execute(
                        f"""
                        CREATE INDEX CONCURRENTLY {name}
                        ON {table_name} USING {index_type} ({', '.join(fields)})
                    """
                    )
                else:
                    cursor.execute(
                        f"""
                        CREATE INDEX {name}
                        ON {table_name} USING {index_type} ({', '.join(fields)})
                    """
                    )

                logger.info(f"Created index {name} on {table_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create index {name}: {e}")
            return False

    def analyze_table(self, table_name: str) -> bool:
        """Run ANALYZE on a table to update statistics"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"ANALYZE {table_name}")
                logger.info(f"Analyzed table {table_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to analyze table {table_name}: {e}")
            return False

    def vacuum_table(self, table_name: str, full: bool = False) -> bool:
        """Run VACUUM on a table to reclaim space"""
        try:
            with self.connection.cursor() as cursor:
                if full:
                    cursor.execute(f"VACUUM FULL {table_name}")
                else:
                    cursor.execute(f"VACUUM {table_name}")
                logger.info(f"Vacuumed table {table_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to vacuum table {table_name}: {e}")
            return False

    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get comprehensive table statistics"""
        with self.connection.cursor() as cursor:
            # Basic stats
            cursor.execute(
                """
                SELECT
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats
                WHERE tablename = %s
                ORDER BY schemaname, tablename, attname;
            """,
                [table_name],
            )
            columns = [col[0] for col in cursor.description]
            column_stats = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Size info
            cursor.execute(
                """
                SELECT
                    pg_size_pretty(pg_total_relation_size(%s)) as total_size,
                    pg_size_pretty(pg_relation_size(%s)) as table_size,
                    pg_size_pretty(pg_indexes_size(%s)) as indexes_size,
                    pg_total_relation_size(%s) as total_size_bytes
            """,
                [table_name, table_name, table_name, table_name],
            )
            size_info = dict(zip(["total_size", "table_size", "indexes_size", "total_size_bytes"], cursor.fetchone()))

            # Row count estimate
            cursor.execute(
                f"""
                SELECT reltuples::bigint AS estimate
                FROM pg_class
                WHERE relname = %s;
            """,
                [table_name],
            )
            row_count = cursor.fetchone()[0]

            return {
                "table_name": table_name,
                "row_estimate": row_count,
                "size_info": size_info,
                "column_stats": column_stats,
                "indexes": self.analyze_indexes(table_name),
            }

    def optimize_configuration(self) -> Dict[str, Any]:
        """Get PostgreSQL configuration optimization recommendations"""
        recommendations = []

        with self.connection.cursor() as cursor:
            # Check key performance settings
            settings_to_check = [
                ("shared_buffers", "25% of RAM"),
                ("work_mem", "4-64MB per connection"),
                ("maintenance_work_mem", "256MB-1GB"),
                ("effective_cache_size", "50-75% of RAM"),
                ("random_page_cost", "1.1 for SSD, 4.0 for HDD"),
                ("effective_io_concurrency", "200 for SSD, 1-2 for HDD"),
                ("max_worker_processes", "number of CPU cores"),
                ("max_parallel_workers", "number of CPU cores"),
                ("max_parallel_workers_per_gather", "2-4"),
                ("wal_buffers", "16MB"),
                ("checkpoint_completion_target", "0.9"),
                ("default_statistics_target", "100-1000"),
            ]

            current_settings = {}
            for setting, recommendation in settings_to_check:
                cursor.execute("SHOW %s", [setting])
                current_value = cursor.fetchone()[0]

                current_settings[setting] = {"current": current_value, "recommended": recommendation}

                # Add specific recommendations
                if setting == "shared_buffers" and int(current_value) < 1024:
                    recommendations.append(
                        {
                            "setting": setting,
                            "current": current_value,
                            "recommended": f"Set to {recommendation} for better performance",
                            "impact": "High",
                        }
                    )

        return {"current_settings": current_settings, "recommendations": recommendations}

    def create_hypothetical_index(self, table_name: str, fields: List[str]) -> str:
        """Create a hypothetical index for testing without affecting production"""
        import uuid

        index_name = f"hypo_idx_{uuid.uuid4().hex[:8]}"
        field_str = "_".join(fields)

        with self.connection.cursor() as cursor:
            # Requires hypopg extension
            cursor.execute(
                f"""
                SELECT * FROM hypopg_create_index(
                    'CREATE INDEX {index_name} ON {table_name} ({field_str})'
                );
            """
            )

            return index_name

    def explain_query(self, query: str, analyze: bool = True) -> Dict[str, Any]:
        """Get detailed query execution plan"""
        with self.connection.cursor() as cursor:
            if analyze:
                cursor.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
            else:
                cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")

            result = cursor.fetchone()[0]
            return result[0] if result else {}

    @contextmanager
    def performance_monitoring(self, operation_name: str):
        """Context manager for monitoring query performance"""
        start_time = time.time()
        start_queries = self.connection.queries_log[-1]["time"] if self.connection.queries_log else 0

        try:
            yield
        finally:
            end_time = time.time()
            end_queries = self.connection.queries_log[-1]["time"] if self.connection.queries_log else 0

            duration = end_time - start_time
            query_count = end_queries - start_queries

            logger.info(f"Operation '{operation_name}' took {duration:.3f}s with {query_count} queries")

            if duration > 1.0:  # Log slow operations
                logger.warning(f"Slow operation detected: {operation_name} ({duration:.3f}s)")


# Global optimizer instance
postgres_optimizer = PostgresOptimizer()


# Utility functions for common optimization tasks
def optimize_patient_queries():
    """Apply specific optimizations for patient-related queries"""
    # Create optimal indexes for patient model
    indexes_to_create = [
        ("patients_patient", ["hospital_id", "status", "last_name"], "btree"),
        ("patients_patient", ["hospital_id", "date_of_birth"], "btree"),
        ("patients_patient", ["primary_care_physician_id", "status"], "btree"),
        ("patients_patient", ["medical_record_number"], "btree"),
        ("patients_patient", ["hospital_id", "created_at"], "btree"),
        ("patients_patient", ["uuid"], "btree"),
    ]

    for table, fields, index_type in indexes_to_create:
        postgres_optimizer.create_index(table, fields, index_type)

    # Analyze the table
    postgres_optimizer.analyze_table("patients_patient")


def optimize_appointment_queries():
    """Apply specific optimizations for appointment-related queries"""
    indexes_to_create = [
        ("appointments_appointment", ["hospital_id", "appointment_date", "status"], "btree"),
        ("appointments_appointment", ["patient_id", "appointment_date"], "btree"),
        ("appointments_appointment", ["physician_id", "appointment_date"], "btree"),
        ("appointments_appointment", ["hospital_id", "status"], "btree"),
    ]

    for table, fields, index_type in indexes_to_create:
        postgres_optimizer.create_index(table, fields, index_type)

    postgres_optimizer.analyze_table("appointments_appointment")


def optimize_database_warmup():
    """Pre-warm database cache with frequently accessed data"""
    queries_to_warm = [
        "SELECT * FROM patients_patient LIMIT 1000",
        "SELECT * FROM appointments_appointment WHERE appointment_date >= CURRENT_DATE LIMIT 1000",
        "SELECT * FROM hospitals_hospital LIMIT 100",
    ]

    with connection.cursor() as cursor:
        for query in queries_to_warm:
            try:
                cursor.execute(query)
                cursor.fetchall()  # Force execution
                logger.info(f"Warmed up cache with: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to warm up cache with {query}: {e}")


def schedule_maintenance():
    """Schedule regular maintenance tasks"""
    import threading
    import time

    def maintenance_task():
        while True:
            try:
                # Run ANALYZE on all tables
                tables = ["patients_patient", "appointments_appointment", "hospitals_hospital"]
                for table in tables:
                    postgres_optimizer.analyze_table(table)

                # Run VACUUM if needed
                if time.time() % 86400 == 0:  # Daily
                    for table in tables:
                        postgres_optimizer.vacuum_table(table)

                time.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Maintenance task failed: {e}")
                time.sleep(3600)  # Wait before retrying

    # Start maintenance thread
    thread = threading.Thread(target=maintenance_task, daemon=True)
    thread.start()
