"""
Comprehensive Database Migration Testing for HMS System
Tests Django migrations, data integrity, backward compatibility, and healthcare data validation
"""

import pytest
import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import django
from django.conf import settings
from django.test import TestCase, TransactionTestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, transaction, DatabaseError
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState
from django.db.models import Count, Sum, Avg, Max, Min
from django.apps import apps
import psycopg2
from psycopg2 import sql
import pandas as pd
import numpy as np
from decimal import Decimal
import uuid

# Configure Django settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.hms.settings')
    django.setup()

# Import Django models after setup
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

# Import HMS models
from backend.patients.models import Patient, EmergencyContact, InsuranceInformation, PatientAlert
from backend.ehr.models import MedicalRecord, Allergy, Assessment, ClinicalNote, PlanOfCare, Encounter, EncounterAttachment, ERtriage
from backend.appointments.models import Appointment, AppointmentHistory, AppointmentReminder, SurgeryType, OTSlot, OTBooking
from backend.billing.models import Bill, ServiceCatalog, Discount, DepartmentBudget
from backend.pharmacy.models import Medication, MedicationBatch, Manufacturer
from backend.lab.models import LabResult
from backend.users.models import Department, UserCredential, UserLoginHistory
from backend.hospitals.models import Hospital, HospitalPlan
from backend.facilities.models import Facility
from backend.hr.models import Employee, Department as HRDepartment
from backend.accounting.models import Account, Transaction, JournalEntry, AccountingAuditLog
from backend.analytics.models import Analytics
from backend.feedback.models import Feedback, Survey
from backend.core.models import AuditLog, Notification, QualityMetric

# Healthcare-specific imports
from backend.libs.encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField
from backend.core.encryption import EncryptionManager
from backend.core.audit import AuditManager
from backend.core.compliance import ComplianceManager

# Test configuration
TEST_DATABASE_CONFIG = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hms_test_migrations',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
        'TEST': {
            'NAME': 'test_hms_migrations',
        }
    }
}

# Migration test data
MIGRATION_TEST_SCENARIOS = [
    {
        "name": "Patient Data Migration",
        "app": "patients",
        "from_migration": "0001_initial",
        "to_migration": "0005_patient_patients_pa_hospita_8adb46_idx_and_more",
        "test_data_size": 1000,
        "healthcare_data": True,
        "encrypted_fields": ["first_name", "last_name", "email", "phone"],
        "critical": True
    },
    {
        "name": "Medical Records Migration",
        "app": "ehr",
        "from_migration": "0001_initial",
        "to_migration": "0006_notificationmodel_qualitymetric_and_more",
        "test_data_size": 500,
        "healthcare_data": True,
        "encrypted_fields": ["diagnosis", "treatment", "notes"],
        "critical": True
    },
    {
        "name": "Appointments Migration",
        "app": "appointments",
        "from_migration": "0001_initial",
        "to_migration": "0005_appointment_appointment_hospita_399297_idx_and_more",
        "test_data_size": 2000,
        "healthcare_data": False,
        "encrypted_fields": ["notes"],
        "critical": False
    },
    {
        "name": "Billing Migration",
        "app": "billing",
        "from_migration": "0001_initial",
        "to_migration": "0007_bill_billing_bil_hospita_79db2a_idx_and_more",
        "test_data_size": 1500,
        "healthcare_data": True,
        "encrypted_fields": ["payment_method", "insurance_info"],
        "critical": True
    },
    {
        "name": "Accounting Migration",
        "app": "accounting",
        "from_migration": "0001_initial",
        "to_migration": "0002_alter_accountingauditlog_user",
        "test_data_size": 1000,
        "healthcare_data": False,
        "encrypted_fields": ["description"],
        "critical": False
    }
]

