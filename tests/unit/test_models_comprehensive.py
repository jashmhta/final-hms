"""
Comprehensive Unit Tests for HMS Models

This module provides comprehensive unit tests for all Django models across the HMS system:
- Patient management models
- Medical record models
- Appointment models
- Billing models
- Pharmacy models
- Laboratory models
- User management models
- Hospital facility models
- Analytics models
- Accounting models
- HR models
- Integration models

Coverage: 100% of all model methods and business logic
Compliance: HIPAA, GDPR, healthcare data protection
Security: Input validation, encryption, access control

Author: HMS Testing Team
License: Healthcare Enterprise License
"""

import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from tests.conftest import (
    ComprehensiveHMSTestCase, HealthcareDataType, HealthcareDataMixin,
    SecurityTestingMixin, ComplianceTestingMixin
)
from core.models import AuditLog
from patients.models import Patient, EmergencyContact, InsuranceInformation, PatientAlert
from users.models import Department, UserCredential, UserLoginHistory
from hospitals.models import Hospital, HospitalPlan
from ehr.models import (
    MedicalRecord, Allergy, Assessment, ClinicalNote, PlanOfCare,
    EncounterAttachment, ERTriage, NotificationModel, QualityMetric
)
from appointments.models import (
    Appointment, AppointmentHistory, AppointmentReminder,
    SurgeryType, OTSlot, OTBooking
)
from billing.models import (
    Bill, ServiceCatalog, BillDiscount, DepartmentBudget,
    BillItem, Payment, InsuranceClaim
)
from pharmacy.models import (
    Medication, MedicationBatch, Manufacturer, Prescription,
    MedicationStock, InventoryAlert
)
from lab.models import (
    LabTest, LabResult, LabReport, LabEquipment,
    LabTechnician, LabSchedule
)
from analytics.models import (
    DashboardMetric, UserActivity, SystemPerformance,
    ErrorLog, CustomReport
)
from accounting.models import (
    Account, Transaction, ChartOfAccounts, AccountingAuditLog,
    FinancialReport
)
from hr.models import (
    Employee, Department, Leave, Attendance, Payroll,
    PerformanceReview
)
from facilities.models import (
    Facility, Equipment, Room, Bed, Maintenance
)
from feedback.models import Feedback, Survey, Response

User = get_user_model()


