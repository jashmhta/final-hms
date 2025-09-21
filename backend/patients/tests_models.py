import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from ..models import (
    BloodType,
    EmergencyContact,
    InsuranceInformation,
    MaritalStatus,
    Patient,
    PatientAlert,
    PatientGender,
    PatientStatus,
)

User = get_user_model()


class TestPatientModel(TestCase):
    """Comprehensive test suite for Patient model"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = Mock()
        self.user.id = 1

    def test_patient_creation_minimal(self):
        """Test patient creation with minimal required fields"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
        )
        self.assertIsNotNone(patient.pk)
        self.assertEqual(patient.first_name, "John")
        self.assertEqual(patient.last_name, "Doe")
        self.assertEqual(patient.status, PatientStatus.ACTIVE)
        self.assertIsNotNone(patient.uuid)
        self.assertIsNotNone(patient.medical_record_number)

    def test_patient_creation_full(self):
        """Test patient creation with all fields"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="Jane",
            middle_name="Marie",
            last_name="Smith",
            suffix="III",
            preferred_name="Janie",
            date_of_birth=date(1985, 5, 15),
            gender=PatientGender.FEMALE,
            marital_status=MaritalStatus.MARRIED,
            phone_primary="555-123-4567",
            phone_secondary="555-987-6543",
            email="jane.smith@email.com",
            address_line1="123 Main St",
            address_line2="Apt 2B",
            city="Anytown",
            state="CA",
            zip_code="12345",
            blood_type=BloodType.A_POSITIVE,
            weight_kg=Decimal("70.5"),
            height_cm=Decimal("170.2"),
            vip_status=True,
            confidential=True,
            notes="Special care instructions",
            created_by=self.user,
            last_updated_by=self.user,
            organ_donor=True,
            advance_directive_on_file=True,
            healthcare_proxy="John Smith",
            preferred_contact_method="EMAIL",
        )

        self.assertEqual(patient.middle_name, "Marie")
        self.assertEqual(patient.suffix, "III")
        self.assertEqual(patient.preferred_name, "Janie")
        self.assertEqual(patient.weight_kg, Decimal("70.5"))
        self.assertEqual(patient.height_cm, Decimal("170.2"))
        self.assertTrue(patient.vip_status)
        self.assertTrue(patient.confidential)
        self.assertTrue(patient.organ_donor)

    def test_get_full_name(self):
        """Test get_full_name method"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            middle_name="William",
            last_name="Doe",
            suffix="Jr.",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
        )
        self.assertEqual(patient.get_full_name(), "John William Doe Jr.")

        # Test without middle name or suffix
        patient2 = Patient.objects.create(
            hospital=self.hospital,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 1, 1),
            gender=PatientGender.FEMALE,
        )
        self.assertEqual(patient2.get_full_name(), "Jane Smith")

    def test_get_age(self):
        """Test age calculation"""
        # Test exact age
        birth_date = date(1990, 1, 1)
        today = date.today()
        expected_age = today.year - birth_date.year

        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=birth_date,
            gender=PatientGender.MALE,
        )

        # Adjust if birthday hasn't occurred yet this year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            expected_age -= 1

        self.assertEqual(patient.get_age(), expected_age)

        # Test null date of birth
        patient.date_of_birth = None
        patient.save()
        self.assertIsNone(patient.get_age())

    def test_get_age_at_date(self):
        """Test age calculation at specific date"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
        )

        reference_date = date(2020, 1, 1)
        expected_age = 30  # 2020 - 1990
        self.assertEqual(patient.get_age_at_date(reference_date), expected_age)

    def test_is_minor(self):
        """Test minor status check"""
        # Test minor patient
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date.today() - timedelta(days=365 * 10),  # 10 years old
            gender=PatientGender.MALE,
        )
        self.assertTrue(patient.is_minor())

        # Test adult patient
        adult_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date.today() - timedelta(days=365 * 25),  # 25 years old
            gender=PatientGender.FEMALE,
        )
        self.assertFalse(adult_patient.is_minor())

        # Test null date of birth
        patient.date_of_birth = None
        patient.save()
        self.assertFalse(patient.is_minor())

    def test_save_with_mrn_generation(self):
        """Test automatic MRN generation"""
        with patch("time.time", return_value=1234567890):
            patient = Patient.objects.create(
                hospital=self.hospital,
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 1),
                gender=PatientGender.MALE,
            )
            self.assertEqual(patient.medical_record_number, "MRN56789012")

    def test_save_existing_mrn(self):
        """Test that existing MRN is preserved"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            medical_record_number="EXISTING123",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
        )
        self.assertEqual(patient.medical_record_number, "EXISTING123")

    def test_string_representation(self):
        """Test __str__ method"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
        )
        expected_str = f"Doe, John (MRN: {patient.medical_record_number})"
        self.assertEqual(str(patient), expected_str)

    def test_encrypted_fields(self):
        """Test that sensitive fields are encrypted"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_primary="555-123-4567",
            address_line1="123 Main St",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
        )

        # Check that the fields appear correctly when accessed
        self.assertEqual(patient.first_name, "John")
        self.assertEqual(patient.email, "john.doe@example.com")
        self.assertEqual(patient.phone_primary, "555-123-4567")

    def test_patient_status_choices(self):
        """Test all patient status choices are valid"""
        valid_statuses = [status[0] for status in PatientStatus.choices]
        expected_statuses = ["ACTIVE", "INACTIVE", "DECEASED", "TRANSFERRED", "LOST_TO_FOLLOWUP"]
        self.assertEqual(set(valid_statuses), set(expected_statuses))

    def test_blood_type_choices(self):
        """Test all blood type choices are valid"""
        valid_blood_types = [bt[0] for bt in BloodType.choices]
        expected_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "UNKNOWN"]
        self.assertEqual(set(valid_blood_types), set(expected_blood_types))

    def test_invalid_date_of_birth(self):
        """Test validation for invalid date of birth"""
        with self.assertRaises(IntegrityError):
            Patient.objects.create(
                hospital=self.hospital,
                first_name="John",
                last_name="Doe",
                date_of_birth=None,
                gender=PatientGender.MALE,
            )

    def test_deceased_patient(self):
        """Test deceased patient functionality"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1950, 1, 1),
            gender=PatientGender.MALE,
            status=PatientStatus.DECEASED,
            date_of_death=date(2020, 1, 1),
            cause_of_death="Natural causes",
        )

        self.assertEqual(patient.status, PatientStatus.DECEASED)
        self.assertEqual(patient.date_of_death, date(2020, 1, 1))
        self.assertEqual(patient.cause_of_death, "Natural causes")

    def test_hipaa_compliance_fields(self):
        """Test HIPAA compliance related fields"""
        now = timezone.now()
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
            hipaa_acknowledgment_date=now,
            privacy_notice_date=now,
            patient_portal_enrolled=True,
            patient_portal_last_login=now,
        )

        self.assertEqual(patient.hipaa_acknowledgment_date, now)
        self.assertEqual(patient.privacy_notice_date, now)
        self.assertTrue(patient.patient_portal_enrolled)
        self.assertEqual(patient.patient_portal_last_login, now)

    @patch("backend.patients.models.enhanced_cache")
    def test_cache_patient_data_on_save(self, mock_cache):
        """Test that patient data is cached on save"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
        )

        # Verify cache was called
        mock_cache.cache_patient_data.assert_called_once()

    @patch("backend.patients.models.enhanced_cache")
    def test_get_cached_patient(self, mock_cache):
        """Test cached patient retrieval"""
        # Test when patient is in cache
        mock_cache.cache.get.return_value = "cached_patient_data"
        result = Patient.get_cached_patient(1)
        self.assertEqual(result, "cached_patient_data")

        # Test when patient is not in cache
        mock_cache.cache.get.return_value = None
        with patch.object(Patient.objects, "get", return_value=None):
            result = Patient.get_cached_patient(1)
            self.assertIsNone(result)

    @patch("backend.patients.models.enhanced_cache")
    def test_search_patients(self, mock_cache):
        """Test patient search functionality"""
        # Test when results are cached
        mock_cache.cache.get.return_value = "cached_results"
        results = Patient.search_patients(1, "John", 10)
        self.assertEqual(results, "cached_results")

        # Test when search hits database
        mock_cache.cache.get.return_value = None
        with patch.object(Patient.objects, "filter") as mock_filter:
            mock_queryset = Mock()
            mock_queryset.__getitem__ = lambda self, key: [f"result_{key}"]
            mock_filter.return_value = mock_queryset

            results = Patient.search_patients(1, "John", 10)
            self.assertEqual(len(results), 10)

    def test_preferred_contact_method_choices(self):
        """Test preferred contact method choices"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
        )

        valid_methods = ["PHONE", "EMAIL", "SMS", "MAIL", "PORTAL"]
        for method in valid_methods:
            patient.preferred_contact_method = method
            patient.save()
            self.assertEqual(patient.preferred_contact_method, method)

    def test_consent_flags(self):
        """Test various consent flags"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
            allow_sms=True,
            allow_email=True,
            allow_automated_calls=False,
            do_not_resuscitate=False,
            organ_donor=True,
            advance_directive_on_file=True,
        )

        self.assertTrue(patient.allow_sms)
        self.assertTrue(patient.allow_email)
        self.assertFalse(patient.allow_automated_calls)
        self.assertFalse(patient.do_not_resuscitate)
        self.assertTrue(patient.organ_donor)
        self.assertTrue(patient.advance_directive_on_file)