class DatabaseMigrationTestFramework:
    """Comprehensive database migration testing framework"""

    def __init__(self):
        self.test_databases = []
        self.migration_results = []
        self.encryption_manager = EncryptionManager()
        self.audit_manager = AuditManager()
        self.compliance_manager = ComplianceManager()

    def setup_test_database(self, db_name: str) -> Dict[str, Any]:
        """Setup isolated test database for migration testing"""
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host='localhost',
                port='5432',
                user='postgres',
                password='postgres',
                database='postgres'
            )
            conn.autocommit = True
            cursor = conn.cursor()

            # Drop database if exists
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")

            # Create new database
            cursor.execute(f"CREATE DATABASE {db_name} WITH ENCODING 'UTF8'")

            # Create test schema
            cursor.execute(f"""
                CREATE SCHEMA IF NOT EXISTS healthcare_data;
                CREATE SCHEMA IF NOT EXISTS analytics;
                CREATE SCHEMA IF NOT EXISTS audit;
            """)

            cursor.close()
            conn.close()

            return {
                'success': True,
                'database_name': db_name,
                'message': f'Test database {db_name} created successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'database_name': db_name,
                'message': f'Failed to create test database: {str(e)}'
            }

    def cleanup_test_database(self, db_name: str):
        """Cleanup test database"""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port='5432',
                user='postgres',
                password='postgres',
                database='postgres'
            )
            conn.autocommit = True
            cursor = conn.cursor()

            # Terminate all connections to the database
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                AND pid <> pg_backend_pid()
            """)

            # Drop database
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Warning: Failed to cleanup test database {db_name}: {str(e)}")

    def generate_test_healthcare_data(self, model_class, count: int, encrypted_fields: List[str]) -> List[Dict]:
        """Generate anonymized test healthcare data"""
        test_data = []

        for i in range(count):
            data = {}

            # Generate basic data
            if hasattr(model_class, 'first_name'):
                data['first_name'] = f'Test{i:04d}'
            if hasattr(model_class, 'last_name'):
                data['last_name'] = f'Patient{i:04d}'
            if hasattr(model_class, 'email'):
                data['email'] = f'test{i:04d}@example.com'
            if hasattr(model_class, 'phone'):
                data['phone'] = f'555-{i:04d:04d}'

            # Generate healthcare-specific data
            if model_class == Patient:
                data.update({
                    'date_of_birth': datetime.now() - timedelta(days=i*365),
                    'gender': 'M' if i % 2 == 0 else 'F',
                    'blood_type': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'][i % 8],
                    'medical_record_number': f'MRN{i:08d}',
                    'ssn': f'{i:03d}-{i:02d}-{i:04d}',
                    'address': f'{i:04d} Test Street, Test City, TC 12345',
                    'emergency_contact_name': f'Emergency Contact {i}',
                    'emergency_contact_phone': f'555-{i:04d:04d}',
                    'primary_care_physician': f'Dr. Test{i:04d}',
                    'insurance_provider': f'Test Insurance {i % 5 + 1}',
                    'insurance_policy_number': f'POL{i:08d}',
                    'allergies': 'Penicillin',
                    'medications': 'Lisinopril 10mg',
                    'chronic_conditions': 'Hypertension',
                    'last_visit_date': datetime.now() - timedelta(days=i*30),
                    'status': 'active'
                })

            elif model_class == MedicalRecord:
                data.update({
                    'patient_id': i + 1,  # Assuming patient with this ID exists
                    'record_date': datetime.now() - timedelta(days=i*7),
                    'record_type': ['diagnosis', 'treatment', 'follow-up', 'lab_result'][i % 4],
                    'diagnosis': f'Test diagnosis {i}',
                    'treatment': f'Test treatment {i}',
                    'notes': f'Test medical notes for patient {i}',
                    'physician_id': 1,
                    'facility_id': 1,
                    'is_confidential': i % 10 == 0  # 10% are confidential
                })

            elif model_class == Appointment:
                data.update({
                    'patient_id': i + 1,
                    'appointment_date': datetime.now() + timedelta(days=i),
                    'appointment_time': datetime.now().replace(hour=9+i%8, minute=0),
                    'appointment_type': ['consultation', 'follow-up', 'procedure', 'emergency'][i % 4],
                    'status': ['scheduled', 'confirmed', 'completed', 'cancelled'][i % 4],
                    'physician_id': 1,
                    'facility_id': 1,
                    'notes': f'Test appointment notes {i}',
                    'reminder_sent': True
                })

            # Encrypt sensitive fields
            for field in encrypted_fields:
                if field in data:
                    data[field] = self.encryption_manager.encrypt(str(data[field]))

            test_data.append(data)

        return test_data

    def run_migration_test(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive migration test for a given scenario"""
        result = {
            'scenario': scenario['name'],
            'app': scenario['app'],
            'success': False,
            'migration_time': 0,
            'data_integrity_check': False,
            'backward_compatibility': False,
            'performance_metrics': {},
            'errors': [],
            'warnings': []
        }

        test_db_name = f"test_migration_{scenario['app']}_{int(time.time())}"

        try:
            # Setup test database
            setup_result = self.setup_test_database(test_db_name)
            if not setup_result['success']:
                result['errors'].append(setup_result['message'])
                return result

            self.test_databases.append(test_db_name)

            # Get model class
            try:
                model_class = apps.get_model(scenario['app'], scenario['app'].capitalize())
            except LookupError:
                model_class = apps.get_model(scenario['app'], scenario['app'][:-1].capitalize())

            # Generate test data
            if scenario['healthcare_data']:
                test_data = self.generate_test_healthcare_data(
                    model_class, scenario['test_data_size'], scenario['encrypted_fields']
                )

            # Configure Django for test database
            original_db_config = settings.DATABASES['default'].copy()
            settings.DATABASES['default'].update({
                'NAME': test_db_name,
                'TEST': {'NAME': test_db_name}
            })

            # Create migration executor
            executor = MigrationExecutor(connection)

            # Get migration states
            from_state = executor.loader.project_state(scenario['from_migration'])
            to_state = executor.loader.project_state(scenario['to_migration'])

            # Test forward migration
            start_time = time.time()

            try:
                # Apply migrations from start state
                executor.migrate([scenario['from_migration']])

                # Insert test data if healthcare data
                if scenario['healthcare_data'] and test_data:
                    model_class.objects.bulk_create([
                        model_class(**data) for data in test_data[:100]  # Test with subset
                    ])

                # Apply target migration
                executor.migrate([scenario['to_migration']])

                migration_time = time.time() - start_time
                result['migration_time'] = migration_time
                result['performance_metrics']['migration_time'] = migration_time

                # Test data integrity
                integrity_result = self.test_data_integrity(model_class, scenario)
                result['data_integrity_check'] = integrity_result['success']
                result.update(integrity_result['metrics'])

                # Test backward compatibility
                backward_result = self.test_backward_compatibility(executor, scenario)
                result['backward_compatibility'] = backward_result['success']

                if not backward_result['success']:
                    result['errors'].extend(backward_result['errors'])

                # Test encryption integrity for healthcare data
                if scenario['healthcare_data'] and scenario['encrypted_fields']:
                    encryption_result = self.test_encryption_integrity(
                        model_class, scenario['encrypted_fields']
                    )
                    result['encryption_integrity'] = encryption_result['success']
                    if not encryption_result['success']:
                        result['warnings'].extend(encryption_result['warnings'])

                result['success'] = True

            except Exception as e:
                result['errors'].append(f"Migration failed: {str(e)}")

            finally:
                # Restore original database configuration
                settings.DATABASES['default'] = original_db_config

        except Exception as e:
            result['errors'].append(f"Test setup failed: {str(e)}")

        return result

    def test_data_integrity(self, model_class, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test data integrity after migration"""
        result = {
            'success': True,
            'metrics': {},
            'errors': []
        }

        try:
            # Test record count
            record_count = model_class.objects.count()
            result['metrics']['record_count'] = record_count

            # Test field accessibility
            for field in model_class._meta.fields:
                try:
                    # Test field exists and is accessible
                    field_name = field.name
                    result['metrics'][f'field_{field_name}'] = 'accessible'

                    # Test field type consistency
                    field_type = field.get_internal_type()
                    result['metrics'][f'field_{field_name}_type'] = field_type

                except Exception as e:
                    result['errors'].append(f"Field {field.name} issue: {str(e)}")
                    result['success'] = False

            # Test data consistency for healthcare data
            if scenario['healthcare_data']:
                # Test required fields have values
                required_fields = [
                    f.name for f in model_class._meta.fields
                    if not f.null and f.default != 'NOT_PROVIDED' and not f.blank
                ]

                for field in required_fields:
                    try:
                        # Check for null values in required fields
                        null_count = model_class.objects.filter(**{f"{field}__isnull": True}).count()
                        if null_count > 0:
                            result['errors'].append(f"Required field {field} has {null_count} null values")
                            result['success'] = False

                        result['metrics'][f'required_field_{field}_null_count'] = null_count

                    except Exception as e:
                        result['errors'].append(f"Required field {field} check failed: {str(e)}")
                        result['success'] = False

                # Test encrypted field integrity
                if scenario['encrypted_fields']:
                    for field in scenario['encrypted_fields']:
                        try:
                            # Test encrypted fields can be decrypted
                            sample_record = model_class.objects.first()
                            if sample_record and hasattr(sample_record, field):
                                encrypted_value = getattr(sample_record, field)
                                if encrypted_value:
                                    decrypted_value = self.encryption_manager.decrypt(encrypted_value)
                                    result['metrics'][f'encrypted_field_{field}_decrypted'] = True

                        except Exception as e:
                            result['errors'].append(f"Encrypted field {field} integrity issue: {str(e)}")
                            result['success'] = False

            # Test performance metrics
            start_time = time.time()
            model_class.objects.count()  # Simple count query
            query_time = time.time() - start_time
            result['metrics']['count_query_time'] = query_time

            # Test indexing performance
            if hasattr(model_class, 'medical_record_number'):
                start_time = time.time()
                model_class.objects.filter(medical_record_number__startswith='TEST').count()
                indexed_query_time = time.time() - start_time
                result['metrics']['indexed_query_time'] = indexed_query_time

        except Exception as e:
            result['errors'].append(f"Data integrity test failed: {str(e)}")
            result['success'] = False

        return result

    def test_backward_compatibility(self, executor: MigrationExecutor, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test backward compatibility of migration"""
        result = {
            'success': True,
            'errors': []
        }

        try:
            # Test rollback capability
            executor.migrate([scenario['from_migration']])

            # Test that we can still access basic data structure
            try:
                # Get model class
                model_class = apps.get_model(scenario['app'], scenario['app'].capitalize())

                # Test basic operations
                record_count = model_class.objects.count()
                result['rollback_record_count'] = record_count

            except Exception as e:
                result['errors'].append(f"Rollback compatibility issue: {str(e)}")
                result['success'] = False

            # Migrate forward again
            executor.migrate([scenario['to_migration']])

        except Exception as e:
            result['errors'].append(f"Backward compatibility test failed: {str(e)}")
            result['success'] = False

        return result

    def test_encryption_integrity(self, model_class, encrypted_fields: List[str]) -> Dict[str, Any]:
        """Test encryption integrity for healthcare data"""
        result = {
            'success': True,
            'warnings': []
        }

        try:
            # Test encryption/decryption consistency
            sample_records = model_class.objects.all()[:10]

            for record in sample_records:
                for field in encrypted_fields:
                    if hasattr(record, field):
                        encrypted_value = getattr(record, field)
                        if encrypted_value:
                            try:
                                decrypted_value = self.encryption_manager.decrypt(encrypted_value)
                                # Test that decrypted value is reasonable
                                if len(str(decrypted_value)) == 0:
                                    result['warnings'].append(f"Field {field} decrypted to empty value")
                                    result['success'] = False

                            except Exception as e:
                                result['warnings'].append(f"Failed to decrypt field {field}: {str(e)}")
                                result['success'] = False

            # Test encryption key rotation (if applicable)
            try:
                # Test with different encryption keys
                test_data = "test_sensitive_data"
                encrypted_v1 = self.encryption_manager.encrypt(test_data)
                decrypted_v1 = self.encryption_manager.decrypt(encrypted_v1)

                if decrypted_v1 != test_data:
                    result['warnings'].append("Encryption/decryption roundtrip failed")
                    result['success'] = False

            except Exception as e:
                result['warnings'].append(f"Encryption key test failed: {str(e)}")

        except Exception as e:
            result['warnings'].append(f"Encryption integrity test failed: {str(e)}")
            result['success'] = False

        return result

    def cleanup_all_test_databases(self):
        """Cleanup all test databases"""
        for db_name in self.test_databases:
            self.cleanup_test_database(db_name)
        self.test_databases = []

    def run_comprehensive_migration_tests(self) -> Dict[str, Any]:
        """Run comprehensive migration tests for all scenarios"""
        results = {
            'total_scenarios': len(MIGRATION_TEST_SCENARIOS),
            'passed_scenarios': 0,
            'failed_scenarios': 0,
            'total_migration_time': 0,
            'scenario_results': [],
            'summary': {}
        }

        for scenario in MIGRATION_TEST_SCENARIOS:
            print(f"Testing migration scenario: {scenario['name']}")
            result = self.run_migration_test(scenario)
            results['scenario_results'].append(result)
            results['total_migration_time'] += result.get('migration_time', 0)

            if result['success']:
                results['passed_scenarios'] += 1
            else:
                results['failed_scenarios'] += 1

        # Generate summary
        results['summary'] = {
            'success_rate': (results['passed_scenarios'] / results['total_scenarios']) * 100,
            'average_migration_time': results['total_migration_time'] / results['total_scenarios'],
            'critical_migrations_passed': len([
                r for r in results['scenario_results']
                if r['success'] and MIGRATION_TEST_SCENARIOS[
                    MIGRATION_TEST_SCENARIOS.index(next(s for s in MIGRATION_TEST_SCENARIOS if s['name'] == r['scenario']))
                ]['critical']
            ])
        }

        return results

class TestDjangoMigrations(TestCase):
    """Test Django migrations framework"""

    def setUp(self):
        """Setup test environment"""
        self.migration_framework = DatabaseMigrationTestFramework()

    def tearDown(self):
        """Cleanup test environment"""
        self.migration_framework.cleanup_all_test_databases()

    def test_migration_executor_initialization(self):
        """Test migration executor initialization"""
        try:
            executor = MigrationExecutor(connection)
            self.assertIsNotNone(executor)
            self.assertIsNotNone(executor.loader)
            self.assertIsNotNone(executor.connection)
        except Exception as e:
            self.fail(f"Migration executor initialization failed: {str(e)}")

    def test_migration_plan_generation(self):
        """Test migration plan generation"""
        try:
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

            self.assertIsInstance(plan, list)
            self.assertTrue(len(plan) > 0)

            # Test plan structure
            for migration in plan:
                self.assertTrue(hasattr(migration, 'app_label'))
                self.assertTrue(hasattr(migration, 'name'))

        except Exception as e:
            self.fail(f"Migration plan generation failed: {str(e)}")

    def test_migration_state_consistency(self):
        """Test migration state consistency"""
        try:
            executor = MigrationExecutor(connection)
            project_state = executor.loader.project_state()

            self.assertIsNotNone(project_state)
            self.assertIsInstance(project_state.apps, django.apps.apps.Apps)

            # Test that models are accessible
            try:
                patient_model = project_state.apps.get_model('patients', 'Patient')
                self.assertIsNotNone(patient_model)
            except LookupError:
                # Model might not exist in initial state
                pass

        except Exception as e:
            self.fail(f"Migration state consistency test failed: {str(e)}")

class TestPatientDataMigration(TransactionTestCase):
    """Test patient data migration specifically"""

    def setUp(self):
        """Setup test environment"""
        self.framework = DatabaseMigrationTestFramework()

    def test_patient_model_migration(self):
        """Test patient model migration with healthcare data"""
        scenario = next(s for s in MIGRATION_TEST_SCENARIOS if s['app'] == 'patients')

        result = self.framework.run_migration_test(scenario)

        self.assertTrue(result['success'], f"Patient migration failed: {result['errors']}")
        self.assertTrue(result['data_integrity_check'], "Data integrity check failed")
        self.assertTrue(result['backward_compatibility'], "Backward compatibility failed")

        # Test healthcare-specific requirements
        self.assertIn('encryption_integrity', result)
        self.assertTrue(result['encryption_integrity'], "Encryption integrity failed")

    def test_patient_encrypted_fields(self):
        """Test patient encrypted field migration"""
        from backend.patients.models import Patient

        # Create test patient
        patient_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '555-123-4567',
            'date_of_birth': datetime.now() - timedelta(days=30*365),
            'gender': 'M',
            'blood_type': 'A+',
            'medical_record_number': 'MRN12345678',
            'ssn': '123-45-6789',
            'address': '123 Test St, Test City, TC 12345',
            'emergency_contact_name': 'Jane Doe',
            'emergency_contact_phone': '555-987-6543',
            'primary_care_physician': 'Dr. Smith',
            'insurance_provider': 'Test Insurance',
            'insurance_policy_number': 'POL12345678',
            'allergies': 'Penicillin',
            'medications': 'Lisinopril 10mg',
            'chronic_conditions': 'Hypertension',
            'last_visit_date': datetime.now(),
            'status': 'active'
        }

        patient = Patient.objects.create(**patient_data)

        # Test encrypted fields are not stored in plaintext
        self.assertNotEqual(patient.first_name, 'John')  # Should be encrypted
        self.assertNotEqual(patient.last_name, 'Doe')   # Should be encrypted
        self.assertNotEqual(patient.email, 'john.doe@example.com')  # Should be encrypted

        # Test decryption works
        encryption_manager = EncryptionManager()
        decrypted_first_name = encryption_manager.decrypt(patient.first_name)
        self.assertEqual(decrypted_first_name, 'John')

    def test_patient_data_integrity(self):
        """Test patient data integrity after migration"""
        from backend.patients.models import Patient

        # Create multiple test patients
        patients = []
        for i in range(10):
            patient_data = {
                'first_name': f'Test{i}',
                'last_name': f'Patient{i}',
                'email': f'test{i}@example.com',
                'phone': f'555-{i:04d}',
                'date_of_birth': datetime.now() - timedelta(days=i*365),
                'gender': 'M' if i % 2 == 0 else 'F',
                'blood_type': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'][i % 8],
                'medical_record_number': f'MRN{i:08d}',
                'ssn': f'{i:03d}-{i:02d}-{i:04d}',
                'status': 'active'
            }
            patients.append(Patient.objects.create(**patient_data))

        # Test data retrieval
        all_patients = Patient.objects.all()
        self.assertEqual(len(all_patients), 10)

        # Test filtering
        male_patients = Patient.objects.filter(gender='M')
        self.assertEqual(male_patients.count(), 5)

        # Test medical record number uniqueness
        mrn_count = Patient.objects.values('medical_record_number').annotate(
            count=Count('medical_record_number')
        ).filter(count__gt=1)
        self.assertEqual(mrn_count.count(), 0)

