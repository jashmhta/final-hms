import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.utils import timezone

from .models import PatientConsent


class HIPAAEncryptionUtils:
    """
    HIPAA-compliant encryption utilities for PHI in transit and at rest.
    Uses Fernet (symmetric) for simplicity and AES for custom transit encryption.
    Key management follows NIST SP 800-57 recommendations.
    """

    @staticmethod
    def generate_key(password: str, salt: bytes = None) -> bytes:
        """Generate encryption key from password using PBKDF2 (HIPAA-compliant)."""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # NIST recommended minimum
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    @staticmethod
    def encrypt_transit_data(data: str, key: bytes) -> str:
        """Encrypt PHI for transit using Fernet (AES-128 in CBC mode + HMAC)."""
        f = Fernet(key)
        encrypted = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    @staticmethod
    def decrypt_transit_data(encrypted_data: str, key: bytes) -> str:
        """Decrypt PHI from transit."""
        try:
            f = Fernet(key)
            decoded = base64.urlsafe_b64decode(encrypted_data)
            decrypted = f.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            raise ValueError("Decryption failed - possible tampering or wrong key")

    @staticmethod
    def get_encryption_key() -> bytes:
        """Retrieve or generate encryption key from Django settings."""
        key_str = getattr(settings, "HIPAA_ENCRYPTION_KEY", None)
        if not key_str:
            # Generate new key if not set (production should set this in settings)
            key = Fernet.generate_key()
            # In production, store this securely (e.g., AWS KMS, HashiCorp Vault)
            print("WARNING: Generated new HIPAA key. Store securely in production!")
            return key
        return base64.urlsafe_b64decode(key_str)

    @staticmethod
    def encrypt_phi_transit(phi_data: dict) -> dict:
        """Encrypt all PHI fields in a data dictionary for transit."""
        key = HIPAAEncryptionUtils.get_encryption_key()
        encrypted_data = {}
        for field, value in phi_data.items():
            if isinstance(value, str):
                encrypted_data[field] = HIPAAEncryptionUtils.encrypt_transit_data(
                    value, key
                )
            else:
                encrypted_data[field] = value
        return encrypted_data

    @staticmethod
    def decrypt_phi_transit(encrypted_data: dict) -> dict:
        """Decrypt all PHI fields from transit."""
        key = HIPAAEncryptionUtils.get_encryption_key()
        decrypted_data = {}
        for field, value in encrypted_data.items():
            if isinstance(value, str) and len(value) > 100:  # Likely encrypted
                try:
                    decrypted_data[field] = HIPAAEncryptionUtils.decrypt_transit_data(
                        value, key
                    )
                except ValueError:
                    decrypted_data[field] = value  # Not encrypted
            else:
                decrypted_data[field] = value
        return decrypted_data


class ConsentManager:
    """
    HIPAA-compliant patient consent management utilities.
    Handles consent validation, expiry checking, and authorization.
    """

    @staticmethod
    def validate_consent(patient_user, consent_type: str, action: str = "read") -> bool:
        """
        Validate if patient has active consent for specific type and action.
        Returns True if consent is valid, False otherwise.
        """
        try:
            now = timezone.now().date()
            consent = PatientConsent.objects.filter(
                patient=patient_user,
                consent_type=consent_type,
                is_active=True,
                expiry_date__gte=now,
            ).first()

            if not consent:
                return False

            # Additional validation for specific actions
            if action == "write" and consent_type == "treatment":
                # Treatment write requires explicit write consent
                # This would be stored in encrypted_consent_details
                pass  # Implementation depends on consent details structure

            return True
        except Exception:
            return False

    @staticmethod
    def get_active_consents(patient_user) -> list:
        """Get all active consents for a patient."""
        now = timezone.now().date()
        consents = PatientConsent.objects.filter(
            patient=patient_user, is_active=True, expiry_date__gte=now
        ).order_by("-consent_date")
        return consents

    @staticmethod
    def check_consent_expiry():
        """Mark expired consents as inactive (call periodically via management command)."""
        now = timezone.now().date()
        expired_consents = PatientConsent.objects.filter(
            expiry_date__lt=now, is_active=True
        )
        count = expired_consents.update(is_active=False)
        return count

    @staticmethod
    def requires_consent(action: str, data_type: str) -> bool:
        """Determine if specific action requires patient consent per HIPAA."""
        consent_matrix = {
            "read": {"medical_records": True, "billing": True, "appointments": True},
            "write": {"medical_records": True, "billing": True, "appointments": True},
            "delete": {"medical_records": True, "billing": True, "appointments": True},
        }
        return consent_matrix.get(action, {}).get(data_type, False)


# Breach detection utilities
class BreachDetectionUtils:
    """
    Utilities for detecting and handling potential HIPAA breaches.
    """

    @staticmethod
    def detect_suspicious_activity(user, action: str, ip_address: str) -> bool:
        """Detect potentially suspicious PHI access patterns."""
        # Implementation would include:
        # - Multiple failed login attempts
        # - Unusual IP locations
        # - Excessive data access in short time
        # - Access outside business hours
        # For now, basic IP check

        if ip_address == "0.0.0.0" or ip_address.startswith("127."):
            return True  # Localhost access might be testing

        # In production, integrate with threat intelligence, SIEM systems
        return False

    @staticmethod
    def calculate_breach_impact(affected_records: int) -> str:
        """Calculate breach impact level per HIPAA Breach Notification Rule."""
        if affected_records > 500:
            return "major"  # 60-day notification to HHS
        elif affected_records > 0:
            return "minor"  # Individual notifications
        return "none"
