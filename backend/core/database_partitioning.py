import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.db import connections, models
from django.db.migrations.operations.base import Operation
from django.db.migrations.executor import MigrationExecutor
from django.db.backends.postgresql.base import DatabaseWrapper
from django.utils import timezone
from core.database_optimization import DatabaseOptimizer


class PartitionStrategy(Enum):
    """Database partitioning strategies for healthcare data."""
    RANGE = "range"          # Range-based partitioning (e.g., date ranges)
    LIST = "list"            # List-based partitioning (e.g., hospital IDs)
    HASH = "hash"            # Hash-based partitioning (e.g., patient ID hash)
    TIME_SERIES = "time_series"  # Time-series partitioning for medical data
    HYBRID = "hybrid"        # Combination of strategies


class PartitionType(Enum):
    """Types of partitioning supported."""
    TABLE_PARTITIONING = "table_partitioning"
    SCHEMA_PARTITIONING = "schema_partitioning"
    DATABASE_SHARDING = "database_sharding"


class HealthcareDataCategory(Enum):
    """Categories of healthcare data for partitioning decisions."""
    PATIENT_DEMOGRAPHICS = "patient_demographics"      # Static patient data
    CLINICAL_DATA = "clinical_data"                    # EHR, encounters, vitals
    APPOINTMENT_DATA = "appointment_data"              # Scheduling and time-based
    FINANCIAL_DATA = "financial_data"                  # Billing, payments
    LABORATORY_DATA = "laboratory_data"                # Lab results and orders
    PHARMACY_DATA = "pharmacy_data"                    # Prescriptions and medications
    IMAGING_DATA = "imaging_data"                     # Radiology and medical images
    AUDIT_DATA = "audit_data"                          # Logs and audit trails


@dataclass
class PartitionConfig:
    """Configuration for database partitioning."""
    table_name: str
    strategy: PartitionStrategy
    partition_key: str
    partition_type: PartitionType
    category: HealthcareDataCategory
    partition_expression: str
    retention_period_days: int
    archive_after_days: int
    compression_enabled: bool = True
    auto_create_partitions: bool = True
    max_partitions: int = 100


@dataclass
class PartitionInfo:
    """Information about a specific partition."""
    partition_name: str
    parent_table: str
    partition_type: PartitionStrategy
    partition_key: str
    partition_expression: str
    from_value: Any
    to_value: Any
    is_active: bool
    row_count: int
    size_mb: float
    created_at: datetime
    last_accessed: datetime