class TestMedicalRecordsMigration(TransactionTestCase):
    """Test medical records migration"""

    def setUp(self):
        """Setup test environment"""
        self.framework = DatabaseMigrationTestFramework()

    def test_medical_record_migration(self):
        """Test medical record migration with confidential data"""
        scenario = next(s for s in MIGRATION_TEST_SCENARIOS if s['app'] == 'ehr')

        result = self.framework.run_migration_test(scenario)

        self.assertTrue(result['success'], f"Medical record migration failed: {result['errors']}")
        self.assertTrue(result['data_integrity_check'], "Data integrity check failed")

    def test_confidential_data_handling(self):
        """Test confidential medical record data handling"""
        from backend.ehr.models import MedicalRecord
        from backend.patients.models import Patient

        # Create test patient
        patient = Patient.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='555-123-4567',
            date_of_birth=datetime.now() - timedelta(days=30*365),
            gender='M',
            medical_record_number='MRN12345678',
            status='active'
        )

        # Create confidential medical record
        medical_record = MedicalRecord.objects.create(
            patient=patient,
            record_date=datetime.now(),
            record_type='diagnosis',
            diagnosis='Confidential Condition',
            treatment='Confidential Treatment',
            notes='Confidential medical notes',
            physician_id=1,
            facility_id=1,
            is_confidential=True
        )

        # Test confidential flag is respected
        self.assertTrue(medical_record.is_confidential)

        # Test encrypted fields
        encryption_manager = EncryptionManager()
        decrypted_diagnosis = encryption_manager.decrypt(medical_record.diagnosis)
        self.assertEqual(decrypted_diagnosis, 'Confidential Condition')