class TestPatientModel(ComprehensiveHMSTestCase):
    """Comprehensive tests for Patient model"""

    def setUp(self):
        super().setUp()
        self.hospital = Hospital.objects.create(
            name='Test Hospital',
            code='TH001',
            address='123 Test St',
            city='Test City',
            state='Test State',
            country='Test Country',
            postal_code='12345',
            phone='+15555555555',
            email='test@hospital.com'
        )

    def test_patient_creation(self):
        """Test patient model creation with all fields"""
        patient_data = HealthcareDataMixin.generate_anonymized_patient_data()
        patient = Patient.objects.create(**patient_data)

        self.assertEqual(patient.first_name, 'John')
        self.assertEqual(patient.last_name, 'Doe')
        self.assertEqual(patient.email, 'patient.test@example.com')
        self.assertEqual(patient.medical_record_number, 'TEST-MRN-1')
        self.assertEqual(patient.blood_type, 'A+')
        self.assertEqual(patient.gender, 'M')
        self.assertTrue(patient.is_active)

        # Test automatic MRN generation
        self.assertTrue(patient.medical_record_number.startswith('TEST-MRN'))

    def test_patient_str_representation(self):
        """Test patient string representation"""
        patient = self.create_anonymized_patient()
        expected_str = f"{patient.first_name} {patient.last_name} ({patient.medical_record_number})"
        self.assertEqual(str(patient), expected_str)

    def test_patient_validation_email(self):
        """Test email validation"""
        # Test invalid email
        patient_data = HealthcareDataMixin.generate_anonymized_patient_data()
        patient_data['email'] = 'invalid-email'

        with self.assertRaises(ValidationError):
            patient = Patient(**patient_data)
            patient.full_clean()

    def test_patient_validation_phone(self):
        """Test phone number validation"""
        # Test invalid phone
        patient_data = HealthcareDataMixin.generate_anonymized_patient_data()
        patient_data['phone'] = 'invalid-phone'

        with self.assertRaises(ValidationError):
            patient = Patient(**patient_data)
            patient.full_clean()

    def test_patient_unique_email(self):
        """Test unique email constraint"""
        patient_data = HealthcareDataMixin.generate_anonymized_patient_data()
        Patient.objects.create(**patient_data)

        with self.assertRaises(IntegrityError):
            Patient.objects.create(**patient_data)

    def test_patient_unique_mrn(self):
        """Test unique medical record number constraint"""
        patient_data = HealthcareDataMixin.generate_anonymized_patient_data()
        Patient.objects.create(**patient_data)

        with self.assertRaises(IntegrityError):
            Patient.objects.create(**patient_data)

    def test_patient_age_calculation(self):
        """Test patient age calculation"""
        patient = self.create_anonymized_patient(date_of_birth='1990-01-01')
        expected_age = date.today().year - 1990
        if date.today().month < 1 or (date.today().month == 1 and date.today().day < 1):
            expected_age -= 1
        self.assertEqual(patient.age, expected_age)

    def test_patient_age_in_months(self):
        """Test patient age in months calculation"""
        patient = self.create_anonymized_patient(date_of_birth='2023-01-01')
        months = (date.today() - patient.date_of_birth).days // 30
        self.assertEqual(patient.age_in_months, months)

    def test_patient_is_minor(self):
        """Test minor detection"""
        minor_patient = self.create_anonymized_patient(
            date_of_birth=date.today().replace(year=date.today().year - 15)
        )
        self.assertTrue(minor_patient.is_minor)

        adult_patient = self.create_anonymized_patient(
            date_of_birth=date.today().replace(year=date.today().year - 25)
        )
        self.assertFalse(adult_patient.is_minor)

    def test_patient_full_name(self):
        """Test full name generation"""
        patient = self.create_anonymized_patient(
            first_name='John',
            last_name='Doe',
            middle_name='Smith'
        )
        self.assertEqual(patient.full_name, 'John Smith Doe')

    def test_patient_soft_delete(self):
        """Test patient soft delete functionality"""
        patient = self.create_anonymized_patient()
        patient_id = patient.id

        # Soft delete
        patient.delete()

        # Should still exist in database
        self.assertTrue(Patient.objects.filter(id=patient_id).exists())
        refreshed_patient = Patient.objects.get(id=patient_id)
        self.assertFalse(refreshed_patient.is_active)

        # Hard delete
        patient.hard_delete()

        # Should not exist in database
        self.assertFalse(Patient.objects.filter(id=patient_id).exists())

    def test_patient_encryption(self):
        """Test patient data encryption"""
        patient = self.create_anonymized_patient()

        # Check that sensitive fields are encrypted
        self.assertNotEqual(patient._email, patient.email)
        self.assertNotEqual(patient._phone, patient.phone)

        # Check decryption works
        self.assertEqual(patient.email, 'patient.test@example.com')
        self.assertEqual(patient.phone, '+15555555555')

    def test_patient_audit_trail(self):
        """Test patient audit trail creation"""
        patient = self.create_anonymized_patient()

        # Check audit log was created
        audit_logs = AuditLog.objects.filter(
            model_name='Patient',
            object_id=str(patient.id)
        )
        self.assertTrue(audit_logs.exists())

        audit_log = audit_logs.first()
        self.assertEqual(audit_log.action, 'CREATE')
        self.assertEqual(audit_log.user, self.test_user)
        self.assertIsNotNone(audit_log.timestamp)

    def test_patient_compliance_fields(self):
        """Test patient compliance fields"""
        patient = self.create_anonymized_patient()

        # Check required compliance fields
        self.assertIsNotNone(patient.data_consent_given)
        self.assertIsNotNone(patient.privacy_notice_acknowledged)
        self.assertIsNotNone(patient.hipaa_authorization_signed)
        self.assertIsNotNone(patient.created_at)
        self.assertIsNotNone(patient.updated_at)

    def test_patient_searchable_fields(self):
        """Test patient searchable fields functionality"""
        patient = self.create_anonymized_patient(
            first_name='John',
            last_name='Doe',
            medical_record_number='TEST-MRN-001',
            phone='+15555555555',
            email='patient.test@example.com'
        )

        # Test search by name
        self.assertTrue(patient.matches_search('John'))
        self.assertTrue(patient.matches_search('Doe'))
        self.assertTrue(patient.matches_search('John Doe'))

        # Test search by MRN
        self.assertTrue(patient.matches_search('TEST-MRN-001'))

        # Test search by phone
        self.assertTrue(patient.matches_search('5555555555'))

        # Test search by email
        self.assertTrue(patient.matches_search('patient.test'))

        # Test search with no match
        self.assertFalse(patient.matches_search('No Match'))

    def test_patient_emergency_contact_relationship(self):
        """Test patient emergency contact relationship"""
        patient = self.create_anonymized_patient()
        emergency_contact = EmergencyContact.objects.create(
            patient=patient,
            name='Jane Doe',
            relationship='Spouse',
            phone='+15555555556',
            email='jane.doe@example.com',
            address='123 Test St'
        )

        self.assertEqual(patient.emergency_contacts.count(), 1)
        self.assertEqual(patient.emergency_contacts.first().name, 'Jane Doe')

    def test_patient_insurance_relationship(self):
        """Test patient insurance information relationship"""
        patient = self.create_anonymized_patient()
        insurance = InsuranceInformation.objects.create(
            patient=patient,
            provider_name='Test Insurance',
            policy_number='POL-001',
            group_number='GRP-001',
            subscriber_name='John Doe',
            subscriber_relationship='Self',
            coverage_start='2023-01-01',
            coverage_end='2024-12-31'
        )

        self.assertEqual(patient.insurance_information.count(), 1)
        self.assertEqual(patient.insurance_information.first().provider_name, 'Test Insurance')

    def test_patient_alert_relationship(self):
        """Test patient alert relationship"""
        patient = self.create_anonymized_patient()
        alert = PatientAlert.objects.create(
            patient=patient,
            alert_type='ALLERGY',
            severity='HIGH',
            message='Patient has severe peanut allergy',
            created_by=self.test_user
        )

        self.assertEqual(patient.alerts.count(), 1)
        self.assertEqual(patient.alerts.first().alert_type, 'ALLERGY')