class DatabasePartitioner:
    """Enterprise-grade database partitioning for healthcare systems."""

    def __init__(self, database_optimizer: DatabaseOptimizer = None):
        self.logger = logging.getLogger(__name__)
        self.db_optimizer = database_optimizer or DatabaseOptimizer()
        self.is_postgres = self.db_optimizer.is_postgres
        self.partition_configs: Dict[str, PartitionConfig] = {}
        self.partition_stats: Dict[str, PartitionInfo] = {}
        self._setup_healthcare_partitioning()

    def _setup_healthcare_partitioning(self):
        """Setup healthcare-specific partitioning configurations."""

        # Patient demographics - partition by hospital (list partitioning)
        self.partition_configs['patients_patient'] = PartitionConfig(
            table_name='patients_patient',
            strategy=PartitionStrategy.LIST,
            partition_key='hospital_id',
            partition_type=PartitionType.TABLE_PARTITIONING,
            category=HealthcareDataCategory.PATIENT_DEMOGRAPHICS,
            partition_expression='hospital_id',
            retention_period_days=3650,  # 10 years retention
            archive_after_days=2555,      # Archive after 7 years
            compression_enabled=True,
            auto_create_partitions=True
        )

        # Clinical encounters - partition by date (range partitioning)
        self.partition_configs['ehr_encounter'] = PartitionConfig(
            table_name='ehr_encounter',
            strategy=PartitionStrategy.RANGE,
            partition_key='encounter_date',
            partition_type=PartitionType.TABLE_PARTITIONING,
            category=HealthcareDataCategory.CLINICAL_DATA,
            partition_expression='DATE(encounter_date)',
            retention_period_days=3650,  # 10 years for medical records
            archive_after_days=1825,     # Archive after 5 years
            compression_enabled=True,
            auto_create_partitions=True
        )

        # Appointments - partition by date (time-series partitioning)
        self.partition_configs['appointments_appointment'] = PartitionConfig(
            table_name='appointments_appointment',
            strategy=PartitionStrategy.TIME_SERIES,
            partition_key='appointment_date',
            partition_type=PartitionType.TABLE_PARTITIONING,
            category=HealthcareDataCategory.APPOINTMENT_DATA,
            partition_expression='DATE(appointment_date)',
            retention_period_days=730,   # 2 years for appointments
            archive_after_days=365,      # Archive after 1 year
            compression_enabled=True,
            auto_create_partitions=True
        )

        # Vital signs - partition by encounter and timestamp (hybrid partitioning)
        self.partition_configs['ehr_vitalsign'] = PartitionConfig(
            table_name='ehr_vitalsign',
            strategy=PartitionStrategy.HYBRID,
            partition_key='recorded_at',
            partition_type=PartitionType.TABLE_PARTITIONING,
            category=HealthcareDataCategory.CLINICAL_DATA,
            partition_expression='DATE(recorded_at)',
            retention_period_days=3650,  # 10 years for vitals
            archive_after_days=1095,     # Archive after 3 years
            compression_enabled=True,
            auto_create_partitions=True
        )

        # Lab results - partition by result date (time-series partitioning)
        self.partition_configs['lab_labresult'] = PartitionConfig(
            table_name='lab_labresult',
            strategy=PartitionStrategy.TIME_SERIES,
            partition_key='result_date',
            partition_type=PartitionType.TABLE_PARTITIONING,
            category=HealthcareDataCategory.LABORATORY_DATA,
            partition_expression='DATE(result_date)',
            retention_period_days=3650,  # 10 years for lab results
            archive_after_days=2555,     # Archive after 7 years
            compression_enabled=True,
            auto_create_partitions=True
        )

        # Prescriptions - partition by prescribed date and hospital (hybrid)
        self.partition_configs['pharmacy_prescription'] = PartitionConfig(
            table_name='pharmacy_prescription',
            strategy=PartitionStrategy.HYBRID,
            partition_key='prescribed_date',
            partition_type=PartitionType.TABLE_PARTITIONING,
            category=HealthcareDataCategory.PHARMACY_DATA,
            partition_expression='DATE(prescribed_date)',
            retention_period_days=3650,  # 10 years for prescriptions
            archive_after_days=1825,     # Archive after 5 years
            compression_enabled=True,
            auto_create_partitions=True
        )

        # Billing - partition by created date and hospital (hybrid)
        self.partition_configs['billing_bill'] = PartitionConfig(
            table_name='billing_bill',
            strategy=PartitionStrategy.HYBRID,
            partition_key='created_at',
            partition_type=PartitionType.TABLE_PARTITIONING,
            category=HealthcareDataCategory.FINANCIAL_DATA,
            partition_expression='DATE(created_at)',
            retention_period_days=4380,  # 12 years for financial records
            archive_after_days=2555,     # Archive after 7 years
            compression_enabled=True,
            auto_create_partitions=True
        )

        # Audit logs - partition by timestamp (time-series with high rotation)
        self.partition_configs['accountingauditlog'] = PartitionConfig(
            table_name='accountingauditlog',
            strategy=PartitionStrategy.TIME_SERIES,
            partition_key='created_at',
            partition_type=PartitionType.TABLE_PARTITIONING,
            category=HealthcareDataCategory.AUDIT_DATA,
            partition_expression='DATE(created_at)',
            retention_period_days=1825,  # 5 years for audit logs
            archive_after_days=90,       # Archive after 90 days
            compression_enabled=True,
            auto_create_partitions=True,
            max_partitions=365           # Daily partitions for 1 year
        )

    def is_partitioning_supported(self) -> bool:
        """Check if the current database supports partitioning."""
        if not self.is_postgres:
            self.logger.warning("Partitioning requires PostgreSQL")
            return False

        try:
            with self.db_optimizer.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    # Check PostgreSQL version (partitioning requires 10.0+)
                    cursor.execute("SELECT version()")
                    version_str = cursor.fetchone()[0]
                    version_parts = version_str.split()[1].split('.')
                    major_version = int(version_parts[0])
                    minor_version = int(version_parts[1]) if len(version_parts) > 1 else 0

                    return major_version >= 10 or (major_version == 10 and minor_version >= 0)
        except Exception as e:
            self.logger.error(f"Error checking partitioning support: {e}")
            return False

    def create_partitioned_table(self, config: PartitionConfig) -> Dict[str, Any]:
        """Create a partitioned table with the specified configuration."""
        if not self.is_partitioning_supported():
            return {"error": "Partitioning not supported"}

        result = {
            "table_name": config.table_name,
            "created": False,
            "partitions_created": 0,
            "errors": [],
            "warnings": []
        }

        try:
            with self.db_optimizer.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    # Check if table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = %s
                        )
                    """, (config.table_name,))

                    table_exists = cursor.fetchone()[0]

                    if table_exists:
                        result["warnings"].append(f"Table {config.table_name} already exists")
                        return result

                    # Create partitioned table
                    create_sql = self._generate_partitioned_table_sql(config)
                    cursor.execute(create_sql)

                    # Create initial partitions
                    initial_partitions = self._create_initial_partitions(cursor, config)
                    result["partitions_created"] = len(initial_partitions)

                    # Create indexes for partitioned table
                    self._create_partition_indexes(cursor, config)

                    result["created"] = True
                    self.logger.info(f"Created partitioned table: {config.table_name}")

        except Exception as e:
            result["errors"].append(str(e))
            self.logger.error(f"Error creating partitioned table {config.table_name}: {e}")

        return result

    def _generate_partitioned_table_sql(self, config: PartitionConfig) -> str:
        """Generate SQL for creating a partitioned table."""

        # Get the original table definition
        table_sql = f"""
            CREATE TABLE {config.table_name} (
                id BIGSERIAL PRIMARY KEY,
                hospital_id INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            ) PARTITION BY {self._get_partition_clause(config)}
        """

        # For existing tables, we need to create a partitioned version
        return f"""
            CREATE TABLE {config.table_name}_partitioned (
                LIKE {config.table_name} INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES
            ) PARTITION BY {self._get_partition_clause(config)}
        """

    def _get_partition_clause(self, config: PartitionConfig) -> str:
        """Get the PARTITION BY clause for the configuration."""
        if config.strategy == PartitionStrategy.RANGE:
            return f"RANGE ({config.partition_expression})"
        elif config.strategy == PartitionStrategy.LIST:
            return f"LIST ({config.partition_key})"
        elif config.strategy == PartitionStrategy.HASH:
            return f"HASH ({config.partition_key})"
        elif config.strategy == PartitionStrategy.TIME_SERIES:
            return f"RANGE ({config.partition_expression})"
        else:  # HYBRID
            return f"RANGE ({config.partition_expression})"

    def _create_initial_partitions(self, cursor, config: PartitionConfig) -> List[str]:
        """Create initial partitions for a table."""
        partitions = []

        if config.strategy in [PartitionStrategy.RANGE, PartitionStrategy.TIME_SERIES, PartitionStrategy.HYBRID]:
            # Create monthly partitions for the next 12 months
            current_date = timezone.now().date()

            for i in range(12):
                start_date = current_date.replace(day=1) + timedelta(days=32*i)
                end_date = start_date + timedelta(days=32)
                end_date = end_date.replace(day=1)

                partition_name = f"{config.table_name}_partitioned_{start_date.strftime('%Y_%m')}"

                partition_sql = f"""
                    CREATE TABLE {partition_name} PARTITION OF {config.table_name}_partitioned
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                """

                cursor.execute(partition_sql)
                partitions.append(partition_name)

        elif config.strategy == PartitionStrategy.LIST:
            # Create partitions for hospital IDs (assuming hospital IDs 1-10)
            for hospital_id in range(1, 11):
                partition_name = f"{config.table_name}_partitioned_hospital_{hospital_id}"

                partition_sql = f"""
                    CREATE TABLE {partition_name} PARTITION OF {config.table_name}_partitioned
                    FOR VALUES IN ({hospital_id})
                """

                cursor.execute(partition_sql)
                partitions.append(partition_name)

        return partitions

    def _create_partition_indexes(self, cursor, config: PartitionConfig):
        """Create indexes optimized for partitioned tables."""
        # Create local indexes for each partition type
        if config.category == HealthcareDataCategory.CLINICAL_DATA:
            # Indexes for clinical data queries
            indexes = [
                f"CREATE INDEX idx_{config.table_name}_partitioned_hospital ON {config.table_name}_partitioned (hospital_id)",
                f"CREATE INDEX idx_{config.table_name}_partitioned_patient ON {config.table_name}_partitioned (patient_id)",
                f"CREATE INDEX idx_{config.table_name}_partitioned_created ON {config.table_name}_partitioned (created_at)"
            ]
        elif config.category == HealthcareDataCategory.APPOINTMENT_DATA:
            # Indexes for appointment scheduling
            indexes = [
                f"CREATE INDEX idx_{config.table_name}_partitioned_date ON {config.table_name}_partitioned (appointment_date)",
                f"CREATE INDEX idx_{config.table_name}_partitioned_hospital_date ON {config.table_name}_partitioned (hospital_id, appointment_date)",
                f"CREATE INDEX idx_{config.table_name}_partitioned_status ON {config.table_name}_partitioned (status)"
            ]
        else:
            # Generic indexes
            indexes = [
                f"CREATE INDEX idx_{config.table_name}_partitioned_hospital ON {config.table_name}_partitioned (hospital_id)",
                f"CREATE INDEX idx_{config.table_name}_partitioned_created ON {config.table_name}_partitioned (created_at)"
            ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                self.logger.warning(f"Could not create index: {e}")

    def create_time_partitions(self, table_name: str, months_ahead: int = 3) -> Dict[str, Any]:
        """Create time-based partitions for the specified number of months ahead."""
        if not self.is_partitioning_supported():
            return {"error": "Partitioning not supported"}

        result = {
            "table_name": table_name,
            "partitions_created": [],
            "errors": [],
            "total_created": 0
        }

        try:
            with self.db_optimizer.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    current_date = timezone.now().date()

                    for i in range(months_ahead):
                        target_date = current_date + timedelta(days=32 * i)
                        start_date = target_date.replace(day=1)
                        end_date = start_date + timedelta(days=32)
                        end_date = end_date.replace(day=1)

                        partition_name = f"{table_name}_partitioned_{start_date.strftime('%Y_%m')}"

                        # Check if partition already exists
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM pg_tables
                                WHERE tablename = %s
                            )
                        """, (partition_name,))

                        if not cursor.fetchone()[0]:
                            partition_sql = f"""
                                CREATE TABLE {partition_name} PARTITION OF {table_name}_partitioned
                                FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                            """

                            cursor.execute(partition_sql)
                            result["partitions_created"].append(partition_name)
                            result["total_created"] += 1

        except Exception as e:
            result["errors"].append(str(e))
            self.logger.error(f"Error creating time partitions for {table_name}: {e}")

        return result

    def maintain_partitions(self) -> Dict[str, Any]:
        """Maintain partitions by creating new ones and archiving old ones."""
        if not self.is_partitioning_supported():
            return {"error": "Partitioning not supported"}

        result = {
            "maintenance_timestamp": timezone.now().isoformat(),
            "tables_processed": 0,
            "partitions_created": 0,
            "partitions_archived": 0,
            "errors": [],
            "tables_status": {}
        }

        for table_name, config in self.partition_configs.items():
            try:
                table_result = self._maintain_table_partitions(table_name, config)
                result["tables_processed"] += 1
                result["partitions_created"] += table_result.get("partitions_created", 0)
                result["partitions_archived"] += table_result.get("partitions_archived", 0)
                result["tables_status"][table_name] = table_result

            except Exception as e:
                result["errors"].append(f"Error maintaining {table_name}: {e}")
                self.logger.error(f"Error maintaining partitions for {table_name}: {e}")

        return result

    def _maintain_table_partitions(self, table_name: str, config: PartitionConfig) -> Dict[str, Any]:
        """Maintain partitions for a specific table."""
        result = {
            "table_name": table_name,
            "partitions_created": 0,
            "partitions_archived": 0,
            "status": "maintained"
        }

        # Create future partitions if auto_create is enabled
        if config.auto_create_partitions:
            create_result = self.create_time_partitions(table_name, months_ahead=3)
            result["partitions_created"] = create_result.get("total_created", 0)

        # Archive old partitions if needed
        if config.archive_after_days > 0:
            archive_result = self._archive_old_partitions(table_name, config)
            result["partitions_archived"] = archive_result.get("partitions_archived", 0)

        return result

    def _archive_old_partitions(self, table_name: str, config: PartitionConfig) -> Dict[str, Any]:
        """Archive old partitions based on retention policy."""
        result = {
            "table_name": table_name,
            "partitions_archived": 0,
            "archived_partitions": []
        }

        try:
            with self.db_optimizer.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    # Get partitions older than retention period
                    cutoff_date = timezone.now() - timedelta(days=config.archive_after_days)

                    cursor.execute("""
                        SELECT
                            schemaname,
                            tablename,
                            partstrat,
                            partattrs
                        FROM pg_partitions
                        WHERE tablename LIKE %s
                    """, (f"{table_name}_partitioned_%",))

                    partitions = cursor.fetchall()

                    for partition in partitions:
                        partition_name = partition[1]

                        # Extract date from partition name (format: table_YYYY_MM)
                        try:
                            date_part = partition_name.split('_')[-2:]
                            year, month = int(date_part[0]), int(date_part[1])
                            partition_date = datetime(year, month, 1).date()

                            if partition_date < cutoff_date:
                                # Archive the partition
                                archive_table_name = f"{partition_name}_archived"

                                cursor.execute(f"""
                                    ALTER TABLE {partition_name} RENAME TO {archive_table_name}
                                """)

                                # Compress archived partition
                                if config.compression_enabled:
                                    cursor.execute(f"""
                                        ALTER TABLE {archive_table_name} SET (compression = 'pglz')
                                    """)

                                result["partitions_archived"] += 1
                                result["archived_partitions"].append(archive_table_name)

                        except (ValueError, IndexError):
                            # Skip if date parsing fails
                            continue

        except Exception as e:
            self.logger.error(f"Error archiving partitions for {table_name}: {e}")

        return result

    def get_partition_stats(self, table_name: str = None) -> Dict[str, Any]:
        """Get statistics about partition usage and performance."""
        stats = {
            "timestamp": timezone.now().isoformat(),
            "partitioning_enabled": self.is_partitioning_supported(),
            "tables": {}
        }

        if not self.is_partitioning_supported():
            return stats

        try:
            with self.db_optimizer.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    if table_name:
                        tables = [table_name]
                    else:
                        # Get all partitioned tables
                        cursor.execute("""
                            SELECT
                                schemaname,
                                tablename,
                                partstrat,
                                partattrs,
                                partcount
                            FROM pg_partitions
                            WHERE schemaname = 'public'
                            GROUP BY schemaname, tablename, partstrat, partattrs, partcount
                        """)
                        tables_info = cursor.fetchall()
                        tables = list(set([info[1] for info in tables_info]))

                    for table in tables:
                        table_stats = self._get_table_partition_stats(cursor, table)
                        stats["tables"][table] = table_stats

        except Exception as e:
            self.logger.error(f"Error getting partition stats: {e}")
            stats["error"] = str(e)

        return stats

    def _get_table_partition_stats(self, cursor, table_name: str) -> Dict[str, Any]:
        """Get partition statistics for a specific table."""
        stats = {
            "table_name": table_name,
            "partition_count": 0,
            "total_rows": 0,
            "total_size_mb": 0,
            "partitions": [],
            "oldest_partition": None,
            "newest_partition": None
        }

        try:
            # Get partition information
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    partstrat,
                    partattrs,
                    partcount
                FROM pg_partitions
                WHERE tablename = %s
                LIMIT 1
            """, (table_name,))

            partition_info = cursor.fetchone()
            if partition_info:
                stats["partition_strategy"] = partition_info[2]
                stats["partition_attributes"] = partition_info[3]
                stats["partition_count"] = partition_info[4]

            # Get individual partition stats
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    tablename AS partition_name,
                    pg_total_relation_size(schemaname||'.'||tablename) as size
                FROM pg_tables
                WHERE tablename LIKE %s
                ORDER BY tablename
            """, (f"{table_name}_partitioned_%",))

            partitions = cursor.fetchall()

            for partition in partitions:
                partition_name = partition[2]
                size_mb = partition[3] / (1024 * 1024) if partition[3] else 0

                # Get row count for partition
                cursor.execute(f"SELECT COUNT(*) FROM {partition_name}")
                row_count = cursor.fetchone()[0]

                partition_stats = {
                    "partition_name": partition_name,
                    "row_count": row_count,
                    "size_mb": size_mb
                }

                stats["partitions"].append(partition_stats)
                stats["total_rows"] += row_count
                stats["total_size_mb"] += size_mb

        except Exception as e:
            self.logger.error(f"Error getting stats for {table_name}: {e}")

        return stats

    def setup_partition_maintenance_job(self) -> Dict[str, Any]:
        """Setup automated partition maintenance job."""
        if not self.is_partitioning_supported():
            return {"error": "Partitioning not supported"}

        result = {
            "job_created": False,
            "job_name": "partition_maintenance",
            "schedule": "0 2 * * *",  # Daily at 2 AM
            "errors": []
        }

        try:
            # Create the maintenance function
            maintenance_function = """
                CREATE OR REPLACE FUNCTION maintain_partitions()
                RETURNS void AS $$
                DECLARE
                    maint_result TEXT;
                BEGIN
                    -- This would call the partition maintenance logic
                    -- In a real implementation, you'd call your Python function
                    -- or implement the logic directly in PL/pgSQL
                    RAISE NOTICE 'Running partition maintenance';
                END;
                $$ LANGUAGE plpgsql;
            """

            with self.db_optimizer.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(maintenance_function)

            # Schedule the job using pg_cron extension
            try:
                cursor.execute("""
                    SELECT cron.schedule(
                        'partition_maintenance',
                        '0 2 * * *',
                        $$SELECT maintain_partitions()$$
                    )
                """)
                result["job_created"] = True

            except Exception as e:
                result["errors"].append(f"Could not schedule cron job: {e}")
                result["errors"].append("Make sure pg_cron extension is installed")

        except Exception as e:
            result["errors"].append(f"Error setting up maintenance job: {e}")

        return result

    def get_partition_recommendations(self) -> List[Dict[str, Any]]:
        """Get partitioning recommendations for healthcare data."""
        recommendations = []

        # Analyze current table sizes and access patterns
        try:
            db_stats = self.db_optimizer.get_database_stats()

            for table_name, config in self.partition_configs.items():
                try:
                    table_analysis = self.db_optimizer.analyze_table_performance(table_name)

                    if table_analysis.get('row_count', 0) > 100000:
                        recommendations.append({
                            "table": table_name,
                            "recommendation": "Implement table partitioning",
                            "strategy": config.strategy.value,
                            "reason": f"Large table with {table_analysis['row_count']:,} rows",
                            "priority": "high",
                            "estimated_benefit": "Improved query performance and easier maintenance"
                        })

                    if table_analysis.get('table_size_mb', 0) > 1000:
                        recommendations.append({
                            "table": table_name,
                            "recommendation": "Consider archiving old data",
                            "strategy": "time-based archiving",
                            "reason": f"Large table size: {table_analysis['table_size_mb']:.1f} MB",
                            "priority": "medium",
                            "estimated_benefit": "Reduced storage costs and improved performance"
                        })

                except Exception as e:
                    self.logger.warning(f"Could not analyze table {table_name}: {e}")

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")

        return recommendations

    def migrate_to_partitioned_table(self, table_name: str, config: PartitionConfig) -> Dict[str, Any]:
        """Migrate existing data to a partitioned table structure."""
        if not self.is_partitioning_supported():
            return {"error": "Partitioning not supported"}

        result = {
            "table_name": table_name,
            "migration_completed": False,
            "rows_migrated": 0,
            "errors": [],
            "duration_seconds": 0
        }

        start_time = timezone.now()

        try:
            with self.db_optimizer.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    # Check if partitioned table already exists
                    partitioned_table_name = f"{table_name}_partitioned"
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = %s
                        )
                    """, (partitioned_table_name,))

                    if cursor.fetchone()[0]:
                        result["errors"].append(f"Partitioned table {partitioned_table_name} already exists")
                        return result

                    # Create partitioned table
                    create_result = self.create_partitioned_table(config)
                    if create_result.get("errors"):
                        result["errors"].extend(create_result["errors"])
                        return result

                    # Migrate data in batches
                    batch_size = 10000
                    offset = 0

                    while True:
                        cursor.execute(f"""
                            INSERT INTO {partitioned_table_name}
                            SELECT * FROM {table_name}
                            ORDER BY id
                            LIMIT {batch_size} OFFSET {offset}
                        """)

                        rows_affected = cursor.rowcount
                        result["rows_migrated"] += rows_affected

                        if rows_affected < batch_size:
                            break

                        offset += batch_size
                        # Commit batch to avoid long transactions
                        connection.commit()

                    # Rename tables (atomic operation)
                    cursor.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_old")
                    cursor.execute(f"ALTER TABLE {partitioned_table_name} RENAME TO {table_name}")

                    result["migration_completed"] = True
                    result["duration_seconds"] = (timezone.now() - start_time).total_seconds()

                    self.logger.info(f"Successfully migrated {result['rows_migrated']:,} rows to partitioned table {table_name}")

        except Exception as e:
            result["errors"].append(str(e))
            self.logger.error(f"Error migrating table {table_name}: {e}")

        return result


# Singleton instance for easy access
database_partitioner = DatabasePartitioner()