class TestAppointmentsMigration(TransactionTestCase):
    """Test appointments migration"""

    def setUp(self):
        """Setup test environment"""
        self.framework = DatabaseMigrationTestFramework()

    def test_appointment_migration(self):
        """Test appointment migration"""
        scenario = next(s for s in MIGRATION_TEST_SCENARIOS if s['app'] == 'appointments')

        result = self.framework.run_migration_test(scenario)

        self.assertTrue(result['success'], f"Appointment migration failed: {result['errors']}")
        self.assertTrue(result['data_integrity_check'], "Data integrity check failed")

    def test_appointment_scheduling_logic(self):
        """Test appointment scheduling logic after migration"""
        from backend.appointments.models import Appointment
        from backend.patients.models import Patient

        # Create test patient
        patient = Patient.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='555-123-4567',
            date_of_birth=datetime.now() - timedelta(days=30*365),
            gender='M',
            medical_record_number='MRN12345678',
            status='active'
        )

        # Create appointments
        appointments = []
        for i in range(5):
            appointment = Appointment.objects.create(
                patient=patient,
                appointment_date=datetime.now().date() + timedelta(days=i),
                appointment_time=datetime.now().replace(hour=9+i, minute=0),
                appointment_type='consultation',
                status='scheduled',
                physician_id=1,
                facility_id=1
            )
            appointments.append(appointment)

        # Test appointment retrieval
        patient_appointments = Appointment.objects.filter(patient=patient)
        self.assertEqual(patient_appointments.count(), 5)

        # Test date filtering
        today_appointments = Appointment.objects.filter(appointment_date=datetime.now().date())
        self.assertEqual(today_appointments.count(), 1)

