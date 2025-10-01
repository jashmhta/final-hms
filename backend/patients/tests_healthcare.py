"""
tests_healthcare module
"""

import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from ..models import (
    EmergencyContact,
    InsuranceInformation,
    Patient,
    PatientAlert,
    PatientGender,
    PatientStatus,
)

User = get_user_model()


class HealthcareDataTests(TestCase):
    """Healthcare-specific test scenarios with anonymized patient data"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = User.objects.create_user(
            username='healthcare_user',
            email='healthcare@example.com',
            password='healthpass123',
            hospital=self.hospital,
            is_staff=True
        )

    def test_anonymized_patient_data_compliance(self):
        """Test that patient data is properly anonymized for testing"""
        # Create test patient with anonymized data
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="PATIENT_ANONYMIZED_001",
            last_name="TEST_LASTNAME",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
            email="test.anonymized.001@example.com",
            phone_primary="555-TEST-001",
            address_line1="123 TEST STREET",
            city="TEST CITY",
            state="TS",
            zip_code="12345"
        )

        # Verify data follows anonymization patterns
        self.assertTrue(patient.first_name.startswith("PATIENT_ANONYMIZED_"))
        self.assertTrue(patient.last_name.startswith("TEST_"))
        self.assertTrue(patient.email.startswith("test."))
        self.assertTrue(patient.email.endswith("@example.com"))
        self.assertTrue("TEST" in patient.phone_primary)
        self.assertEqual(patient.city, "TEST CITY")

    def test_hipaa_compliant_data_handling(self):
        """Test HIPAA-compliant data handling in tests"""
        # Create patient with sensitive health information
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_PATIENT",
            last_name="ANONYMIZED",
            date_of_birth=date(1985, 5, 15),
            gender=PatientGender.FEMALE,
            hipaa_acknowledgment_date=timezone.now(),
            privacy_notice_date=timezone.now(),
            confidential=True
        )

        # Add HIPAA-related information
        patient.healthcare_proxy = "TEST_PROXY_ANONYMIZED"
        patient.advance_directive_on_file = True
        patient.do_not_resuscitate = False
        patient.organ_donor = True
        patient.save()

        # Verify PHI (Protected Health Information) is handled appropriately
        self.assertIsNotNone(patient.hipaa_acknowledgment_date)
        self.assertIsNotNone(patient.privacy_notice_date)
        self.assertTrue(patient.confidential)

        # Test that encrypted fields contain test data, not real PHI
        self.assertIn("TEST", patient.healthcare_proxy)

    def test_medical_record_number_generation(self):
        """Test medical record number follows healthcare standards"""
        patient1 = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_PATIENT",
            last_name="ONE",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE
        )

        patient2 = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_PATIENT",
            last_name="TWO",
            date_of_birth=date(1985, 5, 15),
            gender=PatientGender.FEMALE
        )

        # Verify MRNs are unique and follow expected format
        self.assertNotEqual(patient1.medical_record_number, patient2.medical_record_number)
        self.assertTrue(patient1.medical_record_number.startswith("MRN"))
        self.assertTrue(patient2.medical_record_number.startswith("MRN"))
        self.assertEqual(len(patient1.medical_record_number), 12)  # MRN + 8 digits

    def test_patient_age_calculation_medical_scenarios(self):
        """Test age calculation for medical scenarios"""
        # Test pediatric patient
        pediatric_dob = date.today() - timedelta(days=365 * 5)  # 5 years old
        pediatric_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_PEDIATRIC",
            last_name="PATIENT",
            date_of_birth=pediatric_dob,
            gender=PatientGender.MALE
        )

        self.assertEqual(pediatric_patient.get_age(), 5)
        self.assertTrue(pediatric_patient.is_minor())

        # Test geriatric patient
        geriatric_dob = date.today() - timedelta(days=365 * 75)  # 75 years old
        geriatric_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_GERIATRIC",
            last_name="PATIENT",
            date_of_birth=geriatric_dob,
            gender=PatientGender.FEMALE
        )

        self.assertEqual(geriatric_patient.get_age(), 75)
        self.assertFalse(geriatric_patient.is_minor())

        # Test newborn patient
        newborn_dob = date.today() - timedelta(days=7)  # 7 days old
        newborn_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_NEWBORN",
            last_name="PATIENT",
            date_of_birth=newborn_dob,
            gender=PatientGender.MALE
        )

        self.assertEqual(newborn_patient.get_age(), 0)
        self.assertTrue(newborn_patient.is_minor())

    def test_blood_type_medical_compatibility(self):
        """Test blood type handling for medical scenarios"""
        blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

        for blood_type in blood_types:
            patient = Patient.objects.create(
                hospital=self.hospital,
                first_name="TEST_PATIENT",
                last_name=f"BLOOD_{blood_type.replace('+', 'P').replace('-', 'N')}",
                date_of_birth=date(1990, 1, 1),
                gender=PatientGender.MALE,
                blood_type=blood_type
            )

            self.assertEqual(patient.blood_type, blood_type)

    def test_medical_alert_scenarios(self):
        """Test medical alert scenarios for patient safety"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_ALERT_PATIENT",
            last_name="ANONYMIZED",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE
        )

        # Test critical allergy alert
        allergy_alert = PatientAlert.objects.create(
            patient=patient,
            alert_type="ALLERGY",
            severity="CRITICAL",
            title="Anaphylaxis to Penicillin",
            description="Patient has history of anaphylactic reaction to penicillin and related antibiotics",
            requires_acknowledgment=True,
            created_by=self.user
        )

        self.assertEqual(allergy_alert.severity, "CRITICAL")
        self.assertTrue(allergy_alert.requires_acknowledgment)
        self.assertIn("anaphylactic", allergy_alert.description.lower())

        # Test fall risk alert for elderly patient
        fall_risk_alert = PatientAlert.objects.create(
            patient=patient,
            alert_type="FALL_RISK",
            severity="HIGH",
            title="High Fall Risk",
            description="Patient has history of falls, requires assistance with ambulation",
            created_by=self.user
        )

        self.assertEqual(fall_risk_alert.alert_type, "FALL_RISK")

        # Test DNR (Do Not Resuscitate) alert
        dnr_alert = PatientAlert.objects.create(
            patient=patient,
            alert_type="DNR",
            severity="HIGH",
            title="DNR Order",
            description="Do Not Resuscitate order on file, signed by patient and physician",
            requires_acknowledgment=True,
            created_by=self.user
        )

        self.assertEqual(dnr_alert.alert_type, "DNR")

        # Test infection control alert
        infection_alert = PatientAlert.objects.create(
            patient=patient,
            alert_type="INFECTION_CONTROL",
            severity="HIGH",
            title="MRSA Positive",
            description="Patient tested positive for MRSA, contact precautions required",
            created_by=self.user
        )

        self.assertEqual(infection_alert.alert_type, "INFECTION_CONTROL")

    def test_medical_emergency_contact_management(self):
        """Test emergency contact management for medical scenarios"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_EMERGENCY",
            last_name="PATIENT",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.FEMALE
        )

        # Test spouse as emergency contact with medical decision authority
        spouse_contact = EmergencyContact.objects.create(
            patient=patient,
            first_name="TEST_SPOUSE",
            last_name="CONTACT",
            relationship="SPOUSE",
            phone_primary="555-SPOUSE-01",
            phone_secondary="555-SPOUSE-02",
            email="spouse.test@example.com",
            is_primary=True,
            can_make_medical_decisions=True
        )

        self.assertTrue(spouse_contact.is_primary)
        self.assertTrue(spouse_contact.can_make_medical_decisions)

        # Test healthcare proxy as emergency contact
        proxy_contact = EmergencyContact.objects.create(
            patient=patient,
            first_name="TEST_PROXY",
            last_name="CONTACT",
            relationship="GUARDIAN",
            phone_primary="555-PROXY-01",
            can_make_medical_decisions=True,
            notes="Healthcare proxy with full medical decision authority"
        )

        self.assertTrue(proxy_contact.can_make_medical_decisions)
        self.assertIn("Healthcare proxy", proxy_contact.notes)

        # Test multiple emergency contacts for comprehensive coverage
        parent_contact = EmergencyContact.objects.create(
            patient=patient,
            first_name="TEST_PARENT",
            last_name="CONTACT",
            relationship="PARENT",
            phone_primary="555-PARENT-01",
            preferred_contact_method="PHONE"
        )

        # Verify primary contact ordering
        self.assertEqual(patient.emergency_contacts.filter(is_primary=True).count(), 1)
        self.assertEqual(patient.emergency_contacts.filter(can_make_medical_decisions=True).count(), 2)

    def test_insurance_coverage_medical_scenarios(self):
        """Test insurance coverage for various medical scenarios"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_INSURANCE",
            last_name="PATIENT",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE
        )

        # Test primary insurance with comprehensive coverage
        primary_insurance = InsuranceInformation.objects.create(
            patient=patient,
            insurance_name="TEST_HEALTH_PLAN_A",
            insurance_type="PRIMARY",
            policy_number="POL-PRIMARY-123",
            group_number="GRP-001",
            member_id="MEM-001",
            effective_date=date(2023, 1, 1),
            insurance_company_name="TEST INSURANCE CO",
            insurance_company_address="123 INSURANCE AVE\nTEST CITY, TS 12345",
            insurance_company_phone="555-INSURE-1",
            copay_amount=Decimal("25.00"),
            deductible_amount=Decimal("1500.00"),
            out_of_pocket_max=Decimal("5000.00"),
            verification_status="VERIFIED",
            verification_date=date(2023, 1, 15)
        )

        self.assertEqual(primary_insurance.insurance_type, "PRIMARY")
        self.assertEqual(primary_insurance.verification_status, "VERIFIED")
        self.assertEqual(primary_insurance.copay_amount, Decimal("25.00"))

        # Test secondary insurance for supplemental coverage
        secondary_insurance = InsuranceInformation.objects.create(
            patient=patient,
            insurance_name="TEST_HEALTH_PLAN_B",
            insurance_type="SECONDARY",
            policy_number="POL-SECONDARY-456",
            effective_date=date(2023, 1, 1),
            insurance_company_name="SECONDARY INSURANCE CO",
            policy_holder_relationship="SELF",
            copay_amount=Decimal("10.00"),
            deductible_amount=Decimal("500.00"),
            out_of_pocket_max=Decimal("2000.00")
        )

        self.assertEqual(secondary_insurance.insurance_type, "SECONDARY")

        # Test Medicare/Medicaid scenarios
        medicare_insurance = InsuranceInformation.objects.create(
            patient=patient,
            insurance_name="MEDICARE",
            insurance_type="PRIMARY",
            policy_number="MEDICARE-789",
            effective_date=date(2023, 1, 1),
            insurance_company_name="MEDICARE ADMINISTRATION",
            policy_holder_relationship="SELF",
            policy_holder_dob=date(1940, 1, 1)  # Eligible for Medicare
        )

        self.assertEqual(medicare_insurance.insurance_name, "MEDICARE")

        # Test insurance expiration and renewal
        expired_insurance = InsuranceInformation.objects.create(
            patient=patient,
            insurance_name="EXPIRED_PLAN",
            insurance_type="TERTIARY",
            policy_number="POL-EXPIRED-999",
            effective_date=date(2022, 1, 1),
            termination_date=date(2022, 12, 31),
            insurance_company_name="EXPIRED CO",
            verification_status="EXPIRED"
        )

        self.assertTrue(expired_insurance.is_expired())
        self.assertEqual(expired_insurance.verification_status, "EXPIRED")

    def test_patient_status_medical_transitions(self):
        """Test patient status transitions in medical contexts"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_TRANSITION",
            last_name="PATIENT",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
            status=PatientStatus.ACTIVE
        )

        # Test admission to inpatient care
        self.assertEqual(patient.status, PatientStatus.ACTIVE)

        # Test discharge from hospital
        patient.status = PatientStatus.ACTIVE
        patient.save()
        self.assertEqual(patient.status, PatientStatus.ACTIVE)

        # Test transfer to another facility
        patient.status = PatientStatus.TRANSFERRED
        patient.save()
        self.assertEqual(patient.status, PatientStatus.TRANSFERRED)

        # Test patient death
        patient.status = PatientStatus.DECEASED
        patient.date_of_death = date(2023, 12, 1)
        patient.cause_of_death = "Test cause of death (anonymized)"
        patient.save()
        self.assertEqual(patient.status, PatientStatus.DECEASED)
        self.assertIsNotNone(patient.date_of_death)

        # Test lost to follow-up
        patient2 = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_LOST",
            last_name="PATIENT",
            date_of_birth=date(1985, 1, 1),
            gender=PatientGender.FEMALE,
            status=PatientStatus.LOST_TO_FOLLOWUP
        )

        self.assertEqual(patient2.status, PatientStatus.LOST_TO_FOLLOWUP)

    def test_medical_specialty_patient_profiles(self):
        """Test patient profiles for various medical specialties"""
        # Pediatric patient profile
        pediatric_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_PEDIATRIC",
            last_name="INFANT",
            date_of_birth=date.today() - timedelta(days=30),  # 30 days old
            gender=PatientGender.MALE,
            weight_kg=Decimal("3.5"),
            height_cm=Decimal("52.0")
        )

        self.assertTrue(pediatric_patient.is_minor())
        self.assertEqual(pediatric_patient.get_age(), 0)

        # Geriatric patient profile
        geriatric_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_GERIATRIC",
            last_name="ELDERLY",
            date_of_birth=date.today() - timedelta(days=365 * 85),  # 85 years old
            gender=PatientGender.FEMALE,
            status=PatientStatus.ACTIVE,
            vip_status=True,
            notes="Multiple chronic conditions, requires special attention"
        )

        self.assertEqual(geriatric_patient.get_age(), 85)
        self.assertFalse(geriatric_patient.is_minor())
        self.assertTrue(geriatric_patient.vip_status)

        # Surgical patient profile
        surgical_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_SURGICAL",
            last_name="CANDIDATE",
            date_of_birth=date(1975, 6, 15),
            gender=PatientGender.MALE,
            blood_type="O-",
            organ_donor=True,
            advance_directive_on_file=True
        )

        self.assertEqual(surgical_patient.blood_type, "O-")
        self.assertTrue(surgical_patient.organ_donor)

        # Emergency patient profile
        emergency_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_EMERGENCY",
            last_name="TRAUMA",
            date_of_birth=date(1995, 3, 20),
            gender=PatientGender.FEMALE,
            confidential=True,
            preferred_contact_method="PHONE",
            allow_sms=True,
            allow_automated_calls=True
        )

        self.assertTrue(emergency_patient.confidential)
        self.assertEqual(emergency_patient.preferred_contact_method, "PHONE")

    def test_medical_demographic_data(self):
        """Test handling of medical demographic information"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_DEMOGRAPHICS",
            last_name="PATIENT",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
            marital_status="SINGLE",
            race="WHITE",
            ethnicity="NOT_HISPANIC_LATINO",
            religion="CHRISTIANITY",
            preferred_language="EN",
            interpreter_needed=False
        )

        # Verify demographic data is properly stored
        self.assertEqual(patient.marital_status, "SINGLE")
        self.assertEqual(patient.race, "WHITE")
        self.assertEqual(patient.ethnicity, "NOT_HISPANIC_LATINO")
        self.assertEqual(patient.religion, "CHRISTIANITY")
        self.assertEqual(patient.preferred_language, "EN")
        self.assertFalse(patient.interpreter_needed)

        # Test patient requiring interpreter
        interpreter_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_NON_ENGLISH",
            last_name="PATIENT",
            date_of_birth=date(1980, 8, 12),
            gender=PatientGender.FEMALE,
            preferred_language="ES",
            interpreter_needed=True
        )

        self.assertEqual(interpreter_patient.preferred_language, "ES")
        self.assertTrue(interpreter_patient.interpreter_needed)

    def test_medical_consent_and_compliance(self):
        """Test medical consent and compliance scenarios"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_CONSENT",
            last_name="PATIENT",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
            hipaa_acknowledgment_date=timezone.now(),
            privacy_notice_date=timezone.now(),
            patient_portal_enrolled=True,
            patient_portal_last_login=timezone.now() - timedelta(days=7)
        )

        # Verify consent and compliance data
        self.assertIsNotNone(patient.hipaa_acknowledgment_date)
        self.assertIsNotNone(patient.privacy_notice_date)
        self.assertTrue(patient.patient_portal_enrolled)
        self.assertIsNotNone(patient.patient_portal_last_login)

        # Test communication preferences
        patient.allow_sms = True
        patient.allow_email = True
        patient.allow_automated_calls = False
        patient.preferred_contact_method = "EMAIL"
        patient.save()

        self.assertTrue(patient.allow_sms)
        self.assertTrue(patient.allow_email)
        self.assertFalse(patient.allow_automated_calls)
        self.assertEqual(patient.preferred_contact_method, "EMAIL")

    def test_medical_data_privacy(self):
        """Test medical data privacy protections"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="PRIVACY_TEST",
            last_name="PATIENT",
            date_of_birth=date(1990, 1, 1),
            gender=PatientGender.MALE,
            confidential=True,
            vip_status=False,
            notes="Highly sensitive medical information - TEST DATA ONLY"
        )

        # Verify privacy flags
        self.assertTrue(patient.confidential)
        self.assertFalse(patient.vip_status)

        # Test that sensitive information is properly marked
        self.assertIn("TEST DATA ONLY", patient.notes)

        # Create additional confidential patient
        confidential_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="CONFIDENTIAL",
            last_name="TEST",
            date_of_birth=date(1985, 5, 15),
            gender=PatientGender.FEMALE,
            confidential=True,
            vip_status=True,  # VIP and confidential
            healthcare_proxy="TEST PROXY - AUTHORIZED REPRESENTATIVE",
        )

        self.assertTrue(confidential_patient.confidential)
        self.assertTrue(confidential_patient.vip_status)
        self.assertIsNotNone(confidential_patient.healthcare_proxy)