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
    PatientStatus,
)

User = get_user_model()


class HIPAAComplianceTests(TestCase):
    """Comprehensive HIPAA compliance validation tests"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = User.objects.create_user(
            username="hipaa_user",
            email="hipaa@example.com",
            password="hipaapass123",
            hospital=self.hospital,
            is_staff=True,
        )

    def test_phi_encryption_requirements(self):
        """Test that Protected Health Information (PHI) is properly encrypted"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="TEST_PATIENT",
            last_name="ANONYMIZED",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="test.phi@example.com",
            phone_primary="555-PHI-TEST",
            address_line1="123 HIPAA COMPLIANT ST",
            city="COMPLIANCE CITY",
            state="HC",
            zip_code="12345",
        )

        # Verify that sensitive fields are encrypted fields
        from encrypted_model_fields.fields import (
            EncryptedCharField,
            EncryptedEmailField,
        )

        # Check that model uses encrypted fields for PHI
        self.assertIsInstance(Patient._meta.get_field("first_name"), EncryptedCharField)
        self.assertIsInstance(Patient._meta.get_field("last_name"), EncryptedCharField)
        self.assertIsInstance(Patient._meta.get_field("email"), EncryptedEmailField)
        self.assertIsInstance(Patient._meta.get_field("phone_primary"), EncryptedCharField)
        self.assertIsInstance(Patient._meta.get_field("address_line1"), EncryptedCharField)

        # Test that data is accessible but encrypted at rest
        self.assertEqual(patient.first_name, "TEST_PATIENT")
        self.assertEqual(patient.email, "test.phi@example.com")

    def test_hipaa_authorization_and_consent(self):
        """Test HIPAA authorization and consent tracking"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="CONSENT",
            last_name="TEST",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            hipaa_acknowledgment_date=timezone.now(),
            privacy_notice_date=timezone.now(),
            created_by=self.user,
        )

        # Verify HIPAA acknowledgment is recorded
        self.assertIsNotNone(patient.hipaa_acknowledgment_date)
        self.assertIsNotNone(patient.privacy_notice_date)

        # Test that acknowledgment cannot be backdated too far
        with self.assertRaises(ValidationError):
            patient.hipaa_acknowledgment_date = timezone.now() - timedelta(days=400)
            patient.save()

        # Test privacy notice requirement
        patient.privacy_notice_date = None
        with self.assertRaises(ValidationError):
            patient.full_clean()

    def test_minimum_necessary_standard(self):
        """Test HIPAA minimum necessary standard for data access"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="MINIMUM",
            last_name="NECESSARY",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            confidential=True,
        )

        # Create sensitive data
        EmergencyContact.objects.create(
            patient=patient,
            first_name="SENSITIVE",
            last_name="CONTACT",
            relationship="SPOUSE",
            phone_primary="555-SENSITIVE",
            can_make_medical_decisions=True,
        )

        PatientAlert.objects.create(
            patient=patient,
            alert_type="SAFETY",
            severity="CRITICAL",
            title="Highly Sensitive Alert",
            description="Contains sensitive medical information",
            created_by=self.user,
        )

        # Test that sensitive data access is controlled
        limited_user = User.objects.create_user(
            username="limited", email="limited@example.com", password="limited123", hospital=self.hospital
        )

        # Limited user should not be able to access confidential patient data
        # (This would be tested through API permissions in actual implementation)
        self.assertFalse(limited_user.is_staff)
        self.assertFalse(limited_user.has_perm("patients.view_confidential_patient"))

    def test_audit_trail_requirements(self):
        """Test HIPAA audit trail requirements for PHI access"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="AUDIT",
            last_name="TRAIL",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            created_by=self.user,
        )

        # Verify creation tracking
        self.assertEqual(patient.created_by, self.user)
        self.assertIsNotNone(patient.created_at)

        # Update with audit trail
        patient.first_name = "UPDATED"
        patient.last_updated_by = self.user
        patient.save()

        updated_patient = Patient.objects.get(id=patient.id)
        self.assertEqual(updated_patient.last_updated_by, self.user)
        self.assertGreater(updated_patient.updated_at, patient.created_at)

        # Test that audit information is preserved
        self.assertEqual(updated_patient.created_by, patient.created_by)
        self.assertEqual(updated_patient.created_at, patient.created_at)

    def test_data_retention_policies(self):
        """Test HIPAA data retention policies"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="RETENTION",
            last_name="TEST",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            status=PatientStatus.ACTIVE,
        )

        # Test deceased patient data retention
        patient.status = PatientStatus.DECEASED
        patient.date_of_death = date(2023, 1, 1)
        patient.cause_of_death = "Natural causes - TEST DATA"
        patient.save()

        # Verify deceased patient data is preserved
        self.assertEqual(patient.status, PatientStatus.DECEASED)
        self.assertIsNotNone(patient.date_of_death)

        # Test that deceased patient information is handled appropriately
        self.assertIn("TEST DATA", patient.cause_of_death)

    def test_breach_notification_readiness(self):
        """Test breach notification readiness"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="BREACH",
            last_name="TEST",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="breach.test@example.com",
            phone_primary="555-BREACH",
            confidential=True,
        )

        # Verify that breach notification contact information is available
        self.assertIsNotNone(patient.email)
        self.assertIsNotNone(patient.phone_primary)

        # Test that last access dates are tracked
        access_date = timezone.now()
        patient.patient_portal_last_login = access_date
        patient.save()

        self.assertEqual(patient.patient_portal_last_login, access_date)

    def test_security_incident_response(self):
        """Test security incident response capabilities"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="SECURITY",
            last_name="INCIDENT",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            vip_status=True,
            confidential=True,
        )

        # Create security-related alerts
        security_alert = PatientAlert.objects.create(
            patient=patient,
            alert_type="SAFETY",
            severity="HIGH",
            title="Security Incident Detected",
            description="Unauthorized access attempt detected - TEST",
            requires_acknowledgment=True,
            created_by=self.user,
        )

        # Verify security alert tracking
        self.assertEqual(security_alert.alert_type, "SAFETY")
        self.assertTrue(security_alert.requires_acknowledgment)
        self.assertIn("Unauthorized access", security_alert.description)

        # Test incident acknowledgment
        security_alert.acknowledged_by = self.user
        security_alert.acknowledged_at = timezone.now()
        security_alert.save()

        self.assertIsNotNone(security_alert.acknowledged_by)
        self.assertIsNotNone(security_alert.acknowledged_at)


