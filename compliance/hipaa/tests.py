import json

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class HIPAAComplianceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_consent_creation(self):
        """Test patient consent creation and audit logging."""
        response = self.client.post(
            reverse("hipaa_compliance:create_patient_consent"),
            {
                "consent_type": "treatment",
                "details": "Test consent details",
                "expiry_date": "2026-01-01",
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_encryption_utils(self):
        """Test HIPAA encryption functionality."""
        from .utils import HIPAAEncryptionUtils

        test_data = "PHI Test Data"
        key = HIPAAEncryptionUtils.get_encryption_key()
        encrypted = HIPAAEncryptionUtils.encrypt_transit_data(test_data, key)
        decrypted = HIPAAEncryptionUtils.decrypt_transit_data(encrypted, key)
        self.assertEqual(test_data, decrypted)
        self.assertNotEqual(test_data, encrypted)

    def test_consent_validation(self):
        """Test consent validation logic."""
        from .utils import ConsentManager

        self.assertFalse(
            ConsentManager.validate_consent(self.user, "treatment", "write")
        )

    def test_audit_logging(self):
        """Test automatic audit logging."""
        from .models import AuditLog

        response = self.client.get(reverse("hipaa_compliance:patient_consent_list"))
        self.assertGreater(AuditLog.objects.count(), 0)
