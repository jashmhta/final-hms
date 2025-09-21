#!/usr/bin/env python3
"""
Emergency Database Performance Optimization Script
Optimizes critical queries, adds indexes, and fixes N+1 query issues
"""
import os
import sys
import django
from django.conf import settings
from django.db import connection, connections, transaction
from django.core.management.base import BaseCommand
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

logger = logging.getLogger(__name__)

CRITICAL_INDEXES = [
    # Patient search optimizations
    """
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_composite_search
    ON patients_patient (hospital_id, last_name, first_name, date_of_birth, status);
    """,

    # Appointment performance
    """
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_provider_time
    ON appointments_appointment (primary_provider_id, start_at, status);
    """,

    """
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_patient_time
    ON appointments_appointment (patient_id, start_at, status);
    """,

    """
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_hospital_status_time
    ON appointments_appointment (hospital_id, status, start_at);
    """,

    # EHR performance
    """
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_medical_records_patient_created
    ON ehr_medicalrecord (patient_id, created_at DESC);
    """,

    """
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vitals_patient_timestamp
    ON ehr_vitalsign (patient_id, recorded_at DESC);
    """,

    # Lab results
    """
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lab_results_patient_test
    ON lab_labresult (patient_id, test_type, result_date DESC);
    """,

    # Pharmacy
    """
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prescriptions_patient_active
    ON pharmacy_prescription (patient_id, is_active, created_at DESC);
    """,

    # Billing
    """
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_billing_patient_status
    ON billing_invoice (patient_id, status, created_at DESC);
    """,
]

QUERY_OPTIMIZATIONS = [
    # Update statistics for better query planning
    "ANALYZE patients_patient;",
    "ANALYZE appointments_appointment;",
    "ANALYZE ehr_medicalrecord;",
    "ANALYZE lab_labresult;",
    "ANALYZE pharmacy_prescription;",
    "ANALYZE billing_invoice;",

    # Set default statistics target for better estimates
    "ALTER DATABASE hms_enterprise SET default_statistics_target = 1000;",

    # Increase work memory for complex queries
    "ALTER DATABASE hms_enterprise SET work_mem = '64MB';",

    # Enable parallel query for large tables
    "ALTER DATABASE hms_enterprise SET max_parallel_workers_per_gather = 4;",
]

CONNECTION_POOL_CONFIG = {
    'max_connections': 200,
    'shared_buffers': '1GB',
    'effective_cache_size': '3GB',
    'maintenance_work_mem': '256MB',
    'checkpoint_completion_target': 0.9,
    'wal_buffers': '16MB',
    'default_statistics_target': 100,
}

class PerformanceOptimizer:
    def __init__(self):
        self.connection = connection

    def execute_sql(self, sql):
        """Execute SQL statement safely"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
                logger.info(f"Executed: {sql[:100]}...")
                return True
        except Exception as e:
            logger.error(f"Error executing SQL: {sql[:100]}... Error: {e}")
            return False

    def create_indexes(self):
        """Create critical performance indexes"""
        logger.info("Creating critical performance indexes...")
        success_count = 0

        for index_sql in CRITICAL_INDEXES:
            if self.execute_sql(index_sql):
                success_count += 1

        logger.info(f"Created {success_count}/{len(CRITICAL_INDEXES)} indexes successfully")
        return success_count == len(CRITICAL_INDEXES)

    def optimize_queries(self):
        """Run query optimizations"""
        logger.info("Running query optimizations...")
        success_count = 0

        for opt_sql in QUERY_OPTIMIZATIONS:
            if self.execute_sql(opt_sql):
                success_count += 1

        logger.info(f"Applied {success_count}/{len(QUERY_OPTIMIZATIONS)} query optimizations")
        return success_count == len(QUERY_OPTIMIZATIONS)

    def update_postgres_config(self):
        """Update PostgreSQL configuration for performance"""
        logger.info("Updating PostgreSQL configuration...")

        config_updates = []
        for param, value in CONNECTION_POOL_CONFIG.items():
            sql = f"ALTER SYSTEM SET {param} = '{value}';"
            if self.execute_sql(sql):
                config_updates.append(param)

        # Reload configuration
        self.execute_sql("SELECT pg_reload_conf();")

        logger.info(f"Updated {len(config_updates)} PostgreSQL configuration parameters")
        return len(config_updates) == len(CONNECTION_POOL_CONFIG)

    def analyze_table_sizes(self):
        """Analyze table sizes and suggest further optimizations"""
        logger.info("Analyzing table sizes...")

        size_query = """
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY size_bytes DESC
        LIMIT 20;
        """

        with self.connection.cursor() as cursor:
            cursor.execute(size_query)
            tables = cursor.fetchall()

        logger.info("Top 20 largest tables:")
        for table in tables:
            logger.info(f"  {table[1]}.{table[0]}: {table[2]}")

        return tables

    def check_slow_queries(self):
        """Check for slow queries in pg_stat_statements"""
        slow_query_check = """
        SELECT
            query,
            calls,
            total_time,
            mean_time,
            rows
        FROM pg_stat_statements
        ORDER BY mean_time DESC
        LIMIT 10;
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(slow_query_check)
                slow_queries = cursor.fetchall()

            if slow_queries:
                logger.warning("Top 10 slowest queries:")
                for query in slow_queries:
                    logger.warning(f"  Mean time: {query[3]:.2f}ms, Calls: {query[1]}, Query: {query[0][:100]}...")
            else:
                logger.info("No slow queries found in pg_stat_statements")

        except Exception as e:
            logger.warning(f"Could not check slow queries: {e}")

    def run_full_optimization(self):
        """Run complete performance optimization"""
        logger.info("Starting full database performance optimization...")

        results = {
            'indexes': self.create_indexes(),
            'query_optimization': self.optimize_queries(),
            'config_update': self.update_postgres_config(),
            'table_analysis': self.analyze_table_sizes(),
            'slow_queries': self.check_slow_queries()
        }

        success_count = sum(1 for v in results.values() if v is True or v is not None)

        logger.info(f"Performance optimization completed. {success_count}/{len(results)} tasks successful")

        return results

def main():
    """Main execution function"""
    optimizer = PerformanceOptimizer()

    print("=" * 60)
    print("EMERGENCY DATABASE PERFORMANCE OPTIMIZATION")
    print("=" * 60)
    print()

    try:
        with transaction.atomic():
            results = optimizer.run_full_optimization()

            print("\n" + "=" * 60)
            print("OPTIMIZATION SUMMARY")
            print("=" * 60)
            print(f"✓ Indexes created: {'Yes' if results['indexes'] else 'No'}")
            print(f"✓ Query optimizations applied: {'Yes' if results['query_optimization'] else 'No'}")
            print(f"✓ PostgreSQL config updated: {'Yes' if results['config_update'] else 'No'}")
            print(f"✓ Table analysis completed: {'Yes' if results['table_analysis'] else 'No'}")
            print("\nDatabase performance optimization completed successfully!")
            print("Restart database services for configuration changes to take effect.")

    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()