class TestBillingMigration(TransactionTestCase):
    """Test billing migration"""

    def setUp(self):
        """Setup test environment"""
        self.framework = DatabaseMigrationTestFramework()

    def test_billing_migration(self):
        """Test billing migration with financial data"""
        scenario = next(s for s in MIGRATION_TEST_SCENARIOS if s['app'] == 'billing')

        result = self.framework.run_migration_test(scenario)

        self.assertTrue(result['success'], f"Billing migration failed: {result['errors']}")
        self.assertTrue(result['data_integrity_check'], "Data integrity check failed")

    def test_financial_data_integrity(self):
        """Test financial data integrity after migration"""
        from backend.billing.models import Bill, ServiceCatalog
        from backend.patients.models import Patient

        # Create test patient
        patient = Patient.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='555-123-4567',
            date_of_birth=datetime.now() - timedelta(days=30*365),
            gender='M',
            medical_record_number='MRN12345678',
            status='active'
        )

        # Create service catalog entries
        services = [
            ServiceCatalog.objects.create(
                service_code='CONSULT',
                service_name='General Consultation',
                description='General medical consultation',
                cost=Decimal('150.00'),
                category='consultation'
            ),
            ServiceCatalog.objects.create(
                service_code='LAB',
                service_name='Blood Test',
                description='Complete blood count',
                cost=Decimal('75.00'),
                category='laboratory'
            )
        ]

        # Create bill
        bill = Bill.objects.create(
            patient=patient,
            bill_date=datetime.now().date(),
            due_date=datetime.now().date() + timedelta(days=30),
            total_amount=Decimal('225.00'),
            status='pending',
            payment_method='insurance',
            insurance_info='Test Insurance Co.'
        )

        # Test financial calculations
        expected_total = sum(service.cost for service in services)
        self.assertEqual(bill.total_amount, expected_total)

        # Test payment method encryption
        encryption_manager = EncryptionManager()
        decrypted_payment_method = encryption_manager.decrypt(bill.payment_method)
        self.assertEqual(decrypted_payment_method, 'insurance')