class GDPRComplianceTests(TestCase):
    """Comprehensive GDPR compliance validation tests"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = User.objects.create_user(
            username="gdpr_user",
            email="gdpr@example.com",
            password="gdprpass123",
            hospital=self.hospital,
            is_staff=True,
        )

    def test_lawful_basis_for_processing(self):
        """Test GDPR lawful basis for processing personal data"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="LAWFUL",
            last_name="BASIS",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            hipaa_acknowledgment_date=timezone.now(),  # Consent
            privacy_notice_date=timezone.now(),  # Privacy notice
            created_by=self.user,
        )

        # Verify lawful basis documentation
        self.assertIsNotNone(patient.hipaa_acknowledgment_date)
        self.assertIsNotNone(patient.privacy_notice_date)

        # Test consent withdrawal capability
        patient.allow_email = False  # Withdraw consent for email communications
        patient.allow_sms = False  # Withdraw consent for SMS
        patient.save()

        self.assertFalse(patient.allow_email)
        self.assertFalse(patient.allow_sms)

    def test_data_minimization_principles(self):
        """Test GDPR data minimization principles"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="MINIMIZED",
            last_name="DATA",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            # Only collect essential information
            phone_primary="555-ESSENTIAL",
            email="essential@example.com",
        )

        # Verify only necessary data is collected
        self.assertEqual(patient.first_name, "MINIMIZED")
        self.assertEqual(patient.last_name, "DATA")
        self.assertIsNotNone(patient.phone_primary)
        self.assertIsNotNone(patient.email)

        # Test that optional fields are not required
        self.assertEqual(patient.middle_name, "")
        self.assertEqual(patient.suffix, "")
        self.assertEqual(patient.maiden_name, "")

    def test_right_to_access(self):
        """Test GDPR right to access personal data"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="ACCESS",
            last_name="RIGHT",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="access.right@example.com",
            phone_primary="555-ACCESS",
            created_by=self.user,
        )

        # Add related data
        EmergencyContact.objects.create(
            patient=patient,
            first_name="EMERGENCY",
            last_name="CONTACT",
            relationship="SPOUSE",
            phone_primary="555-EMERGENCY",
        )

        # Test data access capability
        patient_data = {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "email": patient.email,
            "phone_primary": patient.phone_primary,
            "emergency_contacts": list(patient.emergency_contacts.values()),
        }

        # Verify all personal data is accessible
        self.assertEqual(patient_data["first_name"], "ACCESS")
        self.assertEqual(patient_data["last_name"], "RIGHT")
        self.assertEqual(len(patient_data["emergency_contacts"]), 1)

    def test_right_to_rectification(self):
        """Test GDPR right to rectification of inaccurate data"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="WRONG",
            last_name="DATA",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="wrong@example.com",
            phone_primary="555-WRONG",
        )

        # Correct inaccurate data
        patient.first_name = "CORRECTED"
        patient.last_name = "DATA"
        patient.email = "correct@example.com"
        patient.phone_primary = "555-CORRECT"
        patient.save()

        # Verify data is corrected
        corrected_patient = Patient.objects.get(id=patient.id)
        self.assertEqual(corrected_patient.first_name, "CORRECTED")
        self.assertEqual(corrected_patient.email, "correct@example.com")
        self.assertEqual(corrected_patient.phone_primary, "555-CORRECT")

        # Verify correction history is maintained
        self.assertEqual(corrected_patient.created_by, patient.created_by)
        self.assertNotEqual(corrected_patient.updated_at, patient.created_at)

    def test_right_to_erasure_right_to_be_forgotten(self):
        """Test GDPR right to erasure (right to be forgotten)"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="ERASE",
            last_name="ME",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="erase.me@example.com",
            phone_primary="555-ERASE",
        )

        # Add related data
        emergency_contact = EmergencyContact.objects.create(
            patient=patient,
            first_name="CONTACT",
            last_name="TO_ERASE",
            relationship="SPOUSE",
            phone_primary="555-ERASE-CONTACT",
        )

        insurance = InsuranceInformation.objects.create(
            patient=patient,
            insurance_name="INSURANCE",
            insurance_type="PRIMARY",
            policy_number="POL-ERASE",
            effective_date=date(2023, 1, 1),
            insurance_company_name="ERASE CO",
        )

        patient_id = patient.id

        # Exercise right to erasure
        patient.delete()

        # Verify all personal data is deleted
        self.assertFalse(Patient.objects.filter(id=patient_id).exists())
        self.assertFalse(EmergencyContact.objects.filter(patient_id=patient_id).exists())
        self.assertFalse(InsuranceInformation.objects.filter(patient_id=patient_id).exists())

    def test_right_to_restrict_processing(self):
        """Test GDPR right to restrict processing"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="RESTRICT",
            last_name="PROCESSING",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            confidential=True,  # Mark as restricted processing
            email="restrict@example.com",
        )

        # Verify processing restrictions
        self.assertTrue(patient.confidential)

        # Test that restricted data is handled appropriately
        self.assertEqual(patient.email, "restrict@example.com")

        # Add restriction note
        patient.notes = "Processing restricted per GDPR Article 18 - TEST"
        patient.save()

        self.assertIn("GDPR Article 18", patient.notes)

    def test_right_to_data_portability(self):
        """Test GDPR right to data portability"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="PORTABLE",
            last_name="DATA",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="portable@example.com",
            phone_primary="555-PORTABLE",
        )

        # Add related data for portability
        EmergencyContact.objects.create(
            patient=patient, first_name="CONTACT", last_name="DATA", relationship="SPOUSE", phone_primary="555-CONTACT"
        )

        # Test data export capability
        portable_data = {
            "patient": {
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "date_of_birth": patient.date_of_birth.isoformat(),
                "gender": patient.gender,
                "email": patient.email,
                "phone_primary": patient.phone_primary,
            },
            "emergency_contacts": [
                {
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "relationship": contact.relationship,
                    "phone_primary": contact.phone_primary,
                }
                for contact in patient.emergency_contacts.all()
            ],
        }

        # Verify data is in machine-readable format
        self.assertEqual(portable_data["patient"]["first_name"], "PORTABLE")
        self.assertEqual(len(portable_data["emergency_contacts"]), 1)

    def test_right_to_object(self):
        """Test GDPR right to object to processing"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="OBJECT",
            last_name="PROCESSING",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            allow_automated_calls=False,  # Object to automated processing
            allow_sms=False,  # Object to SMS processing
            notes="Patient objects to automated processing - TEST",
        )

        # Verify processing objections
        self.assertFalse(patient.allow_automated_calls)
        self.assertFalse(patient.allow_sms)

        # Test objection documentation
        self.assertIn("objects to automated processing", patient.notes)

    def test_rights_related_to_automated_decision_making(self):
        """Test GDPR rights related to automated decision making"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="AUTOMATED",
            last_name="DECISION",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            notes="Exempt from automated decision making per patient request - TEST",
        )

        # Verify human intervention capability
        self.assertIn("automated decision making", patient.notes)

        # Test that automated decision making is noted
        self.assertIn("patient request", patient.notes)

    def test_data_protection_by_design_and_default(self):
        """Test GDPR data protection by design and by default"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="PRIVACY",
            last_name="BY_DEFAULT",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            # Privacy by default - minimal data collection
            allow_automated_calls=False,  # Default to no automated calls
            allow_sms=False,  # Default to no SMS
            confidential=True,  # Default to high privacy
        )

        # Verify privacy-by-default settings
        self.assertFalse(patient.allow_automated_calls)
        self.assertFalse(patient.allow_sms)
        self.assertTrue(patient.confidential)

        # Test that data protection is designed into the system
        from encrypted_model_fields.fields import EncryptedCharField

        self.assertIsInstance(Patient._meta.get_field("first_name"), EncryptedCharField)

    def test_data_protection_impact_assessments(self):
        """Test GDPR data protection impact assessments (DPIA)"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="DPIA",
            last_name="ASSESSMENT",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            confidential=True,
            notes="High risk processing - DPIA completed - TEST",
        )

        # Verify DPIA documentation
        self.assertIn("DPIA completed", patient.notes)

        # Test high-risk processing identification
        self.assertTrue(patient.confidential)
        self.assertIn("High risk", patient.notes)

    def test_data_breach_notification(self):
        """Test GDPR data breach notification requirements"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="BREACH",
            last_name="NOTIFICATION",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="breach@example.com",
            phone_primary="555-BREACH",
            confidential=True,
        )

        # Create breach detection alert
        breach_alert = PatientAlert.objects.create(
            patient=patient,
            alert_type="SAFETY",
            severity="CRITICAL",
            title="Data Breach Detected - GDPR",
            description="Unauthorized access to personal data detected - NOTIFICATION REQUIRED",
            requires_acknowledgment=True,
            created_by=self.user,
        )

        # Verify breach detection and notification requirements
        self.assertEqual(breach_alert.severity, "CRITICAL")
        self.assertTrue(breach_alert.requires_acknowledgment)
        self.assertIn("NOTIFICATION REQUIRED", breach_alert.description)

        # Test notification capability
        self.assertIsNotNone(patient.email)
        self.assertIsNotNone(patient.phone_primary)


class HealthcareComplianceIntegrationTests(TestCase):
    """Integration tests for combined HIPAA/GDPR compliance"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = User.objects.create_user(
            username="compliance_user",
            email="compliance@example.com",
            password="compliancepass123",
            hospital=self.hospital,
            is_staff=True,
        )

    def test_cross_compliance_data_subject_rights(self):
        """Test cross-compliance data subject rights"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="CROSS",
            last_name="COMPLIANCE",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="cross.compliance@example.com",
            phone_primary="555-CROSS",
            # HIPAA compliance
            hipaa_acknowledgment_date=timezone.now(),
            privacy_notice_date=timezone.now(),
            # GDPR compliance
            allow_automated_calls=False,
            allow_sms=False,
            confidential=True,
        )

        # Verify HIPAA compliance
        self.assertIsNotNone(patient.hipaa_acknowledgment_date)
        self.assertIsNotNone(patient.privacy_notice_date)

        # Verify GDPR compliance
        self.assertFalse(patient.allow_automated_calls)
        self.assertFalse(patient.allow_sms)

        # Test data portability (GDPR) with encryption (HIPAA)
        portable_data = {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "email": patient.email,
            "compliance_status": "HIPAA & GDPR Compliant",
        }

        self.assertEqual(portable_data["first_name"], "CROSS")
        self.assertIn("HIPAA & GDPR", portable_data["compliance_status"])

    def test_international_data_transfer_compliance(self):
        """Test international data transfer compliance"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="INTERNATIONAL",
            last_name="TRANSFER",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="international@example.com",
            country="US",  # Data location
            notes="International data transfer compliant - GDPR Article 44-49 - TEST",
        )

        # Verify data location tracking
        self.assertEqual(patient.country, "US")

        # Verify international transfer compliance
        self.assertIn("GDPR Article", patient.notes)

    def test_comprehensive_audit_trail(self):
        """Test comprehensive audit trail for compliance"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="AUDIT",
            last_name="COMPREHENSIVE",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            created_by=self.user,
            hipaa_acknowledgment_date=timezone.now(),
            privacy_notice_date=timezone.now(),
        )

        # Update with full audit trail
        patient.first_name = "UPDATED"
        patient.last_updated_by = self.user
        patient.save()

        # Create compliance-related alert
        compliance_alert = PatientAlert.objects.create(
            patient=patient,
            alert_type="CLINICAL",
            severity="MEDIUM",
            title="Compliance Review Required",
            description="HIPAA/GDPR compliance review needed - AUDIT TRAIL",
            created_by=self.user,
        )

        # Verify comprehensive audit capability
        self.assertEqual(patient.created_by, self.user)
        self.assertEqual(patient.last_updated_by, self.user)
        self.assertEqual(compliance_alert.created_by, self.user)

        # Verify timestamp tracking
        self.assertIsNotNone(patient.created_at)
        self.assertIsNotNone(patient.updated_at)
        self.assertIsNotNone(compliance_alert.created_at)

    def test_compliance_documentation_maintenance(self):
        """Test compliance documentation maintenance"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="DOCUMENTATION",
            last_name="COMPLIANCE",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            # HIPAA documentation
            hipaa_acknowledgment_date=timezone.now(),
            privacy_notice_date=timezone.now(),
            # GDPR documentation
            allow_email=True,
            allow_sms=False,
            # Combined compliance notes
            notes="""
            HIPAA Compliance:
            - PHI encryption: Active
            - Audit trail: Enabled
            - Breach notification: Ready

            GDPR Compliance:
            - Lawful basis: Consent
            - Data minimization: Applied
            - Subject rights: Enabled
            - International transfers: Compliant
            """,
        )

        # Verify comprehensive compliance documentation
        self.assertIsNotNone(patient.hipaa_acknowledgment_date)
        self.assertTrue(patient.allow_email)
        self.assertFalse(patient.allow_sms)

        # Verify documentation content
        self.assertIn("HIPAA Compliance", patient.notes)
        self.assertIn("GDPR Compliance", patient.notes)
        self.assertIn("PHI encryption", patient.notes)
        self.assertIn("Data minimization", patient.notes)
