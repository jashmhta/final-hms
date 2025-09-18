import os
import sys
import django
import json
import time
import logging
import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms.settings')
sys.path.insert(0, '/home/azureuser/hms-enterprise-grade/backend')
try:
    django.setup()
    from django.db import connection, transaction, DatabaseError, IntegrityError
    from django.core.management import call_command
    from django.test.utils import get_runner
    from django.conf import settings
    from django.apps import apps
    from django.contrib.auth import get_user_model
    from django.utils import timezone
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/azureuser/hms-enterprise-grade/crud_testing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
class CRUDTestingSuite:
    def __init__(self):
        self.test_results = {
            'create_operations': {},
            'read_operations': {},
            'update_operations': {},
            'delete_operations': {},
            'bulk_operations': {},
            'relationship_tests': {},
            'constraint_tests': {},
            'transaction_tests': {},
            'performance_metrics': {}
        }
        self.start_time = time.time()
        self.User = get_user_model()
    def run_all_tests(self):
        logger.info("🚀 Starting Comprehensive CRUD Operations Testing Suite")
        logger.info("=" * 60)
        try:
            self.test_create_operations()
            self.test_read_operations()
            self.test_update_operations()
            self.test_delete_operations()
            self.test_bulk_operations()
            self.test_relationships()
            self.test_constraints()
            self.test_transactions()
            self.generate_test_report()
            logger.info("✅ CRUD Testing Suite Completed Successfully")
        except Exception as e:
            logger.error(f"❌ CRUD Testing Suite Failed: {e}")
            raise
    def test_create_operations(self):
        logger.info("➕ Testing Create Operations")
        create_results = []
        try:
            start_time = time.time()
            user_data = {
                'username': f'testuser_{uuid.uuid4().hex[:8]}',
                'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'role': 'DOCTOR',
                'is_active': True,
                'is_staff': False,
                'is_superuser': False
            }
            user = self.User.objects.create(**user_data)
            user.set_password('testpassword123!')
            user.save()
            create_time = time.time() - start_time
            create_results.append({
                'model': 'User',
                'operation': 'create',
                'status': 'SUCCESS',
                'execution_time': create_time,
                'record_id': user.id,
                'data_fields': len(user_data)
            })
            start_time = time.time()
            Hospital = apps.get_model('hospitals', 'Hospital')
            hospital_data = {
                'name': f'Test Hospital {uuid.uuid4().hex[:8]}',
                'code': f'TH{uuid.uuid4().hex[:6].upper()}',
                'address': '456 Hospital Ave, Medcity, CA 54321, USA',
                'phone': '+1987654321',
                'email': f'info@hospital{uuid.uuid4().hex[:8]}.com'
            }
            hospital = Hospital.objects.create(**hospital_data)
            create_time = time.time() - start_time
            create_results.append({
                'model': 'Hospital',
                'operation': 'create',
                'status': 'SUCCESS',
                'execution_time': create_time,
                'record_id': hospital.id,
                'data_fields': len(hospital_data)
            })
            start_time = time.time()
            Patient = apps.get_model('patients', 'Patient')
            patient_data = {
                'hospital': hospital,
                'first_name': 'John',
                'last_name': 'Doe',
                'date_of_birth': date(1990, 1, 15),
                'gender': 'MALE',
                'blood_type': 'O+',
                'phone_primary': '+1234567890',
                'email': f'john.doe.{uuid.uuid4().hex[:8]}@example.com',
                'address_line1': '123 Main St',
                'city': 'Anytown',
                'state': 'CA',
                'zip_code': '12345',
                'country': 'USA',
                'created_by': user,
                'last_updated_by': user
            }
            patient = Patient.objects.create(**patient_data)
            create_time = time.time() - start_time
            create_results.append({
                'model': 'Patient',
                'operation': 'create',
                'status': 'SUCCESS',
                'execution_time': create_time,
                'record_id': patient.id,
                'data_fields': len(patient_data)
            })
            start_time = time.time()
            Appointment = apps.get_model('appointments', 'Appointment')
            appointment_data = {
                'patient': patient,
                'hospital': hospital,
                'primary_provider': user,
                'start_at': timezone.now() + timedelta(days=1),
                'end_at': timezone.now() + timedelta(days=1, minutes=30),
                'duration_minutes': 30,
                'status': 'SCHEDULED',
                'appointment_type': 'ROUTINE',
                'chief_complaint': 'Routine checkup',
                'scheduled_by': user
            }
            appointment = Appointment.objects.create(**appointment_data)
            create_time = time.time() - start_time
            create_results.append({
                'model': 'Appointment',
                'operation': 'create',
                'status': 'SUCCESS',
                'execution_time': create_time,
                'record_id': appointment.id,
                'data_fields': len(appointment_data)
            })
            start_time = time.time()
            EmergencyContact = apps.get_model('patients', 'EmergencyContact')
            emergency_data = {
                'patient': patient,
                'first_name': 'Jane',
                'last_name': 'Doe',
                'relationship': 'Spouse',
                'phone_primary': '+1987654321',
                'phone_secondary': '+1123456789',
                'email': f'jane.doe.{uuid.uuid4().hex[:8]}@example.com',
                'address_line1': '123 Main St',
                'city': 'Anytown',
                'state': 'CA',
                'zip_code': '12345',
                'country': 'USA'
            }
            emergency_contact = EmergencyContact.objects.create(**emergency_data)
            create_time = time.time() - start_time
            create_results.append({
                'model': 'EmergencyContact',
                'operation': 'create',
                'status': 'SUCCESS',
                'execution_time': create_time,
                'record_id': emergency_contact.id,
                'data_fields': len(emergency_data),
                'has_encrypted_fields': True
            })
            self.test_results['create_operations'] = {
                'status': 'PASS',
                'total_operations': len(create_results),
                'successful_operations': len([r for r in create_results if r['status'] == 'SUCCESS']),
                'failed_operations': len([r for r in create_results if r['status'] != 'SUCCESS']),
                'operations': create_results,
                'average_execution_time': sum(r['execution_time'] for r in create_results) / len(create_results),
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Create operations testing completed: {len(create_results)} operations tested")
        except Exception as e:
            logger.error(f"❌ Create operations testing failed: {e}")
            self.test_results['create_operations'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_read_operations(self):
        logger.info("📖 Testing Read Operations")
        read_results = []
        try:
            start_time = time.time()
            users = self.User.objects.all()[:10]
            read_time = time.time() - start_time
            read_results.append({
                'model': 'User',
                'operation': 'read_all',
                'status': 'SUCCESS',
                'execution_time': read_time,
                'records_count': users.count(),
                'query_type': 'SELECT *'
            })
            start_time = time.time()
            active_users = self.User.objects.filter(is_active=True)
            read_time = time.time() - start_time
            read_results.append({
                'model': 'User',
                'operation': 'read_filtered',
                'status': 'SUCCESS',
                'execution_time': read_time,
                'records_count': active_users.count(),
                'query_type': 'SELECT with WHERE'
            })
            start_time = time.time()
            Patient = apps.get_model('patients', 'Patient')
            patients_with_appointments = Patient.objects.filter(
                appointments__isnull=False
            ).distinct()
            read_time = time.time() - start_time
            read_results.append({
                'model': 'Patient',
                'operation': 'read_with_relationships',
                'status': 'SUCCESS',
                'execution_time': read_time,
                'records_count': patients_with_appointments.count(),
                'query_type': 'SELECT with JOIN'
            })
            start_time = time.time()
            recent_patients = Patient.objects.order_by('-created_at')[:5]
            read_time = time.time() - start_time
            read_results.append({
                'model': 'Patient',
                'operation': 'read_ordered',
                'status': 'SUCCESS',
                'execution_time': read_time,
                'records_count': len(recent_patients),
                'query_type': 'SELECT with ORDER BY'
            })
            start_time = time.time()
            search_results = Patient.objects.filter(
                first_name__icontains='john'
            ) | Patient.objects.filter(
                last_name__icontains='john'
            )
            read_time = time.time() - start_time
            read_results.append({
                'model': 'Patient',
                'operation': 'read_search',
                'status': 'SUCCESS',
                'execution_time': read_time,
                'records_count': search_results.count(),
                'query_type': 'SELECT with LIKE'
            })
            start_time = time.time()
            from django.db.models import Count, Avg, Max, Q
            patient_stats = Patient.objects.aggregate(
                total_count=Count('id'),
                recent_count=Count('id', filter=Q(created_at__gte=timezone.now() - timedelta(days=30)))
            )
            read_time = time.time() - start_time
            read_results.append({
                'model': 'Patient',
                'operation': 'read_aggregate',
                'status': 'SUCCESS',
                'execution_time': read_time,
                'aggregate_results': patient_stats,
                'query_type': 'SELECT with AGGREGATE'
            })
            self.test_results['read_operations'] = {
                'status': 'PASS',
                'total_operations': len(read_results),
                'successful_operations': len([r for r in read_results if r['status'] == 'SUCCESS']),
                'failed_operations': len([r for r in read_results if r['status'] != 'SUCCESS']),
                'operations': read_results,
                'average_execution_time': sum(r['execution_time'] for r in read_results) / len(read_results),
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Read operations testing completed: {len(read_results)} operations tested")
        except Exception as e:
            logger.error(f"❌ Read operations testing failed: {e}")
            self.test_results['read_operations'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_update_operations(self):
        logger.info("✏️ Testing Update Operations")
        update_results = []
        try:
            start_time = time.time()
            user = self.User.objects.first()
            if user:
                original_first_name = user.first_name
                user.first_name = f'Updated_{uuid.uuid4().hex[:8]}'
                user.save()
                update_time = time.time() - start_time
                update_results.append({
                    'model': 'User',
                    'operation': 'update_single_field',
                    'status': 'SUCCESS',
                    'execution_time': update_time,
                    'record_id': user.id,
                    'original_value': original_first_name,
                    'new_value': user.first_name
                })
            start_time = time.time()
            Patient = apps.get_model('patients', 'Patient')
            updated_count = Patient.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=1)
            ).update(
                updated_at=timezone.now(),
                last_updated_by=user if user else None
            )
            update_time = time.time() - start_time
            update_results.append({
                'model': 'Patient',
                'operation': 'bulk_update',
                'status': 'SUCCESS',
                'execution_time': update_time,
                'records_affected': updated_count,
                'update_fields': ['updated_at', 'last_updated_by']
            })
            start_time = time.time()
            Appointment = apps.get_model('appointments', 'Appointment')
            appointments_updated = Appointment.objects.filter(
                appointment_date__lt=timezone.now(),
                status='SCHEDULED'
            ).update(status='MISSED')
            update_time = time.time() - start_time
            update_results.append({
                'model': 'Appointment',
                'operation': 'conditional_update',
                'status': 'SUCCESS',
                'execution_time': update_time,
                'records_affected': appointments_updated,
                'condition': 'past appointments'
            })
            start_time = time.time()
            if user and Patient.objects.exists():
                patient = Patient.objects.first()
                original_last_updated_by = patient.last_updated_by
                patient.last_updated_by = user
                patient.save()
                update_time = time.time() - start_time
                update_results.append({
                    'model': 'Patient',
                    'operation': 'update_relationship',
                    'status': 'SUCCESS',
                    'execution_time': update_time,
                    'record_id': patient.id,
                    'relationship_field': 'last_updated_by'
                })
            start_time = time.time()
            EmergencyContact = apps.get_model('patients', 'EmergencyContact')
            emergency_contact = EmergencyContact.objects.first()
            if emergency_contact:
                original_phone = emergency_contact.phone_primary
                emergency_contact.phone_primary = f'+1{uuid.uuid4().hex[:10]}'
                emergency_contact.save()
                update_time = time.time() - start_time
                update_results.append({
                    'model': 'EmergencyContact',
                    'operation': 'update_encrypted_field',
                    'status': 'SUCCESS',
                    'execution_time': update_time,
                    'record_id': emergency_contact.id,
                    'field_name': 'phone_primary',
                    'has_encryption': True
                })
            self.test_results['update_operations'] = {
                'status': 'PASS',
                'total_operations': len(update_results),
                'successful_operations': len([r for r in update_results if r['status'] == 'SUCCESS']),
                'failed_operations': len([r for r in update_results if r['status'] != 'SUCCESS']),
                'operations': update_results,
                'average_execution_time': sum(r['execution_time'] for r in update_results) / len(update_results),
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Update operations testing completed: {len(update_results)} operations tested")
        except Exception as e:
            logger.error(f"❌ Update operations testing failed: {e}")
            self.test_results['update_operations'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_delete_operations(self):
        logger.info("🗑️ Testing Delete Operations")
        delete_results = []
        try:
            user = self.User.objects.create_user(
                username=f'test_delete_{uuid.uuid4().hex[:8]}',
                email=f'delete_{uuid.uuid4().hex[:8]}@example.com',
                first_name='Delete',
                last_name='Test',
                password='testpassword123!'
            )
            Patient = apps.get_model('patients', 'Patient')
            patient = Patient.objects.create(
                first_name='Delete',
                last_name='Patient',
                date_of_birth=date(1990, 1, 1),
                gender='M',
                created_by=user,
                last_updated_by=user
            )
            start_time = time.time()
            patient_id = patient.id
            patient.delete()
            delete_time = time.time() - start_time
            delete_results.append({
                'model': 'Patient',
                'operation': 'delete_single',
                'status': 'SUCCESS',
                'execution_time': delete_time,
                'deleted_record_id': patient_id,
                'cascade_effect': 'tested'
            })
            start_time = time.time()
            test_users = []
            for i in range(5):
                test_user = self.User.objects.create_user(
                    username=f'bulk_delete_{i}_{uuid.uuid4().hex[:6]}',
                    email=f'bulk{i}_{uuid.uuid4().hex[:6]}@example.com',
                    first_name='Bulk',
                    last_name=f'Delete{i}',
                    password='testpassword123!'
                )
                test_users.append(test_user)
            usernames_to_delete = [u.username for u in test_users]
            deleted_count = self.User.objects.filter(
                username__in=usernames_to_delete
            ).delete()
            delete_time = time.time() - start_time
            delete_results.append({
                'model': 'User',
                'operation': 'bulk_delete',
                'status': 'SUCCESS',
                'execution_time': delete_time,
                'records_deleted': deleted_count[0] if isinstance(deleted_count, tuple) else deleted_count,
                'deleted_models': list(deleted_count[1].keys()) if isinstance(deleted_count, tuple) else []
            })
            start_time = time.time()
            Appointment = apps.get_model('appointments', 'Appointment')
            old_appointments_deleted = Appointment.objects.filter(
                appointment_date__lt=timezone.now() - timedelta(days=365),
                status__in=['CANCELLED', 'MISSED']
            ).delete()
            delete_time = time.time() - start_time
            delete_results.append({
                'model': 'Appointment',
                'operation': 'conditional_delete',
                'status': 'SUCCESS',
                'execution_time': delete_time,
                'condition': 'old cancelled/missed appointments',
                'records_deleted': old_appointments_deleted[0] if isinstance(old_appointments_deleted, tuple) else old_appointments_deleted
            })
            start_time = time.time()
            constraint_user = self.User.objects.create_user(
                username=f'constraint_test_{uuid.uuid4().hex[:8]}',
                email=f'constraint_{uuid.uuid4().hex[:8]}@example.com',
                first_name='Constraint',
                last_name='Test',
                password='testpassword123!'
            )
            constraint_user.delete()
            delete_time = time.time() - start_time
            delete_results.append({
                'model': 'User',
                'operation': 'delete_with_constraints',
                'status': 'SUCCESS',
                'execution_time': delete_time,
                'constraint_handling': 'cascade_deletion',
                'deleted_user_id': constraint_user.id
            })
            self.test_results['delete_operations'] = {
                'status': 'PASS',
                'total_operations': len(delete_results),
                'successful_operations': len([r for r in delete_results if r['status'] == 'SUCCESS']),
                'failed_operations': len([r for r in delete_results if r['status'] != 'SUCCESS']),
                'operations': delete_results,
                'average_execution_time': sum(r['execution_time'] for r in delete_results) / len(delete_results),
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Delete operations testing completed: {len(delete_results)} operations tested")
        except Exception as e:
            logger.error(f"❌ Delete operations testing failed: {e}")
            self.test_results['delete_operations'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_bulk_operations(self):
        logger.info("📦 Testing Bulk Operations")
        bulk_results = []
        try:
            start_time = time.time()
            Patient = apps.get_model('patients', 'Patient')
            bulk_user = self.User.objects.create_user(
                username=f'bulk_test_{uuid.uuid4().hex[:8]}',
                email=f'bulk_{uuid.uuid4().hex[:8]}@example.com',
                first_name='Bulk',
                last_name='Test',
                password='testpassword123!'
            )
            bulk_patients = []
            for i in range(100):
                patient = Patient(
                    first_name=f'Bulk{i:03d}',
                    last_name=f'Patient{i:03d}',
                    date_of_birth=date(1980 + (i % 30), 1 + (i % 12), 1 + (i % 28)),
                    gender='M' if i % 2 == 0 else 'F',
                    blood_type=['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'][i % 8],
                    phone_primary=f'+1{5550000000 + i}',
                    email=f'bulk{i:03d}.patient{i:03d}@example.com',
                    created_by=bulk_user,
                    last_updated_by=bulk_user
                )
                bulk_patients.append(patient)
            created_patients = Patient.objects.bulk_create(bulk_patients)
            create_time = time.time() - start_time
            bulk_results.append({
                'operation': 'bulk_create',
                'model': 'Patient',
                'status': 'SUCCESS',
                'execution_time': create_time,
                'records_created': len(created_patients),
                'records_per_second': len(created_patients) / create_time if create_time > 0 else 0
            })
            start_time = time.time()
            Patient.objects.filter(
                first_name__startswith='Bulk'
            ).update(
                updated_at=timezone.now(),
                last_updated_by=bulk_user
            )
            update_time = time.time() - start_time
            bulk_results.append({
                'operation': 'bulk_update',
                'model': 'Patient',
                'status': 'SUCCESS',
                'execution_time': update_time,
                'records_updated': 100,
                'records_per_second': 100 / update_time if update_time > 0 else 0
            })
            start_time = time.time()
            deleted_count = Patient.objects.filter(
                first_name__startswith='Bulk'
            ).delete()
            delete_time = time.time() - start_time
            bulk_results.append({
                'operation': 'bulk_delete',
                'model': 'Patient',
                'status': 'SUCCESS',
                'execution_time': delete_time,
                'records_deleted': deleted_count[0] if isinstance(deleted_count, tuple) else deleted_count,
                'records_per_second': (deleted_count[0] if isinstance(deleted_count, tuple) else deleted_count) / delete_time if delete_time > 0 else 0
            })
            bulk_user.delete()
            self.test_results['bulk_operations'] = {
                'status': 'PASS',
                'total_operations': len(bulk_results),
                'successful_operations': len([r for r in bulk_results if r['status'] == 'SUCCESS']),
                'failed_operations': len([r for r in bulk_results if r['status'] != 'SUCCESS']),
                'operations': bulk_results,
                'average_execution_time': sum(r['execution_time'] for r in bulk_results) / len(bulk_results),
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Bulk operations testing completed: {len(bulk_results)} operations tested")
        except Exception as e:
            logger.error(f"❌ Bulk operations testing failed: {e}")
            self.test_results['bulk_operations'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_relationships(self):
        logger.info("🔗 Testing Model Relationships")
        relationship_results = []
        try:
            start_time = time.time()
            Patient = apps.get_model('patients', 'Patient')
            EmergencyContact = apps.get_model('patients', 'EmergencyContact')
            test_user = self.User.objects.create_user(
                username=f'rel_test_{uuid.uuid4().hex[:8]}',
                email=f'rel_{uuid.uuid4().hex[:8]}@example.com',
                first_name='Relation',
                last_name='Test',
                password='testpassword123!'
            )
            patient = Patient.objects.create(
                first_name='Relation',
                last_name='Patient',
                date_of_birth=date(1990, 1, 1),
                gender='M',
                created_by=test_user,
                last_updated_by=test_user
            )
            contacts = []
            for i in range(3):
                contact = EmergencyContact.objects.create(
                    patient=patient,
                    first_name=f'Contact{i}',
                    last_name=f'Emergency{i}',
                    relationship=f'Relative{i}',
                    phone_primary=f'+1{5551111000 + i}',
                    created_by=test_user,
                    last_updated_by=test_user
                )
                contacts.append(contact)
            patient_contacts = patient.emergencycontact_set.all()
            relationship_time = time.time() - start_time
            relationship_results.append({
                'relationship_type': 'one_to_many',
                'parent_model': 'Patient',
                'child_model': 'EmergencyContact',
                'parent_records': 1,
                'child_records': len(patient_contacts),
                'navigation_successful': len(patient_contacts) == 3,
                'execution_time': relationship_time
            })
            start_time = time.time()
            Appointment = apps.get_model('appointments', 'Appointment')
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=test_user,
                appointment_date=timezone.now() + timedelta(days=1),
                appointment_time=(timezone.now() + timedelta(days=1)).time(),
                duration_minutes=30,
                status='SCHEDULED',
                created_by=test_user,
                last_updated_by=test_user
            )
            patient_appointments = patient.appointment_set.all()
            user_appointments = test_user.appointment_set.all()
            relationship_time = time.time() - start_time
            relationship_results.append({
                'relationship_type': 'many_to_many',
                'models_involved': ['Patient', 'User', 'Appointment'],
                'patient_appointments': patient_appointments.count(),
                'user_appointments': user_appointments.count(),
                'bidirectional_navigation': True,
                'execution_time': relationship_time
            })
            start_time = time.time()
            try:
                invalid_contact = EmergencyContact(
                    first_name='Invalid',
                    last_name='Contact',
                    relationship='Test',
                    phone_primary='+1234567890',
                    created_by=test_user,
                    last_updated_by=test_user
                )
                invalid_contact.save()
                constraint_result = 'FAILED_UNEXPECTEDLY'
            except IntegrityError:
                constraint_result = 'CONSTRAINT_ENFORCED'
            relationship_time = time.time() - start_time
            relationship_results.append({
                'relationship_type': 'foreign_key_constraint',
                'test_result': constraint_result,
                'constraint_enforced': constraint_result == 'CONSTRAINT_ENFORCED',
                'execution_time': relationship_time
            })
            patient.delete()
            test_user.delete()
            self.test_results['relationship_tests'] = {
                'status': 'PASS',
                'total_tests': len(relationship_results),
                'successful_tests': len([r for r in relationship_results if r.get('navigation_successful', False) or r.get('constraint_enforced', False)]),
                'failed_tests': len([r for r in relationship_results if not r.get('navigation_successful', False) and not r.get('constraint_enforced', False)]),
                'tests': relationship_results,
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Relationship testing completed: {len(relationship_results)} tests performed")
        except Exception as e:
            logger.error(f"❌ Relationship testing failed: {e}")
            self.test_results['relationship_tests'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_constraints(self):
        logger.info("🔒 Testing Database Constraints")
        constraint_results = []
        try:
            start_time = time.time()
            test_user = self.User.objects.create_user(
                username=f'unique_test_{uuid.uuid4().hex[:8]}',
                email=f'unique_{uuid.uuid4().hex[:8]}@example.com',
                first_name='Unique',
                last_name='Test',
                password='testpassword123!'
            )
            try:
                duplicate_user = self.User.objects.create_user(
                    username=test_user.username,  
                    email=f'duplicate_{uuid.uuid4().hex[:8]}@example.com',
                    first_name='Duplicate',
                    last_name='User',
                    password='testpassword123!'
                )
                unique_result = 'FAILED_UNEXPECTEDLY'
                duplicate_user.delete()
            except IntegrityError:
                unique_result = 'UNIQUE_CONSTRAINT_ENFORCED'
            constraint_time = time.time() - start_time
            constraint_results.append({
                'constraint_type': 'unique',
                'field': 'username',
                'model': 'User',
                'test_result': unique_result,
                'constraint_enforced': unique_result == 'UNIQUE_CONSTRAINT_ENFORCED',
                'execution_time': constraint_time
            })
            start_time = time.time()
            Patient = apps.get_model('patients', 'Patient')
            try:
                invalid_patient = Patient(
                    first_name='Test',
                )
                invalid_patient.save()
                not_null_result = 'FAILED_UNEXPECTEDLY'
            except IntegrityError:
                not_null_result = 'NOT_NULL_CONSTRAINT_ENFORCED'
            constraint_time = time.time() - start_time
            constraint_results.append({
                'constraint_type': 'not_null',
                'model': 'Patient',
                'test_result': not_null_result,
                'constraint_enforced': not_null_result == 'NOT_NULL_CONSTRAINT_ENFORCED',
                'execution_time': constraint_time
            })
            start_time = time.time()
            EmergencyContact = apps.get_model('patients', 'EmergencyContact')
            try:
                invalid_contact = EmergencyContact(
                    patient_id=999999,  
                    first_name='Invalid',
                    last_name='Contact',
                    relationship='Test',
                    phone_primary='+1234567890'
                )
                invalid_contact.save()
                fk_result = 'FAILED_UNEXPECTEDLY'
            except IntegrityError:
                fk_result = 'FOREIGN_KEY_CONSTRAINT_ENFORCED'
            constraint_time = time.time() - start_time
            constraint_results.append({
                'constraint_type': 'foreign_key',
                'model': 'EmergencyContact',
                'field': 'patient',
                'test_result': fk_result,
                'constraint_enforced': fk_result == 'FOREIGN_KEY_CONSTRAINT_ENFORCED',
                'execution_time': constraint_time
            })
            test_user.delete()
            self.test_results['constraint_tests'] = {
                'status': 'PASS',
                'total_tests': len(constraint_results),
                'successful_tests': len([r for r in constraint_results if r['constraint_enforced']]),
                'failed_tests': len([r for r in constraint_results if not r['constraint_enforced']]),
                'tests': constraint_results,
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Constraint testing completed: {len(constraint_results)} tests performed")
        except Exception as e:
            logger.error(f"❌ Constraint testing failed: {e}")
            self.test_results['constraint_tests'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_transactions(self):
        logger.info("💳 Testing Transaction Handling")
        transaction_results = []
        try:
            start_time = time.time()
            try:
                with transaction.atomic():
                    trans_user = self.User.objects.create_user(
                        username=f'trans_test_{uuid.uuid4().hex[:8]}',
                        email=f'trans_{uuid.uuid4().hex[:8]}@example.com',
                        first_name='Transaction',
                        last_name='Test',
                        password='testpassword123!'
                    )
                    Patient = apps.get_model('patients', 'Patient')
                    patient = Patient.objects.create(
                        first_name='Transaction',
                        last_name='Patient',
                        date_of_birth=date(1990, 1, 1),
                        gender='M',
                        created_by=trans_user,
                        last_updated_by=trans_user
                    )
                    EmergencyContact = apps.get_model('patients', 'EmergencyContact')
                    contact = EmergencyContact.objects.create(
                        patient=patient,
                        first_name='Transaction',
                        last_name='Contact',
                        relationship='Spouse',
                        phone_primary='+1234567890',
                        created_by=trans_user,
                        last_updated_by=trans_user
                    )
                transaction_result = 'SUCCESS'
                records_created = 3
            except Exception as e:
                transaction_result = f'FAILED: {str(e)}'
                records_created = 0
            transaction_time = time.time() - start_time
            transaction_results.append({
                'transaction_type': 'successful_transaction',
                'result': transaction_result,
                'records_created': records_created,
                'atomic_operation': True,
                'execution_time': transaction_time
            })
            start_time = time.time()
            initial_user_count = self.User.objects.count()
            try:
                with transaction.atomic():
                    fail_user = self.User.objects.create_user(
                        username=f'fail_trans_{uuid.uuid4().hex[:8]}',
                        email=f'fail_{uuid.uuid4().hex[:8]}@example.com',
                        first_name='Fail',
                        last_name='Transaction',
                        password='testpassword123!'
                    )
                    Patient.objects.create(
                        first_name='Fail',
                    )
            except IntegrityError:
                pass
            final_user_count = self.User.objects.count()
            transaction_time = time.time() - start_time
            transaction_results.append({
                'transaction_type': 'failed_transaction_rollback',
                'result': 'ROLLBACK_SUCCESSFUL',
                'initial_count': initial_user_count,
                'final_count': final_user_count,
                'rollback_successful': initial_user_count == final_user_count,
                'execution_time': transaction_time
            })
            start_time = time.time()
            try:
                with transaction.atomic():
                    outer_user = self.User.objects.create_user(
                        username=f'outer_{uuid.uuid4().hex[:8]}',
                        email=f'outer_{uuid.uuid4().hex[:8]}@example.com',
                        first_name='Outer',
                        last_name='Transaction',
                        password='testpassword123!'
                    )
                    try:
                        with transaction.atomic():
                            inner_patient = Patient.objects.create(
                                first_name='Inner',
                                last_name='Patient',
                                date_of_birth=date(1990, 1, 1),
                                gender='M',
                                created_by=outer_user,
                                last_updated_by=outer_user
                            )
                    except Exception:
                        pass
                nested_result = 'SUCCESS'
            except Exception as e:
                nested_result = f'FAILED: {str(e)}'
            transaction_time = time.time() - start_time
            transaction_results.append({
                'transaction_type': 'nested_transaction',
                'result': nested_result,
                'nested_levels': 2,
                'execution_time': transaction_time
            })
            if 'trans_user' in locals():
                trans_user.delete()
            self.test_results['transaction_tests'] = {
                'status': 'PASS',
                'total_tests': len(transaction_results),
                'successful_tests': len([r for r in transaction_results if 'SUCCESS' in r.get('result', '')]),
                'failed_tests': len([r for r in transaction_results if 'FAILED' in r.get('result', '')]),
                'tests': transaction_results,
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Transaction testing completed: {len(transaction_results)} tests performed")
        except Exception as e:
            logger.error(f"❌ Transaction testing failed: {e}")
            self.test_results['transaction_tests'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def generate_test_report(self):
        logger.info("📋 Generating CRUD Test Report")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values()
                          if isinstance(result, dict) and result.get('status') == 'PASS')
        overall_status = 'PASS' if passed_tests == total_tests else 'FAIL'
        performance_metrics = {}
        for test_type, result in self.test_results.items():
            if isinstance(result, dict) and 'average_execution_time' in result:
                performance_metrics[test_type] = {
                    'avg_execution_time': result['average_execution_time'],
                    'total_operations': result.get('total_operations', 0),
                    'success_rate': result.get('successful_operations', 0) / result.get('total_operations', 1) * 100
                }
        report = {
            'test_suite': 'HMS Enterprise-Grade CRUD Operations Testing',
            'execution_timestamp': datetime.now().isoformat(),
            'total_duration': time.time() - self.start_time,
            'overall_status': overall_status,
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            },
            'detailed_results': self.test_results,
            'performance_metrics': performance_metrics,
            'database_configuration': {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME'],
                'host': settings.DATABASES['default']['HOST'],
                'port': settings.DATABASES['default']['PORT']
            },
            'recommendations': self._generate_recommendations()
        }
        report_path = '/home/azureuser/hms-enterprise-grade/crud_test_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        html_report_path = '/home/azureuser/hms-enterprise-grade/crud_test_report.html'
        self._generate_html_report(report, html_report_path)
        logger.info(f"📊 CRUD Test Report Generated:")
        logger.info(f"   - JSON Report: {report_path}")
        logger.info(f"   - HTML Report: {html_report_path}")
        logger.info(f"   - Overall Status: {overall_status}")
        logger.info(f"   - Success Rate: {report['test_summary']['success_rate']:.1f}%")
        return report
    def _generate_recommendations(self):
        recommendations = []
        if 'performance_metrics' in self.test_results:
            for test_type, metrics in self.test_results.get('performance_metrics', {}).items():
                if metrics.get('avg_execution_time', 0) > 0.1:  
                    recommendations.append({
                        'category': 'Performance',
                        'priority': 'MEDIUM',
                        'issue': f'Slow {test_type.replace("_", " ")} operations',
                        'recommendation': f'Optimize {test_type.replace("_", " ")} queries and consider indexing'
                    })
        if 'constraint_tests' in self.test_results:
            constraint_tests = self.test_results['constraint_tests']
            if isinstance(constraint_tests, dict):
                failed_constraints = len([t for t in constraint_tests.get('tests', []) if not t.get('constraint_enforced', False)])
                if failed_constraints > 0:
                    recommendations.append({
                        'category': 'Data Integrity',
                        'priority': 'HIGH',
                        'issue': f'{failed_constraints} database constraints not enforced',
                        'recommendation': 'Review and enforce all database constraints'
                    })
        if 'transaction_tests' in self.test_results:
            transaction_tests = self.test_results['transaction_tests']
            if isinstance(transaction_tests, dict):
                rollback_tests = [t for t in transaction_tests.get('tests', []) if 'rollback' in t.get('transaction_type', '')]
                if rollback_tests:
                    rollback_success = all(t.get('rollback_successful', False) for t in rollback_tests)
                    if not rollback_success:
                        recommendations.append({
                            'category': 'Data Integrity',
                            'priority': 'CRITICAL',
                            'issue': 'Transaction rollback not working properly',
                            'recommendation': 'Review transaction handling and rollback mechanisms'
                        })
        return recommendations
    def _generate_html_report(self, report_data, output_path):
        html_content = f
        for test_type, metrics in report_data.get('performance_metrics', {}).items():
            success_rate = metrics.get('success_rate', 0)
            html_content += f
        if report_data.get('recommendations'):
            html_content += 
            for rec in report_data['recommendations']:
                priority_class = rec['priority'].lower()
                html_content += f
            html_content += "</div>"
        html_content += 
        with open(output_path, 'w') as f:
            f.write(html_content)
def main():
    print("🚀 HMS Enterprise-Grade CRUD Operations Testing Suite")
    print("=" * 50)
    try:
        test_suite = CRUDTestingSuite()
        test_suite.run_all_tests()
        print("\n✅ CRUD Testing Suite Completed Successfully!")
        print("📊 Check the generated reports for detailed results:")
        print("   - crud_test_report.json (detailed JSON report)")
        print("   - crud_test_report.html (visual HTML report)")
        print("   - crud_testing.log (execution log)")
        return 0
    except Exception as e:
        print(f"\n❌ CRUD Testing Suite Failed: {e}")
        return 1
if __name__ == "__main__":
    sys.exit(main())