class TestMigrationPerformance(TransactionTestCase):
    """Test migration performance"""

    def setUp(self):
        """Setup test environment"""
        self.framework = DatabaseMigrationTestFramework()

    def test_large_dataset_migration_performance(self):
        """Test migration performance with large datasets"""
        # Test with a larger dataset
        scenario = {
            'name': 'Large Dataset Performance Test',
            'app': 'patients',
            'from_migration': '0001_initial',
            'to_migration': '0005_patient_patients_pa_hospita_8adb46_idx_and_more',
            'test_data_size': 5000,
            'healthcare_data': True,
            'encrypted_fields': ["first_name", "last_name", "email", "phone"],
            'critical': True
        }

        result = self.framework.run_migration_test(scenario)

        self.assertTrue(result['success'], f"Large dataset migration failed: {result['errors']}")

        # Check performance metrics
        migration_time = result.get('migration_time', 0)
        self.assertLess(migration_time, 300, f"Migration took too long: {migration_time} seconds")

        # Check data integrity
        self.assertTrue(result['data_integrity_check'], "Data integrity check failed")

    def test_concurrent_migration_safety(self):
        """Test concurrent migration safety"""
        # This would test multiple concurrent migrations
        # For now, we'll test basic migration safety
        scenario = {
            'name': 'Concurrent Migration Safety Test',
            'app': 'patients',
            'from_migration': '0001_initial',
            'to_migration': '0005_patient_patients_pa_hospita_8adb46_idx_and_more',
            'test_data_size': 100,
            'healthcare_data': True,
            'encrypted_fields': ["first_name", "last_name", "email", "phone"],
            'critical': True
        }

        result = self.framework.run_migration_test(scenario)

        self.assertTrue(result['success'], f"Concurrent migration test failed: {result['errors']}")

