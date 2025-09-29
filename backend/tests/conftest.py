"""
Pytest configuration and shared fixtures for HMS testing
"""

import json
import os
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from factory.django import DjangoModelFactory
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

# from accounting.models import Account, ChartOfAccounts, JournalEntry, Transaction  # App not implemented
# from appointments.models import Appointment, AppointmentHistory, AppointmentReminder  # App not implemented
# from billing.models import Bill, BillLineItem, DepartmentBudget  # App not implemented
# from ehr.models import Allergy, ClinicalNote, Encounter, PlanOfCare, VitalSigns  # App not implemented
# from hospitals.models import Department, Hospital  # App not implemented
# from lab.models import LabOrder, LabResult, LabTest  # App not implemented
# from patients.models import (
#     EmergencyContact,
#     InsuranceInformation,
#     Patient,
#     PatientAlert,
# )  # App not implemented
# from pharmacy.models import Medication, MedicationBatch, Prescription  # App not implemented

User = get_user_model()


@pytest.fixture(scope="session")
def django_db_setup():
    """Session-wide database setup"""
    pass


@pytest.fixture
def api_client():
    """API client fixture"""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Authenticated API client fixture"""
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


# @pytest.fixture
# def hospital_factory():
#     """Hospital factory fixture"""

#     class HospitalFactory(DjangoModelFactory):
#         class Meta:
#             model = Hospital

#         name = "Test Hospital"
#         code = "TEST001"
#         address = "123 Test St"
#         city = "Test City"
#         state = "TS"
#         country = "Test Country"
#         phone = "+1234567890"
#         email = "test@hospital.com"
#         capacity = 100
#         is_active = True

#     return HospitalFactory


# @pytest.fixture
# def department_factory(hospital_factory):
#     """Department factory fixture"""

#     class DepartmentFactory(DjangoModelFactory):
#         class Meta:
#             model = Department

#         name = "Test Department"
#         code = "TEST_DEPT"
#         hospital = hospital_factory()
#         head = None
#         description = "Test department description"
#         is_active = True

# return DepartmentFactory


@pytest.fixture
def user_factory():
    """User factory fixture"""

    class UserFactory(DjangoModelFactory):
        class Meta:
            model = User

        username = "testuser"
        email = "test@example.com"
        first_name = "Test"
        last_name = "User"
        password = "SecurePass123!"
        role = "staff"
        is_active = True

        @classmethod
        def _create(cls, model_class, *args, **kwargs):
            """Override to use create_user for proper password hashing"""
            manager = cls._get_manager(model_class)
            return manager.create_user(*args, **kwargs)

    return UserFactory


@pytest.fixture
def test_user(user_factory):
    """Test user fixture"""
    return user_factory()


@pytest.fixture
def doctor_user(user_factory, hospital_factory):
    """Doctor user fixture"""
    return user_factory(
        username="doctor",
        email="doctor@hospital.com",
        role="doctor",
        hospital=hospital_factory(),
    )

    # @pytest.fixture
    # def patient_factory(hospital_factory, doctor_user):
    #     """Patient factory fixture"""

    #     class PatientFactory(DjangoModelFactory):
    #         class Meta:
    #             model = Patient

    #         first_name = "Test"
    #         last_name = "Patient"
    #         date_of_birth = date(1990, 1, 1)
    #         gender = "F"
    #         blood_type = "O+"
    #         phone_primary = "+1234567890"
    #         email = "patient@example.com"
    #         address = "123 Patient St"
    #         city = "Patient City"
    #         state = "PS"
    #         country = "Test Country"
    #         hospital = hospital_factory()
    #         primary_care_physician = doctor_user
    #         medical_record_number = "MRN123456"
    #         is_active = True

    #     return PatientFactory

    # @pytest.fixture
    # def test_patient(patient_factory):
    """Test patient fixture"""
    return patient_factory()

    # @pytest.fixture
    # def appointment_factory(hospital_factory, test_patient, doctor_user):
    """Appointment factory fixture"""

    class AppointmentFactory(DjangoModelFactory):
        class Meta:
            model = Appointment

        hospital = hospital_factory()
        patient = test_patient
        primary_provider = doctor_user
        appointment_type = "consultation"
        status = "scheduled"
        start_at = timezone.now() + timedelta(days=1)
        end_at = timezone.now() + timedelta(days=1, minutes=30)
        is_active = True

    return AppointmentFactory


# @pytest.fixture
# def encounter_factory(hospital_factory, test_patient, doctor_user):
#     """Encounter factory fixture"""

#     class EncounterFactory(DjangoModelFactory):
#         class Meta:
#             model = Encounter

#         hospital = hospital_factory()
#         patient = test_patient
#         primary_physician = doctor_user
#         encounter_type = "outpatient"
#         encounter_status = "scheduled"
#         scheduled_start = timezone.now()
#         is_active = True

#     return EncounterFactory


# @pytest.fixture
# def medication_factory(hospital_factory):
#     """Medication factory fixture"""

#     class MedicationFactory(DjangoModelFactory):
#         class Meta:
#             model = Medication

#         hospital = hospital_factory()
#         name = "Test Medication"
#         generic_name = "Test Generic"
#         strength = "500mg"
#         dosage_form = "tablet"
#         ndc = "12345-678-90"
#         stock_quantity = 100
#         reorder_level = 20
#         is_controlled = False
#         is_active = True

#     return MedicationFactory


# @pytest.fixture
# def lab_test_factory(hospital_factory):
#     """Lab test factory fixture"""

#     class LabTestFactory(DjangoModelFactory):
#         class Meta:
#             model = LabTest

#         hospital = hospital_factory()
#         name = "Complete Blood Count"
#         code = "CBC"
#         description = "Complete blood count test"
#         category = "hematology"
#         turnaround_time_hours = 24
#         active = True

#     return LabTestFactory


# @pytest.fixture
# def bill_factory(hospital_factory, test_patient):
#     """Bill factory fixture"""

#     class BillFactory(DjangoModelFactory):
#         class Meta:
#             model = Bill

#         hospital = hospital_factory()
#         patient = test_patient
#         status = "pending"
#         total_cents = 10000
#         insurance_claim_status = "pending"
#         is_active = True

#     return BillFactory


@pytest.fixture
def sample_test_data():
    """Sample test data for various scenarios"""
    return {
        "patient": {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "gender": "M",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
        },
        "appointment": {
            "appointment_type": "consultation",
            "duration_minutes": 30,
            "status": "scheduled",
        },
        "vital_signs": {
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 72,
            "temperature": 98.6,
            "oxygen_saturation": 98,
            "respiratory_rate": 16,
        },
        "medication": {
            "name": "Test Medication",
            "dosage": "1 tablet",
            "frequency": "twice daily",
            "duration": "7 days",
        },
    }


@pytest.fixture
def mock_external_services():
    """Mock external services"""
    return {
        "email_service": MagicMock(),
        "sms_service": MagicMock(),
        "payment_gateway": MagicMock(),
        "insurance_service": MagicMock(),
        "notification_service": MagicMock(),
    }


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test"""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def test_encryption():
    """Test encryption fixture"""
    from cryptography.fernet import Fernet

    key = Fernet.generate_key()
    cipher_suite = Fernet(key)

    return {
        "key": key,
        "cipher_suite": cipher_suite,
        "encrypt": cipher_suite.encrypt,
        "decrypt": cipher_suite.decrypt,
    }