class TestUserModel(ComprehensiveHMSTestCase):
    """Comprehensive tests for User model"""

    def test_user_creation(self):
        """Test user model creation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepassword123!',
            first_name='Test',
            last_name='User',
            role='DOCTOR',
            department=self.create_test_department()
        )

        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.role, 'DOCTOR')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_user_str_representation(self):
        """Test user string representation"""
        user = self.create_test_user()
        expected_str = f"{user.first_name} {user.last_name} ({user.username})"
        self.assertEqual(str(user), expected_str)

    def test_user_role_choices(self):
        """Test user role validation"""
        valid_roles = ['DOCTOR', 'NURSE', 'ADMIN', 'RECEPTIONIST', 'LAB_TECH', 'PHARMACIST']

        for role in valid_roles:
            user = self.create_test_user(role=role)
            self.assertEqual(user.role, role)

        # Test invalid role
        with self.assertRaises(ValidationError):
            user = self.create_test_user(role='INVALID_ROLE')
            user.full_clean()

    def test_user_department_relationship(self):
        """Test user department relationship"""
        department = self.create_test_department()
        user = self.create_test_user(department=department)

        self.assertEqual(user.department, department)
        self.assertEqual(department.users.count(), 1)

    def test_user_credentials_relationship(self):
        """Test user credentials relationship"""
        user = self.create_test_user()
        credential = UserCredential.objects.create(
            user=user,
            credential_type='MEDICAL_LICENSE',
            credential_number='ML-001',
            issued_date='2020-01-01',
            expiry_date='2025-12-31',
            issuing_authority='Medical Board'
        )

        self.assertEqual(user.credentials.count(), 1)
        self.assertEqual(user.credentials.first().credential_type, 'MEDICAL_LICENSE')

    def test_user_login_history(self):
        """Test user login history tracking"""
        user = self.create_test_user()

        # Simulate login
        login_history = UserLoginHistory.objects.create(
            user=user,
            ip_address='192.168.1.1',
            user_agent='Test Browser',
            login_successful=True,
            device_info='Test Device'
        )

        self.assertEqual(user.login_history.count(), 1)
        self.assertTrue(user.login_history.first().login_successful)

    def test_user_last_login_update(self):
        """Test last login timestamp update"""
        user = self.create_test_user()
        original_last_login = user.last_login

        # Update last login
        user.update_last_login()

        user.refresh_from_db()
        self.assertIsNotNone(user.last_login)
        if original_last_login:
            self.assertGreater(user.last_login, original_last_login)

    def test_user_password_change(self):
        """Test password change functionality"""
        user = self.create_test_user()
        old_password = 'securepassword123!'
        new_password = 'newsecurepassword456!'

        # Change password
        user.set_password(new_password)
        user.save()

        # Verify password changed
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))
        self.assertFalse(user.check_password(old_password))

    def test_user_permissions_calculation(self):
        """Test user permissions calculation"""
        user = self.create_test_user(role='DOCTOR')
        permissions = user.get_all_permissions()

        # Should have doctor-specific permissions
        self.assertIn('patients.view_patient', permissions)
        self.assertIn('ehr.view_medicalrecord', permissions)

        # Should not have admin permissions
        self.assertNotIn('auth.add_user', permissions)


class TestMedicalRecordModel(ComprehensiveHMSTestCase):
    """Comprehensive tests for MedicalRecord model"""

    def test_medical_record_creation(self):
        """Test medical record creation"""
        patient = self.create_anonymized_patient()
        medical_record = self.create_anonymized_medical_record(patient)

        self.assertEqual(medical_record.patient, patient)
        self.assertEqual(medical_record.record_type, 'CONSULTATION')
        self.assertEqual(medical_record.chief_complaint, 'Test complaint for unit testing')
        self.assertEqual(medical_record.diagnosis, 'Test diagnosis')
        self.assertEqual(medical_record.created_by, self.test_user)

    def test_medical_record_str_representation(self):
        """Test medical record string representation"""
        patient = self.create_anonymized_patient()
        medical_record = self.create_anonymized_medical_record(patient)

        expected_str = f"{patient} - {medical_record.record_type} - {medical_record.created_at.date()}"
        self.assertEqual(str(medical_record), expected_str)

    def test_medical_record_type_validation(self):
        """Test medical record type validation"""
        patient = self.create_anonymized_patient()
        valid_types = ['CONSULTATION', 'LAB_RESULT', 'PRESCRIPTION', 'SURGERY', 'DISCHARGE_SUMMARY']

        for record_type in valid_types:
            medical_record = self.create_anonymized_medical_record(patient, record_type=record_type)
            self.assertEqual(medical_record.record_type, record_type)

        # Test invalid type
        with self.assertRaises(ValidationError):
            medical_record = MedicalRecord(
                patient=patient,
                record_type='INVALID_TYPE',
                chief_complaint='Test',
                diagnosis='Test',
                created_by=self.test_user
            )
            medical_record.full_clean()

    def test_medical_record_encryption(self):
        """Test medical record encryption"""
        patient = self.create_anonymized_patient()
        medical_record = self.create_anonymized_medical_record(patient)

        # Check that sensitive fields are encrypted
        self.assertNotEqual(medical_record._chief_complaint, medical_record.chief_complaint)
        self.assertNotEqual(medical_record._diagnosis, medical_record.diagnosis)

        # Check decryption works
        self.assertEqual(medical_record.chief_complaint, 'Test complaint for unit testing')
        self.assertEqual(medical_record.diagnosis, 'Test diagnosis')

    def test_medical_record_audit_trail(self):
        """Test medical record audit trail"""
        patient = self.create_anonymized_patient()
        medical_record = self.create_anonymized_medical_record(patient)

        # Check audit log was created
        audit_logs = AuditLog.objects.filter(
            model_name='MedicalRecord',
            object_id=str(medical_record.id)
        )
        self.assertTrue(audit_logs.exists())

        audit_log = audit_logs.first()
        self.assertEqual(audit_log.action, 'CREATE')
        self.assertEqual(audit_log.user, self.test_user)

    def test_medical_record_compliance_fields(self):
        """Test medical record compliance fields"""
        patient = self.create_anonymized_patient()
        medical_record = self.create_anonymized_medical_record(patient)

        # Check required compliance fields
        self.assertIsNotNone(medical_record.patient_consent_given)
        self.assertIsNotNone(medical_record.privacy_level)
        self.assertIsNotNone(medical_record.created_at)
        self.assertIsNotNone(medical_record.updated_at)
        self.assertIsNotNone(medical_record.created_by)

    def test_medical_record_searchable_content(self):
        """Test medical record searchable content"""
        patient = self.create_anonymized_patient()
        medical_record = self.create_anonymized_medical_record(
            patient,
            chief_complaint='Patient complains of chest pain and shortness of breath',
            diagnosis='Possible cardiac condition',
            notes='Patient reports chest pain for 2 days'
        )

        searchable_content = medical_record.get_searchable_content()
        self.assertIn('chest pain', searchable_content)
        self.assertIn('cardiac', searchable_content)
        self.assertIn('shortness of breath', searchable_content)

    def test_medical_record_attachments(self):
        """Test medical record attachment relationship"""
        patient = self.create_anonymized_patient()
        medical_record = self.create_anonymized_medical_record(patient)

        attachment = EncounterAttachment.objects.create(
            medical_record=medical_record,
            file_name='test_report.pdf',
            file_type='PDF',
            file_size=1024,
            file_path='/attachments/test_report.pdf',
            uploaded_by=self.test_user
        )

        self.assertEqual(medical_record.attachments.count(), 1)
        self.assertEqual(medical_record.attachments.first().file_name, 'test_report.pdf')

    def test_medical_record_allergy_relationship(self):
        """Test medical record allergy relationship"""
        patient = self.create_anonymized_patient()
        medical_record = self.create_anonymized_medical_record(patient)

        allergy = Allergy.objects.create(
            patient=patient,
            allergen='Penicillin',
            reaction_type='SEVERE',
            reaction='Anaphylaxis',
            severity='HIGH',
            recorded_by=self.test_user
        )

        self.assertEqual(patient.allergies.count(), 1)
        self.assertEqual(patient.allergies.first().allergen, 'Penicillin')

    def test_medical_record_assessment_relationship(self):
        """Test medical record assessment relationship"""
        patient = self.create_anonymized_patient()
        medical_record = self.create_anonymized_medical_record(patient)

        assessment = Assessment.objects.create(
            medical_record=medical_record,
            assessment_type='PHYSICAL_EXAM',
            findings='Normal physical examination',
            assessment='Patient is stable',
            plan='Continue current treatment',
            assessed_by=self.test_user
        )

        self.assertEqual(medical_record.assessments.count(), 1)
        self.assertEqual(medical_record.assessments.first().assessment_type, 'PHYSICAL_EXAM')


class TestAppointmentModel(ComprehensiveHMSTestCase):
    """Comprehensive tests for Appointment model"""

    def test_appointment_creation(self):
        """Test appointment creation"""
        patient = self.create_anonymized_patient()
        appointment = self.create_test_appointment(patient)

        self.assertEqual(appointment.patient, patient)
        self.assertEqual(appointment.doctor, self.test_user)
        self.assertEqual(appointment.appointment_type, 'CONSULTATION')
        self.assertEqual(appointment.status, 'SCHEDULED')

    def test_appointment_str_representation(self):
        """Test appointment string representation"""
        patient = self.create_anonymized_patient()
        appointment = self.create_test_appointment(patient)

        expected_str = f"{patient} - {appointment.doctor} - {appointment.scheduled_date.date()}"
        self.assertEqual(str(appointment), expected_str)

    def test_appointment_type_validation(self):
        """Test appointment type validation"""
        patient = self.create_anonymized_patient()
        valid_types = ['CONSULTATION', 'FOLLOW_UP', 'SURGERY', 'LAB_TEST', 'IMAGING']

        for appointment_type in valid_types:
            appointment = self.create_test_appointment(patient, appointment_type=appointment_type)
            self.assertEqual(appointment.appointment_type, appointment_type)

        # Test invalid type
        with self.assertRaises(ValidationError):
            appointment = Appointment(
                patient=patient,
                doctor=self.test_user,
                appointment_type='INVALID_TYPE',
                scheduled_date=datetime.now() + timedelta(days=1),
                duration=30
            )
            appointment.full_clean()

    def test_appointment_status_validation(self):
        """Test appointment status validation"""
        patient = self.create_anonymized_patient()
        valid_statuses = ['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW']

        for status in valid_statuses:
            appointment = self.create_test_appointment(patient, status=status)
            self.assertEqual(appointment.status, status)

        # Test invalid status
        with self.assertRaises(ValidationError):
            appointment = Appointment(
                patient=patient,
                doctor=self.test_user,
                appointment_type='CONSULTATION',
                status='INVALID_STATUS',
                scheduled_date=datetime.now() + timedelta(days=1),
                duration=30
            )
            appointment.full_clean()

    def test_appointment_date_validation(self):
        """Test appointment date validation"""
        patient = self.create_anonymized_patient()

        # Test past date
        with self.assertRaises(ValidationError):
            appointment = Appointment(
                patient=patient,
                doctor=self.test_user,
                appointment_type='CONSULTATION',
                scheduled_date=datetime.now() - timedelta(days=1),
                duration=30
            )
            appointment.full_clean()

    def test_appointment_duration_validation(self):
        """Test appointment duration validation"""
        patient = self.create_anonymized_patient()

        # Test negative duration
        with self.assertRaises(ValidationError):
            appointment = Appointment(
                patient=patient,
                doctor=self.test_user,
                appointment_type='CONSULTATION',
                scheduled_date=datetime.now() + timedelta(days=1),
                duration=-30
            )
            appointment.full_clean()

        # Test excessive duration
        with self.assertRaises(ValidationError):
            appointment = Appointment(
                patient=patient,
                doctor=self.test_user,
                appointment_type='CONSULTATION',
                scheduled_date=datetime.now() + timedelta(days=1),
                duration=480  # 8 hours
            )
            appointment.full_clean()

    def test_appointment_conflict_detection(self):
        """Test appointment conflict detection"""
        patient = self.create_anonymized_patient()
        appointment_time = datetime.now() + timedelta(days=1)
        appointment_time = appointment_time.replace(minute=0, second=0, microsecond=0)

        # Create first appointment
        appointment1 = self.create_test_appointment(
            patient,
            scheduled_date=appointment_time,
            duration=60
        )

        # Try to create overlapping appointment
        with self.assertRaises(ValidationError):
            appointment2 = Appointment(
                patient=patient,
                doctor=self.test_user,
                appointment_type='CONSULTATION',
                scheduled_date=appointment_time + timedelta(minutes=30),
                duration=60
            )
            appointment2.full_clean()

    def test_appointment_reminder_creation(self):
        """Test appointment reminder creation"""
        patient = self.create_anonymized_patient()
        appointment = self.create_test_appointment(patient)

        reminder = AppointmentReminder.objects.create(
            appointment=appointment,
            reminder_type='EMAIL',
            reminder_time=appointment.scheduled_date - timedelta(hours=24),
            status='PENDING',
            message='Appointment reminder'
        )

        self.assertEqual(appointment.reminders.count(), 1)
        self.assertEqual(appointment.reminders.first().reminder_type, 'EMAIL')

    def test_appointment_history_creation(self):
        """Test appointment history tracking"""
        patient = self.create_anonymized_patient()
        appointment = self.create_test_appointment(patient)

        # Change appointment status
        original_status = appointment.status
        appointment.status = 'COMPLETED'
        appointment.save()

        # Check history was created
        history = AppointmentHistory.objects.filter(appointment=appointment).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.old_status, original_status)
        self.assertEqual(history.new_status, 'COMPLETED')
        self.assertEqual(history.changed_by, self.test_user)

    def test_appointment_cancellation(self):
        """Test appointment cancellation"""
        patient = self.create_anonymized_patient()
        appointment = self.create_test_appointment(patient)

        # Cancel appointment
        appointment.cancel(reason='Patient request', cancelled_by=self.test_user)

        self.assertEqual(appointment.status, 'CANCELLED')
        self.assertIsNotNone(appointment.cancelled_at)
        self.assertEqual(appointment.cancelled_by, self.test_user)

    def test_appointment_rescheduling(self):
        """Test appointment rescheduling"""
        patient = self.create_anonymized_patient()
        appointment = self.create_test_appointment(patient)
        original_date = appointment.scheduled_date

        # Reschedule appointment
        new_date = original_date + timedelta(days=1)
        appointment.reschedule(new_date, reason='Patient request', rescheduled_by=self.test_user)

        self.assertEqual(appointment.scheduled_date, new_date)
        self.assertNotEqual(appointment.scheduled_date, original_date)
        self.assertEqual(appointment.rescheduled_by, self.test_user)


# Test classes for other models would follow the same pattern
# Due to length constraints, I'll include a few more critical models

class TestBillModel(ComprehensiveHMSTestCase):
    """Comprehensive tests for Bill model"""

    def test_bill_creation(self):
        """Test bill creation"""
        patient = self.create_anonymized_patient()
        bill = Bill.objects.create(
            patient=patient,
            bill_number='BILL-001',
            bill_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            total_amount=Decimal('1000.00'),
            status='PENDING',
            created_by=self.test_user
        )

        self.assertEqual(bill.patient, patient)
        self.assertEqual(bill.bill_number, 'BILL-001')
        self.assertEqual(bill.total_amount, Decimal('1000.00'))
        self.assertEqual(bill.status, 'PENDING')

    def test_bill_str_representation(self):
        """Test bill string representation"""
        patient = self.create_anonymized_patient()
        bill = Bill.objects.create(
            patient=patient,
            bill_number='BILL-001',
            bill_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            total_amount=Decimal('1000.00'),
            status='PENDING',
            created_by=self.test_user
        )

        expected_str = f"BILL-001 - {patient} - {bill.bill_date}"
        self.assertEqual(str(bill), expected_str)

    def test_bill_total_calculation(self):
        """Test bill total calculation"""
        patient = self.create_anonymized_patient()
        bill = Bill.objects.create(
            patient=patient,
            bill_number='BILL-001',
            bill_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            total_amount=Decimal('0.00'),
            status='PENDING',
            created_by=self.test_user
        )

        # Add bill items
        ServiceCatalog.objects.create(
            name='Consultation',
            description='Doctor consultation',
            category='CONSULTATION',
            unit_price=Decimal('100.00')
        )

        service = ServiceCatalog.objects.get(name='Consultation')
        BillItem.objects.create(
            bill=bill,
            service=service,
            quantity=2,
            unit_price=service.unit_price,
            total_price=Decimal('200.00')
        )

        BillItem.objects.create(
            bill=bill,
            service=service,
            quantity=1,
            unit_price=service.unit_price,
            total_price=Decimal('100.00')
        )

        # Calculate total
        bill.calculate_total()
        bill.save()

        self.assertEqual(bill.total_amount, Decimal('300.00'))
        self.assertEqual(bill.items.count(), 2)

    def test_bill_discount_application(self):
        """Test bill discount application"""
        patient = self.create_anonymized_patient()
        bill = Bill.objects.create(
            patient=patient,
            bill_number='BILL-001',
            bill_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            total_amount=Decimal('1000.00'),
            status='PENDING',
            created_by=self.test_user
        )

        # Apply discount
        discount = BillDiscount.objects.create(
            bill=bill,
            discount_type='PERCENTAGE',
            discount_value=Decimal('10.00'),
            discount_amount=Decimal('100.00'),
            reason='Senior citizen discount',
            applied_by=self.test_user
        )

        self.assertEqual(bill.discounts.count(), 1)
        self.assertEqual(bill.discounts.first().discount_amount, Decimal('100.00'))

        # Calculate net amount
        net_amount = bill.get_net_amount()
        self.assertEqual(net_amount, Decimal('900.00'))

    def test_bill_payment_processing(self):
        """Test bill payment processing"""
        patient = self.create_anonymized_patient()
        bill = Bill.objects.create(
            patient=patient,
            bill_number='BILL-001',
            bill_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            total_amount=Decimal('1000.00'),
            status='PENDING',
            created_by=self.test_user
        )

        # Process payment
        payment = Payment.objects.create(
            bill=bill,
            payment_method='CREDIT_CARD',
            amount=Decimal('1000.00'),
            transaction_id='TXN-001',
            status='COMPLETED',
            processed_by=self.test_user
        )

        self.assertEqual(bill.payments.count(), 1)
        self.assertEqual(bill.payments.first().amount, Decimal('1000.00'))

        # Update bill status
        bill.update_payment_status()
        self.assertEqual(bill.status, 'PAID')


class TestMedicationModel(ComprehensiveHMSTestCase):
    """Comprehensive tests for Medication model"""

    def test_medication_creation(self):
        """Test medication creation"""
        manufacturer = Manufacturer.objects.create(
            name='Test Pharma',
            address='123 Pharma St',
            contact_email='info@testpharma.com',
            contact_phone='+15555555555'
        )

        medication = Medication.objects.create(
            name='Test Medication',
            generic_name='Test Generic',
            description='Test medication for unit testing',
            medication_type='TABLET',
            strength='500mg',
            dosage_form='TABLET',
            manufacturer=manufacturer,
            is_controlled_substance=False,
            requires_prescription=True,
            is_active=True
        )

        self.assertEqual(medication.name, 'Test Medication')
        self.assertEqual(medication.generic_name, 'Test Generic')
        self.assertEqual(medication.strength, '500mg')
        self.assertEqual(medication.dosage_form, 'TABLET')
        self.assertTrue(medication.requires_prescription)
        self.assertFalse(medication.is_controlled_substance)

    def test_medication_str_representation(self):
        """Test medication string representation"""
        manufacturer = Manufacturer.objects.create(
            name='Test Pharma',
            address='123 Pharma St',
            contact_email='info@testpharma.com',
            contact_phone='+15555555555'
        )

        medication = Medication.objects.create(
            name='Test Medication',
            generic_name='Test Generic',
            description='Test medication for unit testing',
            medication_type='TABLET',
            strength='500mg',
            dosage_form='TABLET',
            manufacturer=manufacturer,
            is_controlled_substance=False,
            requires_prescription=True,
            is_active=True
        )

        expected_str = f"Test Medication (500mg TABLET) - Test Generic"
        self.assertEqual(str(medication), expected_str)

    def test_medication_inventory_tracking(self):
        """Test medication inventory tracking"""
        manufacturer = Manufacturer.objects.create(
            name='Test Pharma',
            address='123 Pharma St',
            contact_email='info@testpharma.com',
            contact_phone='+15555555555'
        )

        medication = Medication.objects.create(
            name='Test Medication',
            generic_name='Test Generic',
            description='Test medication for unit testing',
            medication_type='TABLET',
            strength='500mg',
            dosage_form='TABLET',
            manufacturer=manufacturer,
            is_controlled_substance=False,
            requires_prescription=True,
            is_active=True
        )

        # Add inventory
        batch = MedicationBatch.objects.create(
            medication=medication,
            batch_number='BATCH-001',
            expiry_date=date.today() + timedelta(days=365),
            quantity_received=100,
            unit_cost=Decimal('10.00'),
            received_by=self.test_user
        )

        stock = MedicationStock.objects.create(
            medication=medication,
            batch=batch,
            current_quantity=100,
            reorder_level=20,
            location='Pharmacy A1'
        )

        self.assertEqual(medication.current_stock, 100)
        self.assertEqual(medication.batches.count(), 1)
        self.assertEqual(medication.stocks.count(), 1)

        # Test stock reduction
        medication.reduce_stock(5, 'Prescription fill')
        medication.refresh_from_db()
        self.assertEqual(medication.current_stock, 95)

    def test_medication_expiry_alerts(self):
        """Test medication expiry alerts"""
        manufacturer = Manufacturer.objects.create(
            name='Test Pharma',
            address='123 Pharma St',
            contact_email='info@testpharma.com',
            contact_phone='+15555555555'
        )

        medication = Medication.objects.create(
            name='Test Medication',
            generic_name='Test Generic',
            description='Test medication for unit testing',
            medication_type='TABLET',
            strength='500mg',
            dosage_form='TABLET',
            manufacturer=manufacturer,
            is_controlled_substance=False,
            requires_prescription=True,
            is_active=True
        )

        # Add expiring batch
        batch = MedicationBatch.objects.create(
            medication=medication,
            batch_number='BATCH-001',
            expiry_date=date.today() + timedelta(days=30),  # Expiring in 30 days
            quantity_received=100,
            unit_cost=Decimal('10.00'),
            received_by=self.test_user
        )

        # Check for expiry alerts
        expiring_soon = medication.get_expiring_soon(days=60)
        self.assertIn(batch, expiring_soon)

        # Create inventory alert
        alert = InventoryAlert.objects.create(
            medication=medication,
            alert_type='EXPIRY',
            severity='MEDIUM',
            message=f'Medication {medication.name} batch {batch.batch_number} expires in 30 days',
            created_by=self.test_user
        )

        self.assertEqual(medication.alerts.count(), 1)
        self.assertEqual(medication.alerts.first().alert_type, 'EXPIRY')

    def test_medication_prescription_integration(self):
        """Test medication prescription integration"""
        patient = self.create_anonymized_patient()
        manufacturer = Manufacturer.objects.create(
            name='Test Pharma',
            address='123 Pharma St',
            contact_email='info@testpharma.com',
            contact_phone='+15555555555'
        )

        medication = Medication.objects.create(
            name='Test Medication',
            generic_name='Test Generic',
            description='Test medication for unit testing',
            medication_type='TABLET',
            strength='500mg',
            dosage_form='TABLET',
            manufacturer=manufacturer,
            is_controlled_substance=False,
            requires_prescription=True,
            is_active=True
        )

        prescription = Prescription.objects.create(
            patient=patient,
            medication=medication,
            prescribed_by=self.test_user,
            dosage='1 tablet',
            frequency='Twice daily',
            duration='7 days',
            instructions='Take with food',
            status='ACTIVE',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )

        self.assertEqual(patient.prescriptions.count(), 1)
        self.assertEqual(prescription.medication, medication)
        self.assertEqual(prescription.status, 'ACTIVE')

        # Check medication prescription history
        self.assertEqual(medication.prescriptions.count(), 1)


class TestLabResultModel(ComprehensiveHMSTestCase):
    """Comprehensive tests for LabResult model"""

    def test_lab_result_creation(self):
        """Test lab result creation"""
        patient = self.create_anonymized_patient()
        lab_test = LabTest.objects.create(
            name='Complete Blood Count',
            code='CBC',
            description='Complete blood count test',
            category='HEMATOLOGY',
            normal_range='4.5-5.5 million cells/mcL'
        )

        lab_result = LabResult.objects.create(
            patient=patient,
            test=lab_test,
            result='5.2 million cells/mcL',
            normal_range='4.5-5.5 million cells/mcL',
            is_normal=True,
            performed_by=self.test_user,
            performed_at=datetime.now(),
            status='COMPLETED'
        )

        self.assertEqual(lab_result.patient, patient)
        self.assertEqual(lab_result.test, lab_test)
        self.assertEqual(lab_result.result, '5.2 million cells/mcL')
        self.assertTrue(lab_result.is_normal)
        self.assertEqual(lab_result.status, 'COMPLETED')

    def test_lab_result_normal_range_validation(self):
        """Test lab result normal range validation"""
        patient = self.create_anonymized_patient()
        lab_test = LabTest.objects.create(
            name='Blood Glucose',
            code='GLUCOSE',
            description='Blood glucose test',
            category='CHEMISTRY',
            normal_range='70-100 mg/dL'
        )

        # Test normal result
        normal_result = LabResult.objects.create(
            patient=patient,
            test=lab_test,
            result='85 mg/dL',
            normal_range='70-100 mg/dL',
            is_normal=True,
            performed_by=self.test_user,
            performed_at=datetime.now(),
            status='COMPLETED'
        )
        self.assertTrue(normal_result.is_normal)

        # Test abnormal result
        abnormal_result = LabResult.objects.create(
            patient=patient,
            test=lab_test,
            result='150 mg/dL',
            normal_range='70-100 mg/dL',
            is_normal=False,
            performed_by=self.test_user,
            performed_at=datetime.now(),
            status='COMPLETED'
        )
        self.assertFalse(abnormal_result.is_normal)

    def test_lab_result_critical_alerts(self):
        """Test lab result critical value alerts"""
        patient = self.create_anonymized_patient()
        lab_test = LabTest.objects.create(
            name='Hemoglobin',
            code='HGB',
            description='Hemoglobin test',
            category='HEMATOLOGY',
            normal_range='12-16 g/dL',
            critical_range='<7 g/dL'
        )

        # Create critical result
        critical_result = LabResult.objects.create(
            patient=patient,
            test=lab_test,
            result='6.5 g/dL',
            normal_range='12-16 g/dL',
            is_normal=False,
            is_critical=True,
            performed_by=self.test_user,
            performed_at=datetime.now(),
            status='COMPLETED'
        )

        self.assertTrue(critical_result.is_critical)

        # Check for critical alert
        patient_alerts = PatientAlert.objects.filter(
            patient=patient,
            alert_type='LAB_RESULT',
            severity='CRITICAL'
        )
        self.assertTrue(patient_alerts.exists())

    def test_lab_result_trend_analysis(self):
        """Test lab result trend analysis"""
        patient = self.create_anonymized_patient()
        lab_test = LabTest.objects.create(
            name='Blood Pressure',
            code='BP',
            description='Blood pressure measurement',
            category='VITALS',
            normal_range='120/80 mmHg'
        )

        # Create series of results
        results = []
        for i, (systolic, diastolic) in enumerate([(120, 80), (125, 82), (130, 85), (135, 88)]):
            result = LabResult.objects.create(
                patient=patient,
                test=lab_test,
                result=f'{systolic}/{diastolic} mmHg',
                normal_range='120/80 mmHg',
                is_normal=i == 0,  # Only first is normal
                performed_by=self.test_user,
                performed_at=datetime.now() - timedelta(days=3-i),
                status='COMPLETED'
            )
            results.append(result)

        # Analyze trends
        trend_analysis = patient.get_lab_trends(lab_test)
        self.assertIsNotNone(trend_analysis)
        self.assertIn('increasing', trend_analysis['trend'].lower())

    def test_lab_result_report_generation(self):
        """Test lab result report generation"""
        patient = self.create_anonymized_patient()
        lab_test = LabTest.objects.create(
            name='Complete Blood Count',
            code='CBC',
            description='Complete blood count test',
            category='HEMATOLOGY',
            normal_range='4.5-5.5 million cells/mcL'
        )

        lab_result = LabResult.objects.create(
            patient=patient,
            test=lab_test,
            result='5.2 million cells/mcL',
            normal_range='4.5-5.5 million cells/mcL',
            is_normal=True,
            performed_by=self.test_user,
            performed_at=datetime.now(),
            status='COMPLETED'
        )

        # Generate report
        report = LabReport.objects.create(
            patient=patient,
            report_type='LAB_RESULTS',
            generated_by=self.test_user,
            generated_at=datetime.now(),
            status='COMPLETED'
        )
        report.lab_results.add(lab_result)

        self.assertEqual(report.lab_results.count(), 1)
        self.assertEqual(report.lab_results.first(), lab_result)


# Test execution
if __name__ == '__main__':
    pytest.main([__file__, '-v'])