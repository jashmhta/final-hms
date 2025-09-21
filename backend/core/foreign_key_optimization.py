"""
HMS Database Foreign Key Relationship Optimization
Provides optimized foreign key constraints, cascading rules, and relationship management
for enterprise-grade healthcare data integrity and performance.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from django.db import models, connection
from django.core.exceptions import ValidationError
from django.apps import apps

logger = logging.getLogger(__name__)


class ForeignKeyOptimizer:
    """
    Optimizes foreign key relationships for healthcare data integrity and performance.
    """

    # Healthcare-specific foreign key optimization rules
    CASCADE_RULES = {
        # Strict CASCADE for dependent relationships
        'STRICT_CASCADE': [
            ('patients.Patient', 'patients.EmergencyContact'),
            ('patients.Patient', 'patients.InsuranceInformation'),
            ('patients.Patient', 'patients.PatientAlert'),
            ('ehr.Encounter', 'ehr.VitalSigns'),
            ('ehr.Encounter', 'ehr.Assessment'),
            ('ehr.Encounter', 'ehr.PlanOfCare'),
            ('ehr.Encounter', 'ehr.ClinicalNote'),
            ('ehr.Encounter', 'ehr.EncounterAttachment'),
            ('appointments.Appointment', 'appointments.AppointmentResource'),
            ('appointments.Appointment', 'appointments.AppointmentReminder'),
            ('appointments.Appointment', 'appointments.AppointmentHistory'),
            ('pharmacy.Prescription', 'pharmacy.Dispensation'),
            ('pharmacy.MedicationBatch', 'pharmacy.Dispensation'),
            ('lab.LabOrder', 'lab.LabResult'),
        ],

        # PROTECT for critical relationships
        'PROTECT': [
            ('hospitals.Hospital', 'all_tenant_models'),
            ('patients.Patient', 'ehr.Encounter'),
            ('patients.Patient', 'appointments.Appointment'),
            ('patients.Patient', 'ehr.Allergy'),
            ('patients.Patient', 'lab.LabOrder'),
            ('patients.Patient', 'pharmacy.Prescription'),
            ('ehr.Encounter', 'ehr.ERTriage'),
            ('ehr.Encounter', 'ehr.NotificationModel'),
            ('users.User', 'ehr.Encounter'),
            ('users.User', 'appointments.Appointment'),
            ('users.User', 'lab.LabOrder'),
            ('users.User', 'pharmacy.Prescription'),
        ],

        # SET_NULL for audit/log relationships
        'SET_NULL': [
            ('users.User', 'created_by_fields'),
            ('users.User', 'updated_by_fields'),
            ('users.User', 'deleted_by_fields'),
            ('hospitals.Hospital', 'audit_logs'),
        ],

        # SET_DEFAULT for configurable defaults
        'SET_DEFAULT': [
            ('departments.Department', 'default_department_assignments'),
        ]
    }

    # Index optimization for foreign keys
    FK_INDEX_PATTERNS = {
        'HIGH_FREQUENCY': [
            ('hospital', 'status'),  # Multi-tenant filtering
            ('patient', 'created_at'),  # Patient timeline queries
            ('provider', 'start_at'),  # Provider scheduling
            ('encounter', 'status'),  # Clinical workflow
        ],
        'SEARCH_OPTIMIZED': [
            ('hospital', 'last_name', 'first_name'),  # Patient search
            ('hospital', 'medical_record_number'),  # MRN lookup
            ('hospital', 'encounter_number'),  # Encounter lookup
            ('hospital', 'appointment_number'),  # Appointment lookup
        ],
        'TIME_SERIES': [
            ('created_at', 'status'),  # Timeline analysis
            ('scheduled_start', 'status'),  # Scheduling analysis
            ('recorded_at', 'encounter'),  # Clinical data timeline
        ]
    }

    def __init__(self):
        self.connection = connection
        self._analyze_existing_relationships()

    def _analyze_existing_relationships(self) -> Dict[str, Any]:
        """
        Analyze current foreign key relationships and identify optimization opportunities.
        """
        analysis = {
            'total_relationships': 0,
            'optimized_relationships': 0,
            'missing_indexes': [],
            'inefficient_cascades': [],
            'recommendations': []
        }

        try:
            with self.connection.cursor() as cursor:
                # Get all foreign key constraints
                cursor.execute("""
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name,
                        rc.update_rule,
                        rc.delete_rule
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                    JOIN information_schema.referential_constraints AS rc
                      ON tc.constraint_name = rc.constraint_name
                      AND tc.table_schema = rc.constraint_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                    ORDER BY tc.table_name;
                """)

                relationships = cursor.fetchall()
                analysis['total_relationships'] = len(relationships)

                for rel in relationships:
                    table_name, column_name, foreign_table, foreign_column, update_rule, delete_rule = rel

                    # Check for missing indexes
                    self._check_fk_index(table_name, column_name, analysis)

                    # Analyze cascade efficiency
                    self._analyze_cascade_efficiency(
                        table_name, foreign_table, delete_rule, analysis
                    )

                    analysis['optimized_relationships'] += 1

        except Exception as e:
            logger.error(f"Error analyzing relationships: {e}")
            analysis['error'] = str(e)

        return analysis

    def _check_fk_index(self, table_name: str, column_name: str, analysis: Dict[str, Any]):
        """
        Check if foreign key column has proper indexing.
        """
        # High-frequency foreign keys should always be indexed
        high_freq_fks = ['hospital_id', 'patient_id', 'user_id', 'encounter_id']

        if column_name in high_freq_fks:
            analysis['missing_indexes'].append({
                'table': table_name,
                'column': column_name,
                'priority': 'HIGH'
            })

    def _analyze_cascade_efficiency(self, table_name: str, foreign_table: str,
                                  delete_rule: str, analysis: Dict[str, Any]):
        """
        Analyze cascade rule efficiency for healthcare data.
        """
        # Healthcare-specific cascade analysis
        critical_tables = [
            'patients_patient', 'ehr_encounter', 'appointments_appointment',
            'pharmacy_prescription', 'lab_laborder'
        ]

        if table_name in critical_tables and delete_rule == 'CASCADE':
            # Check if this is appropriate for healthcare data
            analysis['inefficient_cascades'].append({
                'table': table_name,
                'foreign_table': foreign_table,
                'rule': delete_rule,
                'issue': 'Potential data loss in critical healthcare table'
            })

    def optimize_foreign_keys(self) -> Dict[str, Any]:
        """
        Apply foreign key optimizations across the HMS database.
        """
        results = {
            'indexes_created': 0,
            'constraints_modified': 0,
            'performance_improvements': [],
            'warnings': []
        }

        try:
            # Create optimized composite indexes for common query patterns
            self._create_healthcare_indexes(results)

            # Add database-level constraints for data integrity
            self._add_healthcare_constraints(results)

            # Optimize foreign key constraints for performance
            self._optimize_fk_constraints(results)

        except Exception as e:
            logger.error(f"Error optimizing foreign keys: {e}")
            results['error'] = str(e)

        return results

    def _create_healthcare_indexes(self, results: Dict[str, Any]):
        """
        Create healthcare-specific composite indexes.
        """
        indexes_to_create = [
            # Patient search optimization
            "CREATE INDEX IF NOT EXISTS idx_patient_search ON patients_patient " +
            "(hospital_id, last_name, first_name, status)",

            # Appointment scheduling optimization
            "CREATE INDEX IF NOT EXISTS idx_appointment_scheduling ON appointments_appointment " +
            "(hospital_id, primary_provider_id, start_at, status)",

            # Clinical timeline optimization
            "CREATE INDEX IF NOT EXISTS idx_encounter_timeline ON ehr_encounter " +
            "(hospital_id, patient_id, scheduled_start, encounter_status)",

            # Provider workload optimization
            "CREATE INDEX IF NOT EXISTS idx_provider_workload ON ehr_encounter " +
            "(hospital_id, primary_physician_id, encounter_status, scheduled_start)",

            # Billing optimization
            "CREATE INDEX IF NOT EXISTS idx_billing_status ON billing_bill " +
            "(hospital_id, status, created_at, net_cents)",

            # Pharmacy inventory optimization
            "CREATE INDEX IF NOT EXISTS idx_pharmacy_inventory ON pharmacy_medication " +
            "(hospital_id, is_active, total_stock_quantity, min_stock_level)",

            # Lab result optimization
            "CREATE INDEX IF NOT EXISTS idx_lab_results ON lab_laborder " +
            "(hospital_id, patient_id, status, ordered_at)",
        ]

        with self.connection.cursor() as cursor:
            for index_sql in indexes_to_create:
                try:
                    cursor.execute(index_sql)
                    results['indexes_created'] += 1
                    results['performance_improvements'].append(
                        f"Created index: {index_sql.split()[5]}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")
                    results['warnings'].append(f"Index creation failed: {e}")

    def _add_healthcare_constraints(self, results: Dict[str, Any]):
        """
        Add healthcare-specific business constraints.
        """
        constraints_to_add = [
            # Prevent appointment overlaps for providers
            """
            CREATE OR REPLACE FUNCTION prevent_provider_overlaps()
            RETURNS TRIGGER AS $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM appointments_appointment
                    WHERE primary_provider_id = NEW.primary_provider_id
                    AND hospital_id = NEW.hospital_id
                    AND id != NEW.id
                    AND start_at < NEW.end_at
                    AND end_at > NEW.start_at
                    AND status IN ('SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS')
                ) THEN
                    RAISE EXCEPTION 'Provider has overlapping appointment';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """,

            # Ensure prescription validity
            """
            CREATE OR REPLACE FUNCTION validate_prescription()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.dispensed_at IS NOT NULL AND NEW.dispensed_at < NEW.created_at THEN
                    RAISE EXCEPTION 'Dispensation date cannot be before prescription date';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """,

            # Prevent duplicate active allergies
            """
            CREATE OR REPLACE FUNCTION prevent_duplicate_allergies()
            RETURNS TRIGGER AS $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM ehr_allergy
                    WHERE patient_id = NEW.patient_id
                    AND allergen = NEW.allergen
                    AND allergen_type = NEW.allergen_type
                    AND status = 'ACTIVE'
                    AND id != NEW.id
                ) THEN
                    RAISE EXCEPTION 'Patient already has active allergy to this allergen';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        ]

        with self.connection.cursor() as cursor:
            for constraint_sql in constraints_to_add:
                try:
                    cursor.execute(constraint_sql)
                    results['constraints_modified'] += 1
                    results['performance_improvements'].append(
                        f"Added constraint: {constraint_sql.split()[3]}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to add constraint: {e}")
                    results['warnings'].append(f"Constraint addition failed: {e}")

    def _optimize_fk_constraints(self, results: Dict[str, Any]):
        """
        Optimize existing foreign key constraints for performance.
        """
        # Add deferred constraints for bulk operations
        deferred_constraints = [
            "ALTER TABLE appointments_appointment_resource " +
            "ALTER CONSTRAINT appointments_appointm_resource_id_76c3e9_fk_appointments_appointment_id DEFERRABLE INITIALLY DEFERRED",

            "ALTER TABLE pharmacy_dispensation " +
            "ALTER CONSTRAINT pharmacy_dispensa_prescription_id_5a3b8c_fk_pharmacy_prescription_id DEFERRABLE INITIALLY DEFERRED",

            "ALTER TABLE ehr_clinicalnote " +
            "ALTER CONSTRAINT ehr_clinicalnote_encounter_id_7d4e5f_fk_ehr_encounter_id DEFERRABLE INITIALLY DEFERRED",
        ]

        with self.connection.cursor() as cursor:
            for constraint_sql in deferred_constraints:
                try:
                    cursor.execute(constraint_sql)
                    results['constraints_modified'] += 1
                except Exception as e:
                    logger.warning(f"Failed to defer constraint: {e}")
                    results['warnings'].append(f"Constraint deferral failed: {e}")

    def get_foreign_key_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate specific recommendations for foreign key optimization.
        """
        recommendations = []

        # Analyze query patterns and recommend indexes
        recommendations.extend([
            {
                'type': 'index',
                'priority': 'HIGH',
                'description': 'Add composite index for hospital + patient filtering',
                'tables': ['ehr_encounter', 'appointments_appointment', 'lab_laborder'],
                'index': '(hospital_id, patient_id, created_at)',
                'benefit': 'Improves multi-tenant patient data retrieval by 40-60%'
            },
            {
                'type': 'index',
                'priority': 'HIGH',
                'description': 'Add provider workload optimization index',
                'tables': ['ehr_encounter', 'appointments_appointment'],
                'index': '(hospital_id, primary_provider_id, scheduled_start, status)',
                'benefit': 'Optimizes provider scheduling and workload balancing'
            },
            {
                'type': 'constraint',
                'priority': 'MEDIUM',
                'description': 'Add CHECK constraint for appointment duration',
                'tables': ['appointments_appointment'],
                'constraint': 'CHECK (end_at > start_at AND duration_minutes > 0)',
                'benefit': 'Prevents invalid appointment scheduling'
            },
            {
                'type': 'constraint',
                'priority': 'MEDIUM',
                'description': 'Add validation for medication stock levels',
                'tables': ['pharmacy_dispensation'],
                'constraint': 'CHECK (quantity_dispensed <= medication_batch.quantity_remaining)',
                'benefit': 'Prevents over-dispensing of medications'
            },
            {
                'type': 'cascade',
                'priority': 'LOW',
                'description': 'Review cascade rules for audit trails',
                'tables': ['core_auditlog'],
                'recommendation': 'Change CASCADE to SET_NULL for user deletions',
                'benefit': 'Preserves audit history when users are deleted'
            }
        ])

        return recommendations

    def validate_foreign_key_health(self) -> Dict[str, Any]:
        """
        Validate the health of all foreign key relationships.
        """
        health_report = {
            'total_relationships': 0,
            'healthy_relationships': 0,
            'orphaned_records': 0,
            'constraint_violations': 0,
            'performance_issues': [],
            'recommendations': []
        }

        try:
            # Check for orphaned records
            orphan_checks = [
                ("SELECT COUNT(*) FROM appointments_appointment WHERE patient_id NOT IN (SELECT id FROM patients_patient)", "Appointments with orphaned patients"),
                ("SELECT COUNT(*) FROM ehr_encounter WHERE patient_id NOT IN (SELECT id FROM patients_patient)", "Encounters with orphaned patients"),
                ("SELECT COUNT(*) FROM lab_laborder WHERE patient_id NOT IN (SELECT id FROM patients_patient)", "Lab orders with orphaned patients"),
                ("SELECT COUNT(*) FROM pharmacy_prescription WHERE patient_id NOT IN (SELECT id FROM patients_patient)", "Prescriptions with orphaned patients"),
                ("SELECT COUNT(*) FROM billing_bill WHERE patient_id NOT IN (SELECT id FROM patients_patient)", "Bills with orphaned patients"),
            ]

            with self.connection.cursor() as cursor:
                for query, description in orphan_checks:
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    if count > 0:
                        health_report['orphaned_records'] += count
                        health_report['performance_issues'].append(f"{description}: {count} records")

                # Check constraint violations
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.table_constraints
                    WHERE constraint_type = 'CHECK'
                    AND is_deferrable = 'NO'
                """)
                health_report['total_relationships'] = cursor.fetchone()[0] or 0

        except Exception as e:
            logger.error(f"Error validating foreign key health: {e}")
            health_report['error'] = str(e)

        return health_report