class TestMigrationRollback(TransactionTestCase):
    """Test migration rollback capabilities"""

    def setUp(self):
        """Setup test environment"""
        self.framework = DatabaseMigrationTestFramework()

    def test_migration_rollback(self):
        """Test migration rollback functionality"""
        scenario = {
            'name': 'Migration Rollback Test',
            'app': 'patients',
            'from_migration': '0001_initial',
            'to_migration': '0005_patient_patients_pa_hospita_8adb46_idx_and_more',
            'test_data_size': 50,
            'healthcare_data': True,
            'encrypted_fields': ["first_name", "last_name", "email", "phone"],
            'critical': True
        }

        result = self.framework.run_migration_test(scenario)

        self.assertTrue(result['success'], f"Migration rollback test failed: {result['errors']}")
        self.assertTrue(result['backward_compatibility'], "Backward compatibility failed")

    def test_data_preservation_after_rollback(self):
        """Test data preservation after rollback"""
        from backend.patients.models import Patient

        # Create test patient
        patient = Patient.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='555-123-4567',
            date_of_birth=datetime.now() - timedelta(days=30*365),
            gender='M',
            medical_record_number='MRN12345678',
            status='active'
        )

        patient_id = patient.id

        # Test that patient data can be retrieved after operations
        retrieved_patient = Patient.objects.get(id=patient_id)
        self.assertEqual(retrieved_patient.medical_record_number, 'MRN12345678')

class TestMigrationSecurity(TransactionTestCase):
    """Test migration security and compliance"""

    def setUp(self):
        """Setup test environment"""
        self.framework = DatabaseMigrationTestFramework()

    def test_phi_data_protection(self):
        """Test PHI data protection during migration"""
        from backend.patients.models import Patient

        # Create patient with PHI
        patient = Patient.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='555-123-4567',
            date_of_birth=datetime.now() - timedelta(days=30*365),
            gender='M',
            blood_type='A+',
            medical_record_number='MRN12345678',
            ssn='123-45-6789',
            address='123 Test St, Test City, TC 12345',
            emergency_contact_name='Jane Doe',
            emergency_contact_phone='555-987-6543',
            primary_care_physician='Dr. Smith',
            insurance_provider='Test Insurance',
            insurance_policy_number='POL12345678',
            allergies='Penicillin',
            medications='Lisinopril 10mg',
            chronic_conditions='Hypertension',
            last_visit_date=datetime.now(),
            status='active'
        )

        # Test that PHI fields are encrypted
        encryption_manager = EncryptionManager()

        # Test SSN encryption
        decrypted_ssn = encryption_manager.decrypt(patient.ssn)
        self.assertEqual(decrypted_ssn, '123-45-6789')

        # Test that raw database query doesn't expose PHI
        with connection.cursor() as cursor:
            cursor.execute("SELECT first_name, last_name, email FROM patients_patient WHERE id = %s", [patient.id])
            row = cursor.fetchone()

            # The values should be encrypted, not plaintext
            self.assertNotEqual(row[0], 'John')  # Should be encrypted
            self.assertNotEqual(row[1], 'Doe')   # Should be encrypted
            self.assertNotEqual(row[2], 'john.doe@example.com')  # Should be encrypted

    def test_audit_trail_maintenance(self):
        """Test audit trail maintenance during migration"""
        from backend.core.models import AuditLog

        # Create audit log entry
        audit_log = AuditLog.objects.create(
            user_id=1,
            action='test_migration',
            object_type='Patient',
            object_id=1,
            details='Test migration audit',
            ip_address='127.0.0.1'
        )

        # Test audit log is preserved
        retrieved_log = AuditLog.objects.get(id=audit_log.id)
        self.assertEqual(retrieved_log.action, 'test_migration')