@pytest.fixture
def performance_test_data():
    """Performance test data"""
    return {
        "large_dataset_size": 1000,
        "concurrent_users": 100,
        "response_time_threshold": 2.0,
        "throughput_threshold": 100,
    }


@pytest.fixture
def security_test_data():
    """Security test data"""
    return {
        "sql_injection_payloads": [
            "1; DROP TABLE users; --",
            "' OR '1'='1",
            "1 UNION SELECT * FROM users",
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ],
        "invalid_tokens": ["invalid_token", "", "null", "undefined"],
    }


@pytest.fixture
def compliance_test_data():
    """Compliance test data"""
    return {
        "hipaa_requirements": [
            "data_encryption",
            "access_control",
            "audit_logging",
            "data_retention",
        ],
        "gdpr_requirements": [
            "consent_management",
            "data_portability",
            "right_to_be_forgotten",
        ],
        "patient_data_fields": [
            "first_name",
            "last_name",
            "date_of_birth",
            "medical_record_number",
            "diagnosis",
        ],
    }


@pytest.fixture
def api_test_data():
    """API test data"""
    return {
        "endpoints": [
            "/api/patients/",
            "/api/appointments/",
            "/api/ehr/",
            "/api/billing/",
            "/api/pharmacy/",
        ],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "content_types": ["application/json", "application/xml"],
    }


@pytest.fixture
def database_test_data():
    """Database test data"""
    return {
        "table_names": [
            "patients_patient",
            "ehr_encounter",
            "appointments_appointment",
            "billing_bill",
            "pharmacy_medication",
        ],
        "index_columns": [
            "id",
            "hospital_id",
            "patient_id",
            "created_at",
            "updated_at",
        ],
        "constraint_types": ["PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK"],
    }


