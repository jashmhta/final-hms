"""
Comprehensive database indexing strategy for healthcare data optimization.
Provides automatic index management, analysis, and recommendations.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from django.db import connections, models
from django.db.models import Index, UniqueConstraint
from django.utils import timezone

from .database_optimization import DatabaseOptimizer

logger = logging.getLogger(__name__)


class IndexType(Enum):
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    BRIN = "brin"
    SPGIST = "spgist"
    PARTIAL = "partial"


class IndexPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class IndexDefinition:
    table_name: str
    column_names: List[str]
    index_type: IndexType
    priority: IndexPriority
    description: str
    estimated_benefit: float = 0.0
    queries_affected: int = 0
    is_unique: bool = False
    condition: Optional[str] = None  # For partial indexes
    estimated_size_mb: float = 0.0


@dataclass
class IndexAnalysisResult:
    table_name: str
    current_indexes: List[str]
    recommended_indexes: List[IndexDefinition]
    missing_indexes: List[str]
    redundant_indexes: List[str]
    unused_indexes: List[str]
    optimization_score: float = 0.0


class HealthcareIndexingStrategy:
    """Healthcare-specific indexing strategy and recommendations."""

    def __init__(self):
        self.db_optimizer = DatabaseOptimizer()
        self.healthcare_indexes = self._define_healthcare_indexes()

    def _define_healthcare_indexes(self) -> Dict[str, List[IndexDefinition]]:
        """Define healthcare-specific index patterns."""
        return {
            "patients_patient": [
                IndexDefinition(
                    table_name="patients_patient",
                    column_names=["hospital_id", "status", "created_at"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.CRITICAL,
                    description="Multi-tenant patient queries with status filtering",
                    estimated_benefit=0.95,
                    queries_affected=1000,
                ),
                IndexDefinition(
                    table_name="patients_patient",
                    column_names=["hospital_id", "last_name", "first_name"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.HIGH,
                    description="Patient search by name within hospital",
                    estimated_benefit=0.85,
                    queries_affected=500,
                ),
                IndexDefinition(
                    table_name="patients_patient",
                    column_names=["medical_record_number"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.CRITICAL,
                    description="Unique patient identifier lookup",
                    estimated_benefit=0.99,
                    queries_affected=800,
                    is_unique=True,
                ),
                IndexDefinition(
                    table_name="patients_patient",
                    column_names=["hospital_id", "date_of_birth"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.MEDIUM,
                    description="Patient lookup by date of birth",
                    estimated_benefit=0.70,
                    queries_affected=200,
                ),
                IndexDefinition(
                    table_name="patients_patient",
                    column_names=["uuid"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.HIGH,
                    description="UUID-based patient lookup",
                    estimated_benefit=0.90,
                    queries_affected=600,
                    is_unique=True,
                ),
                IndexDefinition(
                    table_name="patients_patient",
                    column_names=["hospital_id", "primary_care_physician_id", "status"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.MEDIUM,
                    description="Patient queries by physician within hospital",
                    estimated_benefit=0.75,
                    queries_affected=300,
                ),
            ],
            "appointments_appointment": [
                IndexDefinition(
                    table_name="appointments_appointment",
                    column_names=["hospital_id", "doctor_id", "appointment_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.CRITICAL,
                    description="Doctor's daily schedule queries",
                    estimated_benefit=0.95,
                    queries_affected=1200,
                ),
                IndexDefinition(
                    table_name="appointments_appointment",
                    column_names=["hospital_id", "patient_id", "appointment_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.HIGH,
                    description="Patient appointment history queries",
                    estimated_benefit=0.85,
                    queries_affected=600,
                ),
                IndexDefinition(
                    table_name="appointments_appointment",
                    column_names=["appointment_number"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.CRITICAL,
                    description="Unique appointment number lookup",
                    estimated_benefit=0.99,
                    queries_affected=900,
                    is_unique=True,
                ),
                IndexDefinition(
                    table_name="appointments_appointment",
                    column_names=["hospital_id", "status", "appointment_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.HIGH,
                    description="Appointment status filtering by date",
                    estimated_benefit=0.80,
                    queries_affected=400,
                ),
                IndexDefinition(
                    table_name="appointments_appointment",
                    column_names=[
                        "hospital_id",
                        "appointment_date",
                        "appointment_time",
                    ],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.MEDIUM,
                    description="Time-based appointment queries",
                    estimated_benefit=0.75,
                    queries_affected=350,
                ),
            ],
            "ehr_encounter": [
                IndexDefinition(
                    table_name="ehr_encounter",
                    column_names=["hospital_id", "patient_id", "encounter_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.CRITICAL,
                    description="Patient encounter history queries",
                    estimated_benefit=0.95,
                    queries_affected=1000,
                ),
                IndexDefinition(
                    table_name="ehr_encounter",
                    column_names=["hospital_id", "doctor_id", "encounter_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.HIGH,
                    description="Doctor's patient encounters queries",
                    estimated_benefit=0.85,
                    queries_affected=500,
                ),
                IndexDefinition(
                    table_name="ehr_encounter",
                    column_names=["hospital_id", "encounter_type", "created_at"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.MEDIUM,
                    description="Encounter type filtering queries",
                    estimated_benefit=0.70,
                    queries_affected=300,
                ),
                IndexDefinition(
                    table_name="ehr_encounter",
                    column_names=["hospital_id", "patient_id", "is_finalized"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.MEDIUM,
                    description="Active vs finalized encounter queries",
                    estimated_benefit=0.65,
                    queries_affected=200,
                ),
            ],
            "pharmacy_prescription": [
                IndexDefinition(
                    table_name="pharmacy_prescription",
                    column_names=["hospital_id", "patient_id", "prescribed_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.HIGH,
                    description="Patient prescription history queries",
                    estimated_benefit=0.85,
                    queries_affected=600,
                ),
                IndexDefinition(
                    table_name="pharmacy_prescription",
                    column_names=["hospital_id", "medication_id", "prescribed_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.MEDIUM,
                    description="Medication usage tracking queries",
                    estimated_benefit=0.70,
                    queries_affected=300,
                ),
                IndexDefinition(
                    table_name="pharmacy_prescription",
                    column_names=["hospital_id", "status", "prescribed_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.MEDIUM,
                    description="Active prescription queries",
                    estimated_benefit=0.75,
                    queries_affected=350,
                ),
            ],
            "lab_laborder": [
                IndexDefinition(
                    table_name="lab_laborder",
                    column_names=["hospital_id", "patient_id", "order_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.HIGH,
                    description="Patient lab order history queries",
                    estimated_benefit=0.85,
                    queries_affected=500,
                ),
                IndexDefinition(
                    table_name="lab_laborder",
                    column_names=["hospital_id", "doctor_id", "order_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.MEDIUM,
                    description="Doctor's lab order queries",
                    estimated_benefit=0.70,
                    queries_affected=250,
                ),
                IndexDefinition(
                    table_name="lab_laborder",
                    column_names=["hospital_id", "test_id", "order_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.MEDIUM,
                    description="Test-specific lab queries",
                    estimated_benefit=0.65,
                    queries_affected=200,
                ),
                IndexDefinition(
                    table_name="lab_laborder",
                    column_names=["hospital_id", "status", "order_date"],
                    index_type=IndexType.BTREE,
                    priority=IndexPriority.MEDIUM,
                    description="Lab order status queries",
                    estimated_benefit=0.75,
                    queries_affected=300,
                ),
            ],
        }

    def analyze_table_indexes(self, table_name: str) -> IndexAnalysisResult:
        """Analyze current indexes for a table and provide recommendations."""
        result = IndexAnalysisResult(
            table_name=table_name,
            current_indexes=[],
            recommended_indexes=[],
            missing_indexes=[],
            redundant_indexes=[],
            unused_indexes=[],
        )

        try:
            with self.db_optimizer.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    if self.db_optimizer.is_postgres:
                        # Get existing indexes
                        cursor.execute(
                            """
                            SELECT
                                indexname,
                                indexdef,
                                indisunique,
                                indisprimary,
                                pg_relation_size(indexrelid) as index_size
                            FROM pg_indexes
                            JOIN pg_stat_user_indexes USING (schemaname, tablename, indexname)
                            WHERE tablename = %s
                        """,
                            (table_name,),
                        )

                        for row in cursor.fetchall():
                            result.current_indexes.append(
                                {
                                    "name": row[0],
                                    "definition": row[1],
                                    "is_unique": row[2],
                                    "is_primary": row[3],
                                    "size_bytes": row[4],
                                }
                            )

                        # Get index usage statistics
                        cursor.execute(
                            """
                            SELECT
                                indexrelname,
                                idx_scan,
                                idx_tup_read,
                                idx_tup_fetch
                            FROM pg_stat_user_indexes
                            WHERE relname = %s
                        """,
                            (table_name,),
                        )

                        index_stats = {}
                        for row in cursor.fetchall():
                            index_stats[row[0]] = {
                                "scans": row[1],
                                "tuples_read": row[2],
                                "tuples_fetched": row[3],
                            }

                        # Analyze for unused indexes
                        for index_info in result.current_indexes:
                            index_name = index_info["name"]
                            stats = index_stats.get(index_name, {})
                            if (
                                stats.get("scans", 0) == 0
                                and not index_info["is_primary"]
                            ):
                                result.unused_indexes.append(index_name)

                        # Get healthcare-specific recommendations
                        if table_name in self.healthcare_indexes:
                            recommended = self.healthcare_indexes[table_name]
                            existing_index_names = {
                                idx["name"] for idx in result.current_indexes
                            }

                            for rec in recommended:
                                # Check if similar index already exists
                                index_name = self._generate_index_name(rec)
                                if index_name not in existing_index_names:
                                    result.recommended_indexes.append(rec)
                                    result.missing_indexes.append(
                                        f"{rec.column_names} ({rec.index_type.value})"
                                    )

                        # Calculate optimization score
                        result.optimization_score = self._calculate_optimization_score(
                            result
                        )

        except Exception as e:
            logger.error(f"Error analyzing table indexes for {table_name}: {e}")

        return result

    def _generate_index_name(self, index_def: IndexDefinition) -> str:
        """Generate a standardized index name."""
        columns = "_".join(index_def.column_names)
        unique_suffix = "_unique" if index_def.is_unique else ""
        return f"{index_def.table_name}_{columns}{unique_suffix}_idx"

    def _calculate_optimization_score(self, analysis: IndexAnalysisResult) -> float:
        """Calculate optimization score for a table (0.0 to 1.0)."""
        score = 1.0

        # Deduct for missing indexes
        if analysis.missing_indexes:
            critical_missing = sum(
                1
                for rec in analysis.recommended_indexes
                if rec.priority == IndexPriority.CRITICAL
            )
            score -= min(critical_missing * 0.2, 0.5)

        # Deduct for unused indexes
        if analysis.unused_indexes:
            score -= min(len(analysis.unused_indexes) * 0.05, 0.2)

        # Deduct for redundant indexes
        if analysis.redundant_indexes:
            score -= min(len(analysis.redundant_indexes) * 0.1, 0.3)

        return max(score, 0.0)

    def generate_index_sql(self, index_def: IndexDefinition) -> str:
        """Generate SQL for creating an index."""
        columns_str = ", ".join(index_def.column_names)
        index_name = self._generate_index_name(index_def)

        if index_def.condition:
            # Partial index
            return f"""
                CREATE INDEX CONCURRENTLY {index_name}
                ON {index_def.table_name} USING {index_def.index_type.value} ({columns_str})
                WHERE {index_def.condition};
            """
        elif index_def.is_unique:
            return f"""
                CREATE UNIQUE INDEX CONCURRENTLY {index_name}
                ON {index_def.table_name} USING {index_def.index_type.value} ({columns_str});
            """
        else:
            return f"""
                CREATE INDEX CONCURRENTLY {index_name}
                ON {index_def.table_name} USING {index_def.index_type.value} ({columns_str});
            """

    def create_indexes(self, table_name: str, dry_run: bool = True) -> Dict[str, Any]:
        """Create recommended indexes for a table."""
        result = {
            "table_name": table_name,
            "indexes_created": 0,
            "sql_executed": [],
            "errors": [],
            "dry_run": dry_run,
        }

        try:
            analysis = self.analyze_table_indexes(table_name)

            for index_def in analysis.recommended_indexes:
                try:
                    sql = self.generate_index_sql(index_def)

                    if not dry_run:
                        with self.db_optimizer.get_database_connection() as connection:
                            with connection.cursor() as cursor:
                                cursor.execute(sql)

                    result["indexes_created"] += 1
                    result["sql_executed"].append(sql)

                except Exception as e:
                    error_msg = f"Error creating index {index_def.column_names}: {e}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

        except Exception as e:
            result["errors"].append(f"Error creating indexes for {table_name}: {e}")

        return result

    def analyze_all_healthcare_tables(self) -> Dict[str, IndexAnalysisResult]:
        """Analyze all healthcare-related tables."""
        results = {}

        for table_name in self.healthcare_indexes.keys():
            try:
                results[table_name] = self.analyze_table_indexes(table_name)
            except Exception as e:
                logger.error(f"Error analyzing table {table_name}: {e}")

        return results

    def get_index_recommendations_summary(self) -> Dict[str, Any]:
        """Get summary of all index recommendations."""
        summary = {
            "timestamp": timezone.now().isoformat(),
            "total_tables_analyzed": 0,
            "total_recommendations": 0,
            "critical_recommendations": 0,
            "high_priority_recommendations": 0,
            "unused_indexes": 0,
            "optimization_score": 0.0,
            "table_summaries": {},
        }

        try:
            all_results = self.analyze_all_healthcare_tables()

            for table_name, analysis in all_results.items():
                summary["total_tables_analyzed"] += 1
                summary["total_recommendations"] += len(analysis.recommended_indexes)

                # Count by priority
                for rec in analysis.recommended_indexes:
                    if rec.priority == IndexPriority.CRITICAL:
                        summary["critical_recommendations"] += 1
                    elif rec.priority == IndexPriority.HIGH:
                        summary["high_priority_recommendations"] += 1

                summary["unused_indexes"] += len(analysis.unused_indexes)

                # Store table summary
                summary["table_summaries"][table_name] = {
                    "optimization_score": analysis.optimization_score,
                    "recommendations": len(analysis.recommended_indexes),
                    "unused_indexes": len(analysis.unused_indexes),
                    "critical_issues": sum(
                        1
                        for r in analysis.recommended_indexes
                        if r.priority == IndexPriority.CRITICAL
                    ),
                }

            # Calculate overall optimization score
            if summary["total_tables_analyzed"] > 0:
                total_score = sum(
                    analysis.optimization_score for analysis in all_results.values()
                )
                summary["optimization_score"] = (
                    total_score / summary["total_tables_analyzed"]
                )

        except Exception as e:
            logger.error(f"Error generating index recommendations summary: {e}")

        return summary


# Global instance for easy access
healthcare_indexing_strategy = HealthcareIndexingStrategy()