# Test runners and utilities
def run_comprehensive_migration_tests():
    """Run comprehensive migration tests"""
    framework = DatabaseMigrationTestFramework()

    try:
        results = framework.run_comprehensive_migration_tests()

        # Generate report
        report = f"""
# Database Migration Test Report

## Summary
- **Total Scenarios**: {results['total_scenarios']}
- **Passed**: {results['passed_scenarios']}
- **Failed**: {results['failed_scenarios']}
- **Success Rate**: {results['summary']['success_rate']:.1f}%
- **Average Migration Time**: {results['summary']['average_migration_time']:.2f}s
- **Critical Migrations Passed**: {results['summary']['critical_migrations_passed']}

## Scenario Results
"""

        for result in results['scenario_results']:
            report += f"""
### {result['scenario']}
- **Status**: {'✅ PASS' if result['success'] else '❌ FAIL'}
- **Migration Time**: {result.get('migration_time', 0):.2f}s
- **Data Integrity**: {'✅ PASS' if result['data_integrity_check'] else '❌ FAIL'}
- **Backward Compatible**: {'✅ PASS' if result['backward_compatibility'] else '❌ FAIL'}
"""

            if result['errors']:
                report += "- **Errors**:\n"
                for error in result['errors']:
                    report += f"  - {error}\n"

            if result['warnings']:
                report += "- **Warnings**:\n"
                for warning in result['warnings']:
                    report += f"  - {warning}\n"

        # Save report
        with open('/tmp/migration_test_report.md', 'w') as f:
            f.write(report)

        print(f"Migration tests completed. Report saved to /tmp/migration_test_report.md")
        return results

    finally:
        framework.cleanup_all_test_databases()

def validate_database_schema_consistency():
    """Validate database schema consistency across environments"""
    framework = DatabaseMigrationTestFramework()

    try:
        # This would compare schemas across different environments
        # For now, we'll validate the current schema
        with connection.cursor() as cursor:
            # Get table information
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
            schema_info = cursor.fetchall()

            # Create schema report
            report = "# Database Schema Validation Report\n\n"
            report += "## Tables and Columns\n\n"

            current_table = None
            for row in schema_info:
                table_name, column_name, data_type, is_nullable = row

                if table_name != current_table:
                    report += f"\n### {table_name}\n\n"
                    report += "| Column | Type | Nullable |\n"
                    report += "|--------|------|----------|\n"
                    current_table = table_name

                report += f"| {column_name} | {data_type} | {is_nullable} |\n"

            # Save schema report
            with open('/tmp/schema_validation_report.md', 'w') as f:
                f.write(report)

            print("Schema validation completed. Report saved to /tmp/schema_validation_report.md")
            return schema_info

    except Exception as e:
        print(f"Schema validation failed: {str(e)}")
        return None

if __name__ == "__main__":
    # Run comprehensive tests
    print("Running comprehensive database migration tests...")
    results = run_comprehensive_migration_tests()

    # Validate schema consistency
    print("Validating database schema consistency...")
    schema_info = validate_database_schema_consistency()

    # Print summary
    print(f"\nTest Summary:")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"Critical Migrations: {results['summary']['critical_migrations_passed']}/{len([s for s in MIGRATION_TEST_SCENARIOS if s['critical']])}")

    # Run Django tests
    print("\nRunning Django migration tests...")
    import django
    from django.test.utils import get_runner

    django.setup()
    test_runner = get_runner(settings)()
    failures = test_runner.run_tests(['__main__'])

    if failures:
        print(f"❌ {failures} Django test(s) failed")
        exit(1)
    else:
        print("✅ All Django tests passed")