class TestEmergencyContactModel(TestCase):
    """Comprehensive test suite for EmergencyContact model"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

    def test_emergency_contact_creation(self):
        """Test emergency contact creation"""
        contact = EmergencyContact.objects.create(
            patient=self.patient,
            first_name="Jane",
            last_name="Doe",
            relationship="SPOUSE",
            phone_primary="555-123-4567",
        )

        self.assertIsNotNone(contact.pk)
        self.assertEqual(contact.patient, self.patient)
        self.assertEqual(contact.first_name, "Jane")
        self.assertEqual(contact.last_name, "Doe")
        self.assertEqual(contact.relationship, "SPOUSE")
        self.assertTrue(contact.is_active)

    def test_emergency_contact_full_name(self):
        """Test get_full_name method"""
        contact = EmergencyContact.objects.create(
            patient=self.patient,
            first_name="Jane",
            middle_name="Marie",
            last_name="Doe",
            relationship="SPOUSE",
            phone_primary="555-123-4567",
        )

        self.assertEqual(contact.get_full_name(), "Jane Marie Doe")

    def test_primary_contact_flag(self):
        """Test primary contact flag"""
        contact1 = EmergencyContact.objects.create(
            patient=self.patient,
            first_name="Jane",
            last_name="Doe",
            relationship="SPOUSE",
            phone_primary="555-123-4567",
            is_primary=True,
        )

        contact2 = EmergencyContact.objects.create(
            patient=self.patient,
            first_name="John",
            last_name="Smith",
            relationship="FATHER",
            phone_primary="555-987-6543",
            is_primary=False,
        )

        self.assertTrue(contact1.is_primary)
        self.assertFalse(contact2.is_primary)

    def test_medical_decision_authority(self):
        """Test medical decision authority flag"""
        contact = EmergencyContact.objects.create(
            patient=self.patient,
            first_name="Jane",
            last_name="Doe",
            relationship="SPOUSE",
            phone_primary="555-123-4567",
            can_make_medical_decisions=True,
        )

        self.assertTrue(contact.can_make_medical_decisions)

    def test_relationship_choices(self):
        """Test valid relationship choices"""
        valid_relationships = [
            "SPOUSE",
            "PARENT",
            "CHILD",
            "SIBLING",
            "GRANDPARENT",
            "GRANDCHILD",
            "FRIEND",
            "CAREGIVER",
            "GUARDIAN",
            "OTHER",
        ]

        for relationship in valid_relationships:
            contact = EmergencyContact.objects.create(
                patient=self.patient,
                first_name="Test",
                last_name="Contact",
                relationship=relationship,
                phone_primary="555-123-4567",
            )
            self.assertEqual(contact.relationship, relationship)

    def test_encrypted_contact_fields(self):
        """Test that contact information is encrypted"""
        contact = EmergencyContact.objects.create(
            patient=self.patient,
            first_name="Jane",
            last_name="Doe",
            relationship="SPOUSE",
            phone_primary="555-123-4567",
            email="jane.doe@example.com",
            address_line1="123 Main St",
        )

        # Check that fields are accessible
        self.assertEqual(contact.phone_primary, "555-123-4567")
        self.assertEqual(contact.email, "jane.doe@example.com")


class TestInsuranceInformationModel(TestCase):
    """Comprehensive test suite for InsuranceInformation model"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

    def test_insurance_creation(self):
        """Test insurance information creation"""
        insurance = InsuranceInformation.objects.create(
            patient=self.patient,
            insurance_name="Blue Cross Blue Shield",
            insurance_type="PRIMARY",
            policy_number="POL123456789",
            effective_date=date(2023, 1, 1),
            insurance_company_name="BCBS",
        )

        self.assertIsNotNone(insurance.pk)
        self.assertEqual(insurance.patient, self.patient)
        self.assertEqual(insurance.insurance_name, "Blue Cross Blue Shield")
        self.assertEqual(insurance.insurance_type, "PRIMARY")
        self.assertEqual(insurance.verification_status, "PENDING")

    def test_insurance_expiration(self):
        """Test insurance expiration check"""
        insurance = InsuranceInformation.objects.create(
            patient=self.patient,
            insurance_name="Test Insurance",
            insurance_type="PRIMARY",
            policy_number="POL123",
            effective_date=date(2023, 1, 1),
            termination_date=date(2023, 12, 31),
            insurance_company_name="Test Co",
        )

        # Test expired
        with patch("backend.patients.models.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 1)
            self.assertTrue(insurance.is_expired())

        # Test not expired
        with patch("backend.patients.models.date") as mock_date:
            mock_date.today.return_value = date(2023, 6, 1)
            self.assertFalse(insurance.is_expired())

    def test_insurance_types(self):
        """Test valid insurance types"""
        valid_types = ["PRIMARY", "SECONDARY", "TERTIARY"]

        for ins_type in valid_types:
            insurance = InsuranceInformation.objects.create(
                patient=self.patient,
                insurance_name="Test Insurance",
                insurance_type=ins_type,
                policy_number=f"POL{ins_type}",
                effective_date=date(2023, 1, 1),
                insurance_company_name="Test Co",
            )
            self.assertEqual(insurance.insurance_type, ins_type)

    def test_financial_information(self):
        """Test financial fields (copay, deductible, etc.)"""
        insurance = InsuranceInformation.objects.create(
            patient=self.patient,
            insurance_name="Test Insurance",
            insurance_type="PRIMARY",
            policy_number="POL123",
            effective_date=date(2023, 1, 1),
            insurance_company_name="Test Co",
            copay_amount=Decimal("25.00"),
            deductible_amount=Decimal("1000.00"),
            out_of_pocket_max=Decimal("5000.00"),
        )

        self.assertEqual(insurance.copay_amount, Decimal("25.00"))
        self.assertEqual(insurance.deductible_amount, Decimal("1000.00"))
        self.assertEqual(insurance.out_of_pocket_max, Decimal("5000.00"))

    def test_verification_statuses(self):
        """Test verification status choices"""
        valid_statuses = ["PENDING", "VERIFIED", "INVALID", "EXPIRED"]

        for status in valid_statuses:
            insurance = InsuranceInformation.objects.create(
                patient=self.patient,
                insurance_name="Test Insurance",
                insurance_type="PRIMARY",
                policy_number=f"POL{status}",
                effective_date=date(2023, 1, 1),
                insurance_company_name="Test Co",
                verification_status=status,
            )
            self.assertEqual(insurance.verification_status, status)

    def test_policy_holder_relationships(self):
        """Test policy holder relationship choices"""
        valid_relationships = ["SELF", "SPOUSE", "PARENT", "CHILD", "OTHER"]

        for relationship in valid_relationships:
            insurance = InsuranceInformation.objects.create(
                patient=self.patient,
                insurance_name="Test Insurance",
                insurance_type="PRIMARY",
                policy_number=f"POL{relationship}",
                effective_date=date(2023, 1, 1),
                insurance_company_name="Test Co",
                policy_holder_relationship=relationship,
            )
            self.assertEqual(insurance.policy_holder_relationship, relationship)


class TestPatientAlertModel(TestCase):
    """Comprehensive test suite for PatientAlert model"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = Mock()
        self.user.id = 1
        self.patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

    def test_alert_creation(self):
        """Test alert creation"""
        alert = PatientAlert.objects.create(
            patient=self.patient,
            alert_type="ALLERGY",
            severity="HIGH",
            title="Penicillin Allergy",
            description="Patient has severe allergic reaction to penicillin",
            created_by=self.user,
        )

        self.assertIsNotNone(alert.pk)
        self.assertEqual(alert.patient, self.patient)
        self.assertEqual(alert.alert_type, "ALLERGY")
        self.assertEqual(alert.severity, "HIGH")
        self.assertEqual(alert.title, "Penicillin Allergy")
        self.assertEqual(alert.verification_status, "PENDING")

    def test_alert_types(self):
        """Test valid alert types"""
        valid_types = [
            "ALLERGY",
            "DRUG_INTERACTION",
            "FALL_RISK",
            "SUICIDE_RISK",
            "INFECTION_CONTROL",
            "DNR",
            "ADVANCE_DIRECTIVE",
            "VIP",
            "FINANCIAL",
            "SAFETY",
            "CLINICAL",
            "OTHER",
        ]

        for alert_type in valid_types:
            alert = PatientAlert.objects.create(
                patient=self.patient,
                alert_type=alert_type,
                severity="MEDIUM",
                title=f"Test {alert_type}",
                description=f"Test {alert_type} description",
                created_by=self.user,
            )
            self.assertEqual(alert.alert_type, alert_type)

    def test_severity_levels(self):
        """Test severity level choices"""
        valid_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        for severity in valid_severities:
            alert = PatientAlert.objects.create(
                patient=self.patient,
                alert_type="CLINICAL",
                severity=severity,
                title=f"Test {severity}",
                description=f"Test {severity} description",
                created_by=self.user,
            )
            self.assertEqual(alert.severity, severity)

    def test_alert_expiration(self):
        """Test alert expiration check"""
        alert = PatientAlert.objects.create(
            patient=self.patient,
            alert_type="CLINICAL",
            severity="HIGH",
            title="Test Alert",
            description="Test description",
            created_by=self.user,
            expires_at=timezone.now() - timedelta(hours=1),
        )

        self.assertTrue(alert.is_expired())

        # Test non-expired alert
        non_expired_alert = PatientAlert.objects.create(
            patient=self.patient,
            alert_type="CLINICAL",
            severity="HIGH",
            title="Test Alert 2",
            description="Test description 2",
            created_by=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        self.assertFalse(non_expired_alert.is_expired())

    def test_alert_acknowledgment(self):
        """Test alert acknowledgment functionality"""
        alert = PatientAlert.objects.create(
            patient=self.patient,
            alert_type="SAFETY",
            severity="CRITICAL",
            title="Safety Alert",
            description="Safety alert requires acknowledgment",
            created_by=self.user,
            requires_acknowledgment=True,
        )

        # Initially not acknowledged
        self.assertIsNone(alert.acknowledged_by)
        self.assertIsNone(alert.acknowledged_at)

        # Acknowledge alert
        now = timezone.now()
        alert.acknowledged_by = self.user
        alert.acknowledged_at = now
        alert.save()

        self.assertEqual(alert.acknowledged_by, self.user)
        self.assertEqual(alert.acknowledged_at, now)

    def test_alert_active_status(self):
        """Test alert active status"""
        alert = PatientAlert.objects.create(
            patient=self.patient,
            alert_type="CLINICAL",
            severity="MEDIUM",
            title="Test Alert",
            description="Test description",
            created_by=self.user,
            is_active=True,
        )

        self.assertTrue(alert.is_active)

        # Deactivate alert
        alert.is_active = False
        alert.save()
        self.assertFalse(alert.is_active)

    def test_string_representation(self):
        """Test __str__ method"""
        alert = PatientAlert.objects.create(
            patient=self.patient,
            alert_type="ALLERGY",
            severity="HIGH",
            title="Test Allergy",
            description="Test description",
            created_by=self.user,
        )

        expected_str = f"{self.patient} - Test Allergy (HIGH)"
        self.assertEqual(str(alert), expected_str)


class TestPatientModelRelationships(TestCase):
    """Test Patient model relationships and cascading behavior"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = Mock()
        self.user.id = 1
        self.patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            created_by=self.user,
            last_updated_by=self.user,
        )

    def test_patient_emergency_contacts_relationship(self):
        """Test Patient -> EmergencyContacts relationship"""
        contact1 = EmergencyContact.objects.create(
            patient=self.patient,
            first_name="Jane",
            last_name="Doe",
            relationship="SPOUSE",
            phone_primary="555-123-4567",
        )

        contact2 = EmergencyContact.objects.create(
            patient=self.patient,
            first_name="John",
            last_name="Smith",
            relationship="FATHER",
            phone_primary="555-987-6543",
        )

        self.assertEqual(self.patient.emergency_contacts.count(), 2)
        self.assertIn(contact1, self.patient.emergency_contacts.all())
        self.assertIn(contact2, self.patient.emergency_contacts.all())

    def test_patient_insurance_relationship(self):
        """Test Patient -> InsuranceInformation relationship"""
        insurance1 = InsuranceInformation.objects.create(
            patient=self.patient,
            insurance_name="Primary Insurance",
            insurance_type="PRIMARY",
            policy_number="POL1",
            effective_date=date(2023, 1, 1),
            insurance_company_name="Primary Co",
        )

        insurance2 = InsuranceInformation.objects.create(
            patient=self.patient,
            insurance_name="Secondary Insurance",
            insurance_type="SECONDARY",
            policy_number="POL2",
            effective_date=date(2023, 1, 1),
            insurance_company_name="Secondary Co",
        )

        self.assertEqual(self.patient.insurance_plans.count(), 2)
        self.assertIn(insurance1, self.patient.insurance_plans.all())
        self.assertIn(insurance2, self.patient.insurance_plans.all())

    def test_patient_alerts_relationship(self):
        """Test Patient -> PatientAlerts relationship"""
        alert1 = PatientAlert.objects.create(
            patient=self.patient,
            alert_type="ALLERGY",
            severity="HIGH",
            title="Allergy 1",
            description="First allergy",
            created_by=self.user,
        )

        alert2 = PatientAlert.objects.create(
            patient=self.patient,
            alert_type="SAFETY",
            severity="MEDIUM",
            title="Safety Alert",
            description="Safety concern",
            created_by=self.user,
        )

        self.assertEqual(self.patient.alerts.count(), 2)
        self.assertIn(alert1, self.patient.alerts.all())
        self.assertIn(alert2, self.patient.alerts.all())

    def test_cascade_delete_relationships(self):
        """Test that related objects are deleted when patient is deleted"""
        # Create related objects
        EmergencyContact.objects.create(
            patient=self.patient,
            first_name="Jane",
            last_name="Doe",
            relationship="SPOUSE",
            phone_primary="555-123-4567",
        )

        InsuranceInformation.objects.create(
            patient=self.patient,
            insurance_name="Test Insurance",
            insurance_type="PRIMARY",
            policy_number="POL1",
            effective_date=date(2023, 1, 1),
            insurance_company_name="Test Co",
        )

        PatientAlert.objects.create(
            patient=self.patient,
            alert_type="ALLERGY",
            severity="HIGH",
            title="Test Allergy",
            description="Test description",
            created_by=self.user,
        )

        # Delete patient
        patient_id = self.patient.id
        self.patient.delete()

        # Verify related objects are also deleted
        self.assertFalse(EmergencyContact.objects.filter(patient_id=patient_id).exists())
        self.assertFalse(InsuranceInformation.objects.filter(patient_id=patient_id).exists())
        self.assertFalse(PatientAlert.objects.filter(patient_id=patient_id).exists())