@pytest.fixture
def load_test_config():
    """Load test configuration"""
    return {
        "duration_seconds": 60,
        "users": 100,
        "spawn_rate": 10,
        "host": "http://localhost:8000",
        "endpoints": ["/api/health/", "/api/patients/", "/api/appointments/"],
    }


@pytest.fixture
def accessibility_test_data():
    """Accessibility test data"""
    return {
        "wcag_criteria": [
            "1.1.1",  # Non-text content
            "1.3.1",  # Info and relationships
            "2.1.1",  # Keyboard accessible
            "2.4.1",  # Bypass blocks
            "3.3.2",  # Labels or instructions
            "4.1.1",  # Compatible
        ],
        "axe_rules": ["color-contrast", "image-alt", "label", "link-name", "list"],
    }


@pytest.fixture
def visual_regression_test_data():
    """Visual regression test data"""
    return {
        "pages": ["/login", "/dashboard", "/patients", "/appointments"],
        "components": ["header", "navigation", "patient-card", "appointment-form"],
        "viewports": [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 768, "height": 1024},  # Tablet
            {"width": 375, "height": 667},  # Mobile
        ],
    }


@pytest.fixture
def mobile_test_data():
    """Mobile test data"""
    return {
        "devices": ["iPhone 12", "Samsung Galaxy S21", "iPad Pro"],
        "platforms": ["iOS", "Android"],
        "screen_sizes": [
            {"width": 375, "height": 667},
            {"width": 414, "height": 896},
            {"width": 768, "height": 1024},
        ],
    }


@pytest.fixture
def cross_browser_test_data():
    """Cross-browser test data"""
    return {
        "browsers": ["chrome", "firefox", "safari", "edge"],
        "versions": {
            "chrome": "latest",
            "firefox": "latest",
            "safari": "latest",
            "edge": "latest",
        },
        "platforms": ["Windows 10", "macOS Big Sur", "Ubuntu 20.04"],
    }


# Test markers for categorization
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line(
        "markers", "accessibility: marks tests as accessibility tests"
    )
    config.addinivalue_line("markers", "compliance: marks tests as compliance tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")
    config.addinivalue_line("markers", "database: marks tests as database tests")
    config.addinivalue_line("markers", "mobile: marks tests as mobile tests")
    config.addinivalue_line("markers", "contract: marks tests as contract tests")
    config.addinivalue_line("markers", "visual: marks tests as visual regression tests")


# Custom pytest hooks
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Custom test reporting"""
    if call.when == "call":
        if call.excinfo is None:
            # Test passed
            item.user_properties.append(("test_result", "passed"))
        else:
            # Test failed
            item.user_properties.append(("test_result", "failed"))
            item.user_properties.append(("failure_reason", str(call.excinfo.value)))


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test"""
    yield

    # Clean up database tables
    models_to_clear = [
        # Patient,  # Not imported
        # Encounter,  # Not imported
        # Appointment,  # Not imported
        # Bill,  # Not imported
        # Medication,  # Not imported
        # LabTest,  # Not imported
        User,
        # Hospital,  # Not imported
        # Department,  # Not imported
    ]

    for model in models_to_clear:
        try:
            model.objects.all().delete()
        except:
            pass


# Test environment setup
@pytest.fixture(scope="session", autouse=True)
def test_environment_setup():
    """Set up test environment"""
    # Set test environment variables
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hms.settings_test")
    os.environ.setdefault("TESTING", "true")
    os.environ.setdefault("DEBUG", "false")

    yield

    # Clean up
    for key in ["DJANGO_SETTINGS_MODULE", "TESTING", "DEBUG"]:
        os.environ.pop(key, None)


# Test utilities
@pytest.fixture
def test_utils():
    """Test utilities"""
    import json
    import uuid
    from datetime import datetime, timedelta

    class TestUtils:
        @staticmethod
        def generate_test_email():
            """Generate test email"""
            return f"test-{uuid.uuid4().hex[:8]}@example.com"

        @staticmethod
        def generate_test_phone():
            """Generate test phone number"""
            return f"+1{uuid.uuid4().hex[:10]}"

        @staticmethod
        def generate_future_date(days=1):
            """Generate future date"""
            return datetime.now() + timedelta(days=days)

        @staticmethod
        def generate_past_date(days=1):
            """Generate past date"""
            return datetime.now() - timedelta(days=days)

        @staticmethod
        def random_string(length=10):
            """Generate random string"""
            import random
            import string

            return "".join(
                random.choices(string.ascii_letters + string.digits, k=length)
            )

        @staticmethod
        def create_test_payload(data_dict):
            """Create test payload"""
            return json.dumps(data_dict)

    return TestUtils()
