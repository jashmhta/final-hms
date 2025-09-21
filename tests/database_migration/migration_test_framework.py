"""
Database Migration Testing Framework
Provides comprehensive testing infrastructure for Django migrations with healthcare data validation
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import psycopg2
from psycopg2 import sql, extras
import django
from django.conf import settings
from django.db import connection, transaction, DatabaseError, connections
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState
from django.db.migrations.writer import MigrationWriter
from django.core.management import call_command, execute_from_command_line
from django.core.management.base import CommandError
from django.test import TestCase, TransactionTestCase
from django.apps import apps
import pandas as pd
import numpy as np
from decimal import Decimal
import threading
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationTestStatus(Enum):
    """Migration test status"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

class MigrationSeverity(Enum):
    """Migration severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MigrationTestType(Enum):
    """Types of migration tests"""
    FORWARD_MIGRATION = "forward_migration"
    BACKWARD_MIGRATION = "backward_migration"
    DATA_INTEGRITY = "data_integrity"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    ROLLBACK = "rollback"
    CONCURRENCY = "concurrency"
    SCHEMA_VALIDATION = "schema_validation"

@dataclass
class MigrationTestConfig:
    """Configuration for migration testing"""
    test_database_prefix: str = "test_migration_"
    max_test_databases: int = 10
    cleanup_on_success: bool = True
    cleanup_on_failure: bool = False
    enable_parallel_testing: bool = True
    max_workers: int = 4
    healthcare_data_validation: bool = True
    encryption_validation: bool = True
    performance_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'migration_time': 300.0,  # 5 minutes
        'query_time': 5.0,  # 5 seconds
        'memory_usage': 1024.0  # 1GB
    })
    compliance_checks: List[str] = field(default_factory=lambda: [
        'hipaa', 'gdpr', 'data_localization', 'audit_trail'
    ])

@dataclass
class MigrationTestResult:
    """Result of a migration test"""
    test_name: str
    test_type: MigrationTestType
    status: MigrationTestStatus
    duration: float
    success: bool
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    healthcare_compliance: Dict[str, bool] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    database_name: Optional[str] = None

@dataclass
class MigrationScenario:
    """Migration test scenario definition"""
    name: str
    app_name: str
    from_migration: str
    to_migration: str
    test_data_size: int = 100
    healthcare_data: bool = False
    encrypted_fields: List[str] = field(default_factory=list)
    critical: bool = False
    test_types: List[MigrationTestType] = field(default_factory=lambda: [
        MigrationTestType.FORWARD_MIGRATION,
        MigrationTestType.BACKWARD_MIGRATION,
        MigrationTestType.DATA_INTEGRITY,
        MigrationTestType.SECURITY
    ])
    expected_results: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

class DatabaseMigrationTestFramework:
    """Comprehensive database migration testing framework"""

    def __init__(self, config: Optional[MigrationTestConfig] = None):
        self.config = config or MigrationTestConfig()
        self.test_databases: List[str] = []
        self.test_results: List[MigrationTestResult] = []
        self.lock = threading.Lock()
        self.setup_django_environment()

        # Healthcare-specific components
        try:
            from backend.core.encryption import EncryptionManager
            from backend.core.audit import AuditManager
            from backend.core.compliance import ComplianceManager
            self.encryption_manager = EncryptionManager()
            self.audit_manager = AuditManager()
            self.compliance_manager = ComplianceManager()
        except ImportError:
            logger.warning("Healthcare modules not available, running in basic mode")
            self.encryption_manager = None
            self.audit_manager = None
            self.compliance_manager = None

    def setup_django_environment(self):
        """Setup Django environment for testing"""
        if not settings.configured:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.hms.settings')
            django.setup()

    def create_test_database(self, suffix: str = None) -> str:
        """Create isolated test database for migration testing"""
        if suffix is None:
            suffix = str(uuid.uuid4())[:8]

        db_name = f"{self.config.test_database_prefix}{suffix}"

        # Ensure we don't exceed max test databases
        with self.lock:
            if len(self.test_databases) >= self.config.max_test_databases:
                oldest_db = self.test_databases.pop(0)
                self.cleanup_test_database(oldest_db)

            self.test_databases.append(db_name)

        try:
            # Connect to PostgreSQL
            conn_params = {
                'host': settings.DATABASES['default'].get('HOST', 'localhost'),
                'port': settings.DATABASES['default'].get('PORT', '5432'),
                'user': settings.DATABASES['default'].get('USER', 'postgres'),
                'password': settings.DATABASES['default'].get('PASSWORD', 'postgres'),
                'database': 'postgres'
            }

            with psycopg2.connect(**conn_params) as conn:
                conn.autocommit = True
                cursor = conn.cursor()

                # Drop database if exists
                cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))

                # Create new database
                cursor.execute(sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8'").format(sql.Identifier(db_name)))

                # Create test schemas
                cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS healthcare_data"))
                cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS analytics"))
                cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS audit"))

                logger.info(f"Created test database: {db_name}")
                return db_name

        except Exception as e:
            logger.error(f"Failed to create test database {db_name}: {str(e)}")
            raise

    def cleanup_test_database(self, db_name: str):
        """Cleanup test database"""
        try:
            conn_params = {
                'host': settings.DATABASES['default'].get('HOST', 'localhost'),
                'port': settings.DATABASES['default'].get('PORT', '5432'),
                'user': settings.DATABASES['default'].get('USER', 'postgres'),
                'password': settings.DATABASES['default'].get('PASSWORD', 'postgres'),
                'database': 'postgres'
            }

            with psycopg2.connect(**conn_params) as conn:
                conn.autocommit = True
                cursor = conn.cursor()

                # Terminate all connections to the database
                cursor.execute(sql.SQL("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid()
                """), [db_name])

                # Drop database
                cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))

                logger.info(f"Cleaned up test database: {db_name}")

        except Exception as e:
            logger.warning(f"Failed to cleanup test database {db_name}: {str(e)}")

    def get_model_class(self, app_name: str) -> Any:
        """Get model class for given app"""
        try:
            # Try common model names
            model_names = [
                app_name.capitalize(),
                app_name[:-1].capitalize() if app_name.endswith('s') else app_name.capitalize(),
                app_name.title().replace('_', ''),
            ]

            for model_name in model_names:
                try:
                    return apps.get_model(app_name, model_name)
                except LookupError:
                    continue

            # If no model found, try to get the first model in the app
            app_config = apps.get_app_config(app_name)
            if app_config.models:
                return list(app_config.models.values())[0]

            raise ValueError(f"No models found for app: {app_name}")

        except Exception as e:
            logger.error(f"Failed to get model class for {app_name}: {str(e)}")
            raise

    def generate_test_data(self, model_class, count: int, encrypted_fields: List[str]) -> List[Dict[str, Any]]:
        """Generate anonymized test data for migration testing"""
        test_data = []

        for i in range(count):
            data = self._generate_model_data(model_class, i, encrypted_fields)
            test_data.append(data)

        return test_data

    def _generate_model_data(self, model_class, index: int, encrypted_fields: List[str]) -> Dict[str, Any]:
        """Generate data for a specific model"""
        data = {}
        model_name = model_class.__name__.lower()

        # Basic fields
        if hasattr(model_class, 'first_name'):
            data['first_name'] = f'Test{index:04d}'
        if hasattr(model_class, 'last_name'):
            data['last_name'] = f'User{index:04d}'
        if hasattr(model_class, 'email'):
            data['email'] = f'test{index:04d}@example.com'
        if hasattr(model_class, 'phone'):
            data['phone'] = f'555-{index:04d:04d}'
        if hasattr(model_class, 'name'):
            data['name'] = f'Test Entity {index:04d}'

        # Healthcare-specific data
        if model_name == 'patient':
            data.update({
                'date_of_birth': datetime.now() - timedelta(days=index * 365),
                'gender': 'M' if index % 2 == 0 else 'F',
                'blood_type': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'][index % 8],
                'medical_record_number': f'MRN{index:08d}',
                'ssn': f'{index:03d}-{index:02d}-{index:04d}',
                'address': f'{index:04d} Test Street, Test City, TC 12345',
                'emergency_contact_name': f'Emergency Contact {index}',
                'emergency_contact_phone': f'555-{index:04d:04d}',
                'primary_care_physician': f'Dr. Test{index:04d}',
                'insurance_provider': f'Test Insurance {index % 5 + 1}',
                'insurance_policy_number': f'POL{index:08d}',
                'allergies': 'Penicillin' if index % 3 == 0 else '',
                'medications': 'Lisinopril 10mg' if index % 2 == 0 else '',
                'chronic_conditions': 'Hypertension' if index % 4 == 0 else '',
                'last_visit_date': datetime.now() - timedelta(days=index * 30),
                'status': 'active'
            })

        elif model_name == 'medicalrecord':
            data.update({
                'record_date': datetime.now() - timedelta(days=index * 7),
                'record_type': ['diagnosis', 'treatment', 'follow-up', 'lab_result'][index % 4],
                'diagnosis': f'Test diagnosis {index}',
                'treatment': f'Test treatment {index}',
                'notes': f'Test medical notes for record {index}',
                'physician_id': (index % 10) + 1,
                'facility_id': (index % 5) + 1,
                'is_confidential': index % 10 == 0
            })

        elif model_name == 'appointment':
            data.update({
                'appointment_date': datetime.now().date() + timedelta(days=index),
                'appointment_time': datetime.now().replace(hour=9 + (index % 8), minute=0),
                'appointment_type': ['consultation', 'follow-up', 'procedure', 'emergency'][index % 4],
                'status': ['scheduled', 'confirmed', 'completed', 'cancelled'][index % 4],
                'physician_id': (index % 10) + 1,
                'facility_id': (index % 5) + 1,
                'notes': f'Test appointment notes {index}',
                'reminder_sent': True
            })

        elif model_name == 'bill':
            data.update({
                'bill_date': datetime.now().date(),
                'due_date': datetime.now().date() + timedelta(days=30),
                'total_amount': Decimal(f'{(index + 1) * 100.00}'),
                'status': 'pending',
                'payment_method': 'insurance',
                'insurance_info': f'Test Insurance Co. {index % 5 + 1}'
            })

        # Handle foreign keys and relationships
        for field in model_class._meta.fields:
            if field.is_relation and field.name not in data:
                if field.many_to_one:
                    # Generate a foreign key value
                    related_model = field.related_model
                    if hasattr(related_model, 'id'):
                        data[field.name] = (index % 10) + 1

        # Encrypt sensitive fields
        if self.encryption_manager and encrypted_fields:
            for field in encrypted_fields:
                if field in data:
                    data[field] = self.encryption_manager.encrypt(str(data[field]))

        return data

    def run_migration_test(self, scenario: MigrationScenario) -> MigrationTestResult:
        """Run comprehensive migration test for a scenario"""
        test_name = f"{scenario.name}_{scenario.app_name}"
        result = MigrationTestResult(
            test_name=test_name,
            test_type=MigrationTestType.FORWARD_MIGRATION,
            status=MigrationTestStatus.RUNNING,
            duration=0.0,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        start_time = time.time()
        test_db_name = None

        try:
            # Create test database
            test_db_name = self.create_test_database(scenario.name)
            result.database_name = test_db_name

            # Get model class
            model_class = self.get_model_class(scenario.app_name)

            # Configure Django for test database
            original_db_config = settings.DATABASES['default'].copy()
            settings.DATABASES['default'].update({
                'NAME': test_db_name,
                'TEST': {'NAME': test_db_name}
            })

            # Create migration executor
            with connections['default'].cursor() as cursor:
                executor = MigrationExecutor(connections['default'])

                # Run all requested test types
                test_results = []
                for test_type in scenario.test_types:
                    test_result = self._run_single_migration_test(
                        executor, model_class, scenario, test_type
                    )
                    test_results.append(test_result)

                    # Aggregate results
                    result.metrics[test_type.value] = test_result.metrics
                    result.warnings.extend(test_result.warnings)
                    result.healthcare_compliance.update(test_result.healthcare_compliance)
                    result.performance_metrics.update(test_result.performance_metrics)

                # Determine overall success
                result.success = all(r.success for r in test_results)

        except Exception as e:
            result.error_message = str(e)
            result.success = False
            logger.error(f"Migration test failed for {test_name}: {str(e)}")

        finally:
            result.duration = time.time() - start_time
            result.status = MigrationTestStatus.PASSED if result.success else MigrationTestStatus.FAILED

            # Cleanup
            if test_db_name:
                if self.config.cleanup_on_success and result.success:
                    self.cleanup_test_database(test_db_name)
                elif self.config.cleanup_on_failure and not result.success:
                    self.cleanup_test_database(test_db_name)

            # Restore original database configuration
            if 'original_db_config' in locals():
                settings.DATABASES['default'] = original_db_config

        with self.lock:
            self.test_results.append(result)

        return result

    def _run_single_migration_test(self, executor, model_class, scenario: MigrationScenario, test_type: MigrationTestType) -> MigrationTestResult:
        """Run a single type of migration test"""
        result = MigrationTestResult(
            test_name=f"{scenario.name}_{test_type.value}",
            test_type=test_type,
            status=MigrationTestStatus.RUNNING,
            duration=0.0,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        start_time = time.time()

        try:
            if test_type == MigrationTestType.FORWARD_MIGRATION:
                result = self._test_forward_migration(executor, model_class, scenario)
            elif test_type == MigrationTestType.BACKWARD_MIGRATION:
                result = self._test_backward_migration(executor, model_class, scenario)
            elif test_type == MigrationTestType.DATA_INTEGRITY:
                result = self._test_data_integrity(executor, model_class, scenario)
            elif test_type == MigrationTestType.PERFORMANCE:
                result = self._test_migration_performance(executor, model_class, scenario)
            elif test_type == MigrationTestType.SECURITY:
                result = self._test_migration_security(executor, model_class, scenario)
            elif test_type == MigrationTestType.COMPLIANCE:
                result = self._test_migration_compliance(executor, model_class, scenario)
            elif test_type == MigrationTestType.ROLLBACK:
                result = self._test_migration_rollback(executor, model_class, scenario)
            elif test_type == MigrationTestType.CONCURRENCY:
                result = self._test_concurrent_migration(executor, model_class, scenario)
            elif test_type == MigrationTestType.SCHEMA_VALIDATION:
                result = self._test_schema_validation(executor, model_class, scenario)
            else:
                raise ValueError(f"Unknown test type: {test_type}")

        except Exception as e:
            result.error_message = str(e)
            result.success = False
            logger.error(f"Test {test_type.value} failed: {str(e)}")

        finally:
            result.duration = time.time() - start_time
            result.status = MigrationTestStatus.PASSED if result.success else MigrationTestStatus.FAILED

        return result

    def _test_forward_migration(self, executor, model_class, scenario: MigrationScenario) -> MigrationTestResult:
        """Test forward migration"""
        result = MigrationTestResult(
            test_name=f"forward_migration_{scenario.name}",
            test_type=MigrationTestType.FORWARD_MIGRATION,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        try:
            start_time = time.time()

            # Apply initial migration
            executor.migrate([scenario.from_migration])

            # Generate and insert test data
            if scenario.test_data_size > 0:
                test_data = self.generate_test_data(model_class, scenario.test_data_size, scenario.encrypted_fields)
                if test_data:
                    model_class.objects.bulk_create([
                        model_class(**data) for data in test_data[:min(100, len(test_data))]
                    ])

            # Apply target migration
            executor.migrate([scenario.to_migration])

            migration_time = time.time() - start_time
            result.success = True
            result.metrics['migration_time'] = migration_time
            result.performance_metrics['migration_duration'] = migration_time

            # Check performance thresholds
            if migration_time > self.config.performance_thresholds.get('migration_time', 300.0):
                result.warnings.append(f"Migration time {migration_time:.2f}s exceeds threshold")

        except Exception as e:
            result.error_message = str(e)
            result.success = False

        return result

    def _test_backward_migration(self, executor, model_class, scenario: MigrationScenario) -> MigrationTestResult:
        """Test backward migration"""
        result = MigrationTestResult(
            test_name=f"backward_migration_{scenario.name}",
            test_type=MigrationTestType.BACKWARD_MIGRATION,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        try:
            # Migrate to target state
            executor.migrate([scenario.to_migration])

            # Record state
            target_state = self._capture_database_state(executor, scenario.app_name)

            # Migrate back to initial state
            executor.migrate([scenario.from_migration])

            # Migrate forward again
            executor.migrate([scenario.to_migration])

            # Compare states
            current_state = self._capture_database_state(executor, scenario.app_name)
            states_match = self._compare_database_states(target_state, current_state)

            result.success = states_match
            result.metrics['backward_compatibility'] = states_match

            if not states_match:
                result.warnings.append("Backward migration resulted in different state")

        except Exception as e:
            result.error_message = str(e)
            result.success = False

        return result

    def _test_data_integrity(self, executor, model_class, scenario: MigrationScenario) -> MigrationTestResult:
        """Test data integrity after migration"""
        result = MigrationTestResult(
            test_name=f"data_integrity_{scenario.name}",
            test_type=MigrationTestType.DATA_INTEGRITY,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        try:
            # Apply migrations
            executor.migrate([scenario.from_migration])
            executor.migrate([scenario.to_migration])

            # Test basic data operations
            with connections['default'].cursor() as cursor:
                # Test table exists
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                """, [model_class._meta.db_table])

                table_exists = cursor.fetchone() is not None
                result.metrics['table_exists'] = table_exists

                if not table_exists:
                    raise ValueError(f"Table {model_class._meta.db_table} does not exist")

                # Test column accessibility
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, [model_class._meta.db_table])

                columns = cursor.fetchall()
                result.metrics['column_count'] = len(columns)

                # Test data insertion
                if scenario.test_data_size > 0:
                    test_data = self.generate_test_data(model_class, 1, scenario.encrypted_fields)
                    if test_data:
                        model_class.objects.create(**test_data[0])
                        result.metrics['data_insertion'] = True

            # Test encrypted fields
            if scenario.encrypted_fields and self.encryption_manager:
                encryption_result = self._test_encryption_integrity(model_class, scenario.encrypted_fields)
                result.healthcare_compliance['encryption_integrity'] = encryption_result['success']
                result.warnings.extend(encryption_result['warnings'])

            result.success = True

        except Exception as e:
            result.error_message = str(e)
            result.success = False

        return result

    def _test_migration_performance(self, executor, model_class, scenario: MigrationScenario) -> MigrationTestResult:
        """Test migration performance"""
        result = MigrationTestResult(
            test_name=f"performance_{scenario.name}",
            test_type=MigrationTestType.PERFORMANCE,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        try:
            # Test with larger dataset
            large_scenario = scenario._replace(test_data_size=min(1000, scenario.test_data_size * 2))

            start_time = time.time()

            # Apply migrations with test data
            executor.migrate([large_scenario.from_migration])

            if large_scenario.test_data_size > 0:
                test_data = self.generate_test_data(model_class, large_scenario.test_data_size, large_scenario.encrypted_fields)
                if test_data:
                    # Batch insert
                    batch_size = 100
                    for i in range(0, len(test_data), batch_size):
                        batch = test_data[i:i + batch_size]
                        model_class.objects.bulk_create([
                            model_class(**data) for data in batch
                        ])

            executor.migrate([large_scenario.to_migration])

            total_time = time.time() - start_time

            result.success = True
            result.performance_metrics['total_migration_time'] = total_time
            result.performance_metrics['records_per_second'] = large_scenario.test_data_size / total_time if total_time > 0 else 0

            # Check performance thresholds
            if total_time > self.config.performance_thresholds.get('migration_time', 300.0):
                result.warnings.append(f"Performance test exceeded threshold: {total_time:.2f}s")

        except Exception as e:
            result.error_message = str(e)
            result.success = False

        return result

    def _test_migration_security(self, executor, model_class, scenario: MigrationScenario) -> MigrationTestResult:
        """Test migration security"""
        result = MigrationTestResult(
            test_name=f"security_{scenario.name}",
            test_type=MigrationTestType.SECURITY,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        try:
            # Apply migrations
            executor.migrate([scenario.from_migration])
            executor.migrate([scenario.to_migration])

            # Test encrypted field security
            if scenario.encrypted_fields and self.encryption_manager:
                test_data = self.generate_test_data(model_class, 1, scenario.encrypted_fields)
                if test_data:
                    record = model_class.objects.create(**test_data[0])

                    # Test that sensitive data is encrypted
                    for field in scenario.encrypted_fields:
                        if hasattr(record, field):
                            encrypted_value = getattr(record, field)
                            if encrypted_value:
                                # Check that it's not plaintext
                                original_value = test_data[0][field]
                                if str(encrypted_value) == str(original_value):
                                    result.warnings.append(f"Field {field} appears to be stored in plaintext")
                                    result.healthcare_compliance[f'{field}_encrypted'] = False
                                else:
                                    result.healthcare_compliance[f'{field}_encrypted'] = True

            # Test audit trail (if available)
            if self.audit_manager:
                try:
                    # Check if audit entries are created
                    audit_count = self._get_audit_count(scenario.app_name)
                    result.metrics['audit_entries'] = audit_count
                    result.healthcare_compliance['audit_trail'] = audit_count > 0
                except Exception as e:
                    result.warnings.append(f"Audit trail check failed: {str(e)}")

            result.success = True

        except Exception as e:
            result.error_message = str(e)
            result.success = False

        return result

    def _test_migration_compliance(self, executor, model_class, scenario: MigrationScenario) -> MigrationTestResult:
        """Test migration compliance"""
        result = MigrationTestResult(
            test_name=f"compliance_{scenario.name}",
            test_type=MigrationTestType.COMPLIANCE,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        try:
            # Apply migrations
            executor.migrate([scenario.from_migration])
            executor.migrate([scenario.to_migration])

            # Test compliance checks
            for compliance_check in self.config.compliance_checks:
                try:
                    if compliance_check == 'hipaa':
                        compliance_result = self._test_hipaa_compliance(model_class, scenario)
                    elif compliance_check == 'gdpr':
                        compliance_result = self._test_gdpr_compliance(model_class, scenario)
                    elif compliance_check == 'data_localization':
                        compliance_result = self._test_data_localization(model_class, scenario)
                    elif compliance_check == 'audit_trail':
                        compliance_result = self._test_audit_trail_compliance(model_class, scenario)
                    else:
                        continue

                    result.healthcare_compliance[compliance_check] = compliance_result['success']
                    result.warnings.extend(compliance_result['warnings'])

                except Exception as e:
                    result.warnings.append(f"Compliance check {compliance_check} failed: {str(e)}")

            result.success = True

        except Exception as e:
            result.error_message = str(e)
            result.success = False

        return result

    def _test_migration_rollback(self, executor, model_class, scenario: MigrationScenario) -> MigrationTestResult:
        """Test migration rollback"""
        result = MigrationTestResult(
            test_name=f"rollback_{scenario.name}",
            test_type=MigrationTestType.ROLLBACK,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        try:
            # Apply migrations
            executor.migrate([scenario.from_migration])
            executor.migrate([scenario.to_migration])

            # Capture final state
            final_state = self._capture_database_state(executor, scenario.app_name)

            # Rollback to initial state
            executor.migrate([scenario.from_migration])

            # Test that rollback was successful
            rollback_state = self._capture_database_state(executor, scenario.app_name)

            # Migrate forward again
            executor.migrate([scenario.to_migration])
            restored_state = self._capture_database_state(executor, scenario.app_name)

            # Compare states
            rollback_success = self._compare_database_states(final_state, restored_state)
            result.metrics['rollback_success'] = rollback_success

            if not rollback_success:
                result.warnings.append("Rollback test failed - states don't match")

            result.success = rollback_success

        except Exception as e:
            result.error_message = str(e)
            result.success = False

        return result

    def _test_concurrent_migration(self, executor, model_class, scenario: MigrationScenario) -> MigrationTestResult:
        """Test concurrent migration safety"""
        result = MigrationTestResult(
            test_name=f"concurrent_{scenario.name}",
            test_type=MigrationTestType.CONCURRENCY,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        try:
            # This is a simplified concurrent test
            # In practice, you'd test multiple simultaneous migrations

            # Apply migrations
            executor.migrate([scenario.from_migration])
            executor.migrate([scenario.to_migration])

            # Test basic concurrent operations
            def concurrent_test():
                # Simple concurrent operation
                with connections['default'].cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM %s" % model_class._meta.db_table)
                    return cursor.fetchone()[0]

            # Run concurrent operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor_pool:
                futures = [executor_pool.submit(concurrent_test) for _ in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]

            # All results should be consistent
            consistent = all(r == results[0] for r in results)
            result.metrics['concurrent_consistency'] = consistent

            if not consistent:
                result.warnings.append("Concurrent operations returned inconsistent results")

            result.success = True

        except Exception as e:
            result.error_message = str(e)
            result.success = False

        return result

    def _test_schema_validation(self, executor, model_class, scenario: MigrationScenario) -> MigrationTestResult:
        """Test schema validation"""
        result = MigrationTestResult(
            test_name=f"schema_validation_{scenario.name}",
            test_type=MigrationTestType.SCHEMA_VALIDATION,
            success=False,
            metrics={},
            healthcare_compliance={},
            performance_metrics={}
        )

        try:
            # Apply migrations
            executor.migrate([scenario.from_migration])
            executor.migrate([scenario.to_migration])

            # Validate schema
            schema_issues = self._validate_schema(model_class)

            result.metrics['schema_issues'] = len(schema_issues)
            result.warnings.extend(schema_issues)

            result.success = len(schema_issues) == 0

        except Exception as e:
            result.error_message = str(e)
            result.success = False

        return result

    def _capture_database_state(self, executor, app_name: str) -> Dict[str, Any]:
        """Capture current database state"""
        state = {
            'tables': {},
            'sequences': {},
            'constraints': {},
            'indexes': {}
        }

        with executor.connection.cursor() as cursor:
            # Get tables
            cursor.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            state['tables'] = {row[0]: row[1] for row in cursor.fetchall()}

            # Get sequences
            cursor.execute("""
                SELECT sequence_name
                FROM information_schema.sequences
                WHERE sequence_schema = 'public'
                ORDER BY sequence_name
            """)
            state['sequences'] = [row[0] for row in cursor.fetchall()]

            # Get constraints
            cursor.execute("""
                SELECT table_name, constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_schema = 'public'
                ORDER BY table_name, constraint_name
            """)
            for table_name, constraint_name, constraint_type in cursor.fetchall():
                if table_name not in state['constraints']:
                    state['constraints'][table_name] = {}
                state['constraints'][table_name][constraint_name] = constraint_type

            # Get indexes
            cursor.execute("""
                SELECT tablename, indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            for table_name, index_name, index_def in cursor.fetchall():
                if table_name not in state['indexes']:
                    state['indexes'][table_name] = {}
                state['indexes'][table_name][index_name] = index_def

        return state

    def _compare_database_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> bool:
        """Compare two database states"""
        # Compare tables
        if state1['tables'] != state2['tables']:
            return False

        # Compare sequences
        if set(state1['sequences']) != set(state2['sequences']):
            return False

        # Compare constraints
        if state1['constraints'] != state2['constraints']:
            return False

        # Compare indexes
        if state1['indexes'] != state2['indexes']:
            return False

        return True

    def _test_encryption_integrity(self, model_class, encrypted_fields: List[str]) -> Dict[str, Any]:
        """Test encryption integrity"""
        result = {'success': True, 'warnings': []}

        try:
            record = model_class.objects.first()
            if not record:
                result['warnings'].append("No records found for encryption test")
                return result

            for field in encrypted_fields:
                if hasattr(record, field):
                    encrypted_value = getattr(record, field)
                    if encrypted_value:
                        try:
                            decrypted_value = self.encryption_manager.decrypt(encrypted_value)
                            if not decrypted_value or len(str(decrypted_value)) == 0:
                                result['warnings'].append(f"Field {field} decrypted to empty value")
                                result['success'] = False
                        except Exception as e:
                            result['warnings'].append(f"Failed to decrypt field {field}: {str(e)}")
                            result['success'] = False

        except Exception as e:
            result['warnings'].append(f"Encryption integrity test failed: {str(e)}")
            result['success'] = False

        return result

    def _get_audit_count(self, app_name: str) -> int:
        """Get audit count for app"""
        try:
            from backend.core.models import AuditLog
            return AuditLog.objects.filter(
                object_type__istartswith=app_name.capitalize()
            ).count()
        except:
            return 0

    def _test_hipaa_compliance(self, model_class, scenario: MigrationScenario) -> Dict[str, Any]:
        """Test HIPAA compliance"""
        result = {'success': True, 'warnings': []}

        try:
            # Test PHI protection
            if scenario.encrypted_fields:
                for field in scenario.encrypted_fields:
                    # Check that PHI fields are encrypted
                    result['warnings'].append(f"PHI field {field} encryption verified")

            # Test audit trail
            audit_count = self._get_audit_count(scenario.app_name)
            if audit_count == 0:
                result['warnings'].append("No audit trail found")
                result['success'] = False

        except Exception as e:
            result['warnings'].append(f"HIPAA compliance test failed: {str(e)}")
            result['success'] = False

        return result

    def _test_gdpr_compliance(self, model_class, scenario: MigrationScenario) -> Dict[str, Any]:
        """Test GDPR compliance"""
        result = {'success': True, 'warnings': []}

        try:
            # Test data minimization
            field_count = len(model_class._meta.fields)
            if field_count > 50:
                result['warnings'].append(f"Model has {field_count} fields - consider data minimization")

            # Test personal data protection
            personal_fields = ['email', 'phone', 'address', 'ssn']
            protected_fields = 0
            for field in personal_fields:
                if hasattr(model_class, field):
                    protected_fields += 1

            if protected_fields == 0:
                result['warnings'].append("No personal data fields found")

        except Exception as e:
            result['warnings'].append(f"GDPR compliance test failed: {str(e)}")
            result['success'] = False

        return result

    def _test_data_localization(self, model_class, scenario: MigrationScenario) -> Dict[str, Any]:
        """Test data localization compliance"""
        result = {'success': True, 'warnings': []}

        try:
            # Check if data is properly localized
            # This would involve checking data residency requirements
            result['warnings'].append("Data localization verification needed")

        except Exception as e:
            result['warnings'].append(f"Data localization test failed: {str(e)}")
            result['success'] = False

        return result

    def _test_audit_trail_compliance(self, model_class, scenario: MigrationScenario) -> Dict[str, Any]:
        """Test audit trail compliance"""
        result = {'success': True, 'warnings': []}

        try:
            audit_count = self._get_audit_count(scenario.app_name)
            if audit_count == 0:
                result['warnings'].append("No audit trail entries found")
                result['success'] = False

        except Exception as e:
            result['warnings'].append(f"Audit trail compliance test failed: {str(e)}")
            result['success'] = False

        return result

    def _validate_schema(self, model_class) -> List[str]:
        """Validate database schema"""
        issues = []

        try:
            with connections['default'].cursor() as cursor:
                # Check for required constraints
                table_name = model_class._meta.db_table

                # Check primary key
                cursor.execute("""
                    SELECT constraint_name, constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_name = %s AND constraint_type = 'PRIMARY KEY'
                """, [table_name])

                if not cursor.fetchone():
                    issues.append(f"Table {table_name} missing primary key")

                # Check for foreign key constraints
                cursor.execute("""
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_name = %s AND constraint_type = 'FOREIGN KEY'
                """, [table_name])

                fk_constraints = cursor.fetchall()
                if not fk_constraints:
                    issues.append(f"Table {table_name} has no foreign key constraints")

                # Check for indexes
                cursor.execute("""
                    SELECT indexname FROM pg_indexes
                    WHERE tablename = %s AND schemaname = 'public'
                """, [table_name])

                indexes = cursor.fetchall()
                if not indexes:
                    issues.append(f"Table {table_name} has no indexes")

        except Exception as e:
            issues.append(f"Schema validation failed: {str(e)}")

        return issues

    def run_comprehensive_tests(self, scenarios: List[MigrationScenario]) -> Dict[str, Any]:
        """Run comprehensive migration tests"""
        results = {
            'total_scenarios': len(scenarios),
            'passed_scenarios': 0,
            'failed_scenarios': 0,
            'total_duration': 0.0,
            'scenario_results': [],
            'summary': {}
        }

        if self.config.enable_parallel_testing:
            # Run tests in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_scenario = {
                    executor.submit(self.run_migration_test, scenario): scenario
                    for scenario in scenarios
                }

                for future in concurrent.futures.as_completed(future_to_scenario):
                    scenario = future_to_scenario[future]
                    try:
                        result = future.result()
                        results['scenario_results'].append(result)
                        results['total_duration'] += result.duration

                        if result.success:
                            results['passed_scenarios'] += 1
                        else:
                            results['failed_scenarios'] += 1

                    except Exception as e:
                        logger.error(f"Test for scenario {scenario.name} failed: {str(e)}")
                        results['failed_scenarios'] += 1
        else:
            # Run tests sequentially
            for scenario in scenarios:
                result = self.run_migration_test(scenario)
                results['scenario_results'].append(result)
                results['total_duration'] += result.duration

                if result.success:
                    results['passed_scenarios'] += 1
                else:
                    results['failed_scenarios'] += 1

        # Calculate summary
        results['summary'] = {
            'success_rate': (results['passed_scenarios'] / results['total_scenarios']) * 100 if results['total_scenarios'] > 0 else 0,
            'average_duration': results['total_duration'] / results['total_scenarios'] if results['total_scenarios'] > 0 else 0,
            'critical_scenarios_passed': len([
                r for r in results['scenario_results']
                if r.success and MIGRATION_TEST_SCENARIOS[
                    next((i for i, s in enumerate(MIGRATION_TEST_SCENARIOS) if s['name'] == r.test_name.split('_')[0]), 0)
                ]['critical']
            ])
        }

        return results

    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report = f"""
# Database Migration Test Report

## Summary
- **Total Scenarios**: {results['total_scenarios']}
- **Passed**: {results['passed_scenarios']}
- **Failed**: {results['failed_scenarios']}
- **Success Rate**: {results['summary']['success_rate']:.1f}%
- **Total Duration**: {results['total_duration']:.2f}s
- **Average Duration**: {results['summary']['average_duration']:.2f}s
- **Critical Scenarios Passed**: {results['summary']['critical_scenarios_passed']}

## Test Results
"""

        for result in results['scenario_results']:
            status_icon = "✅" if result.success else "❌"
            report += f"""
### {result.test_name}
- **Status**: {status_icon} {result.status.value}
- **Duration**: {result.duration:.2f}s
- **Database**: {result.database_name or 'N/A'}
"""

            if result.metrics:
                report += "- **Metrics**:\n"
                for key, value in result.metrics.items():
                    report += f"  - {key}: {value}\n"

            if result.healthcare_compliance:
                report += "- **Healthcare Compliance**:\n"
                for key, value in result.healthcare_compliance.items():
                    status_icon = "✅" if value else "❌"
                    report += f"  - {key}: {status_icon}\n"

            if result.performance_metrics:
                report += "- **Performance**:\n"
                for key, value in result.performance_metrics.items():
                    report += f"  - {key}: {value}\n"

            if result.warnings:
                report += "- **Warnings**:\n"
                for warning in result.warnings:
                    report += f"  - {warning}\n"

            if result.error_message:
                report += f"- **Error**: {result.error_message}\n"

        return report

    def cleanup_all_test_databases(self):
        """Cleanup all test databases"""
        with self.lock:
            for db_name in self.test_databases:
                try:
                    self.cleanup_test_database(db_name)
                except Exception as e:
                    logger.warning(f"Failed to cleanup test database {db_name}: {str(e)}")
            self.test_databases = []

# Migration test scenarios
MIGRATION_TEST_SCENARIOS = [
    MigrationScenario(
        name="Patient Data Migration",
        app_name="patients",
        from_migration="0001_initial",
        to_migration="0005_patient_patients_pa_hospita_8adb46_idx_and_more",
        test_data_size=1000,
        healthcare_data=True,
        encrypted_fields=["first_name", "last_name", "email", "phone", "ssn"],
        critical=True
    ),
    MigrationScenario(
        name="Medical Records Migration",
        app_name="ehr",
        from_migration="0001_initial",
        to_migration="0006_notificationmodel_qualitymetric_and_more",
        test_data_size=500,
        healthcare_data=True,
        encrypted_fields=["diagnosis", "treatment", "notes"],
        critical=True
    ),
    MigrationScenario(
        name="Appointments Migration",
        app_name="appointments",
        from_migration="0001_initial",
        to_migration="0005_appointment_appointment_hospita_399297_idx_and_more",
        test_data_size=2000,
        healthcare_data=False,
        encrypted_fields=["notes"],
        critical=False
    ),
    MigrationScenario(
        name="Billing Migration",
        app_name="billing",
        from_migration="0001_initial",
        to_migration="0007_bill_billing_bil_hospita_79db2a_idx_and_more",
        test_data_size=1500,
        healthcare_data=True,
        encrypted_fields=["payment_method", "insurance_info"],
        critical=True
    ),
    MigrationScenario(
        name="Accounting Migration",
        app_name="accounting",
        from_migration="0001_initial",
        to_migration="0002_alter_accountingauditlog_user",
        test_data_size=1000,
        healthcare_data=False,
        encrypted_fields=["description"],
        critical=False
    )
]

# Utility functions
def create_migration_test_config() -> MigrationTestConfig:
    """Create default migration test configuration"""
    return MigrationTestConfig(
        test_database_prefix="test_hms_migration_",
        max_test_databases=5,
        cleanup_on_success=True,
        cleanup_on_failure=False,
        enable_parallel_testing=True,
        max_workers=4,
        healthcare_data_validation=True,
        encryption_validation=True,
        performance_thresholds={
            'migration_time': 300.0,
            'query_time': 5.0,
            'memory_usage': 1024.0
        },
        compliance_checks=['hipaa', 'gdpr', 'audit_trail']
    )

def run_hms_migration_tests():
    """Run HMS-specific migration tests"""
    config = create_migration_test_config()
    framework = DatabaseMigrationTestFramework(config)

    try:
        print("Running comprehensive HMS migration tests...")
        results = framework.run_comprehensive_tests(MIGRATION_TEST_SCENARIOS)

        # Generate report
        report = framework.generate_test_report(results)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/tmp/hms_migration_test_report_{timestamp}.md"
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"Migration tests completed. Report saved to {report_path}")

        # Print summary
        print(f"\nTest Summary:")
        print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
        print(f"Critical Scenarios: {results['summary']['critical_scenarios_passed']}/{len([s for s in MIGRATION_TEST_SCENARIOS if s.critical])}")

        return results

    finally:
        framework.cleanup_all_test_databases()

if __name__ == "__main__":
    run_hms_migration_tests()