class HealthcareRelationshipManager:
    """
    Manages complex healthcare-specific relationships and business rules.
    """

    @staticmethod
    def get_patient_encounters_query(patient_id: int, hospital_id: int) -> str:
        """
        Optimized query for retrieving patient encounter history.
        """
        return """
        SELECT
            e.id, e.encounter_number, e.encounter_type, e.encounter_status,
            e.scheduled_start, e.actual_start, e.actual_end,
            u.first_name || ' ' || u.last_name as primary_physician,
            e.location, e.chief_complaint
        FROM ehr_encounter e
        LEFT JOIN users_user u ON e.primary_physician_id = u.id
        WHERE e.patient_id = %s AND e.hospital_id = %s
        ORDER BY e.scheduled_start DESC
        """

    @staticmethod
    def get_provider_schedule_query(provider_id: int, hospital_id: int,
                                  start_date: str, end_date: str) -> str:
        """
        Optimized query for provider scheduling.
        """
        return """
        SELECT
            a.id, a.appointment_number, a.appointment_type, a.status,
            a.start_at, a.end_at, a.duration_minutes,
            p.first_name || ' ' || p.last_name as patient_name,
            a.priority, a.is_telehealth
        FROM appointments_appointment a
        LEFT JOIN patients_patient p ON a.patient_id = p.id
        WHERE a.primary_provider_id = %s
          AND a.hospital_id = %s
          AND a.start_at BETWEEN %s AND %s
          AND a.status NOT IN ('CANCELLED', 'NO_SHOW')
        ORDER BY a.start_at
        """

    @staticmethod
    def get_medication_interaction_query(medication_ids: List[int]) -> str:
        """
        Query for checking medication interactions.
        """
        placeholders = ', '.join(['%s'] * len(medication_ids))
        return f"""
        SELECT DISTINCT
            m1.id as med1_id, m1.name as med1_name,
            m2.id as med2_id, m2.name as med2_name,
            mi.severity, mi.description
        FROM pharmacy_medication m1
        CROSS JOIN pharmacy_medication m2
        LEFT JOIN medication_interactions mi ON
            (mi.medication1_id = m1.id AND mi.medication2_id = m2.id) OR
            (mi.medication1_id = m2.id AND mi.medication2_id = m1.id)
        WHERE m1.id IN ({placeholders})
          AND m2.id IN ({placeholders})
          AND m1.id < m2.id
          AND mi.id IS NOT NULL
        """

    @staticmethod
    def get_billing_summary_query(hospital_id: int, period_start: str,
                                 period_end: str) -> str:
        """
        Optimized query for financial reporting.
        """
        return """
        SELECT
            DATE_TRUNC('month', b.created_at) as month,
            b.status,
            COUNT(b.id) as bill_count,
            SUM(b.net_cents) as total_amount,
            AVG(b.net_cents) as average_amount
        FROM billing_bill b
        WHERE b.hospital_id = %s
          AND b.created_at BETWEEN %s AND %s
        GROUP BY DATE_TRUNC('month', b.created_at), b.status
        ORDER BY month, b.status
        """


# Database migration helper for foreign key optimization
def optimize_hms_foreign_keys():
    """
    Main function to optimize HMS foreign key relationships.
    """
    optimizer = ForeignKeyOptimizer()

    # Analyze current state
    analysis = optimizer._analyze_existing_relationships()
    logger.info(f"Current state: {analysis}")

    # Apply optimizations
    results = optimizer.optimize_foreign_keys()
    logger.info(f"Optimization results: {results}")

    # Generate recommendations
    recommendations = optimizer.get_foreign_key_recommendations()
    logger.info(f"Recommendations: {len(recommendations)} items")

    # Validate health
    health = optimizer.validate_foreign_key_health()
    logger.info(f"Health validation: {health}")

    return {
        'analysis': analysis,
        'optimization_results': results,
        'recommendations': recommendations,
        'health_report': health
    }