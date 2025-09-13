import secrets
import uuid
from datetime import timedelta

import pyotp
from core.models import TimeStampedModel
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class MFADevice(TimeStampedModel):
    """Multi-Factor Authentication devices"""

    DEVICE_TYPES = [
        ("TOTP", "Time-based OTP (Google Authenticator)"),
        ("SMS", "SMS Verification"),
        ("EMAIL", "Email Verification"),
        ("BACKUP", "Backup Codes"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mfa_devices")
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    name = models.CharField(max_length=100, help_text="User-friendly name for device")
    secret_key = models.CharField(max_length=32, help_text="Base32 encoded secret")
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    last_used = models.DateTimeField(null=True, blank=True)

    # For SMS/Email devices
    phone_number = models.CharField(max_length=20, blank=True)
    email_address = models.EmailField(blank=True)

    # For backup codes
    backup_codes = models.JSONField(default=list, blank=True)
    codes_used = models.JSONField(default=list, blank=True)

    # Security
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["user", "device_type", "name"]

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.device_type})"

    def save(self, *args, **kwargs):
        if not self.secret_key and self.device_type == "TOTP":
            self.secret_key = pyotp.random_base32()
        super().save(*args, **kwargs)

    def get_totp_uri(self):
        """Get TOTP URI for QR code generation"""
        if self.device_type != "TOTP":
            return None

        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(name=self.user.email, issuer_name="HMS Enterprise")

    def verify_token(self, token):
        """Verify MFA token"""
        if not self.is_active or self.is_locked():
            return False

        try:
            if self.device_type == "TOTP":
                totp = pyotp.TOTP(self.secret_key)
                is_valid = totp.verify(token, valid_window=1)
            elif self.device_type == "BACKUP":
                is_valid = token in self.backup_codes and token not in self.codes_used
                if is_valid:
                    self.codes_used.append(token)
                    self.save()
            else:
                # SMS/Email tokens are handled separately
                return False

            if is_valid:
                self.failed_attempts = 0
                self.last_used = timezone.now()
                self.save()
                return True
            else:
                self.failed_attempts += 1
                if self.failed_attempts >= 5:
                    self.locked_until = timezone.now() + timedelta(minutes=30)
                self.save()
                return False

        except Exception:
            return False

    def is_locked(self):
        """Check if device is temporarily locked"""
        return self.locked_until and self.locked_until > timezone.now()

    def generate_backup_codes(self, count=10):
        """Generate new backup codes"""
        self.backup_codes = [secrets.token_hex(4).upper() for _ in range(count)]
        self.codes_used = []
        self.save()
        return self.backup_codes


class LoginSession(TimeStampedModel):
    """Track user login sessions for security"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="login_sessions"
    )
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.JSONField(default=dict, blank=True)

    # Authentication details
    login_method = models.CharField(max_length=20, default="PASSWORD")
    mfa_verified = models.BooleanField(default=False)
    mfa_device_used = models.ForeignKey(
        MFADevice, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Session management
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)

    # Security flags
    is_suspicious = models.BooleanField(default=False)
    risk_score = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.ip_address} ({self.created_at})"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def extend_session(self, minutes=30):
        """Extend session expiry"""
        self.expires_at = timezone.now() + timedelta(minutes=minutes)
        self.last_activity = timezone.now()
        self.save()


class SecurityEvent(TimeStampedModel):
    """Security events and audit logging"""

    EVENT_TYPES = [
        ("LOGIN_SUCCESS", "Successful Login"),
        ("LOGIN_FAILED", "Failed Login"),
        ("LOGOUT", "User Logout"),
        ("MFA_SETUP", "MFA Device Setup"),
        ("MFA_SUCCESS", "MFA Verification Success"),
        ("MFA_FAILED", "MFA Verification Failed"),
        ("PASSWORD_CHANGE", "Password Changed"),
        ("PASSWORD_RESET", "Password Reset"),
        ("ACCOUNT_LOCKED", "Account Locked"),
        ("SUSPICIOUS_ACTIVITY", "Suspicious Activity"),
        ("PERMISSION_DENIED", "Permission Denied"),
        ("DATA_ACCESS", "Sensitive Data Access"),
        ("SYSTEM_ADMIN", "System Administration"),
    ]

    SEVERITY_LEVELS = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default="LOW")

    # Event details
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.UUIDField(null=True, blank=True)

    # Context data
    metadata = models.JSONField(default=dict, blank=True)
    affected_resource = models.CharField(max_length=200, blank=True)

    # Response tracking
    requires_action = models.BooleanField(default=False)
    action_taken = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_security_events",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "event_type", "-created_at"]),
            models.Index(fields=["severity", "-created_at"]),
            models.Index(fields=["requires_action", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.user or 'Anonymous'} ({self.created_at})"


class PasswordPolicy(models.Model):
    """Password policy configuration"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    # Password requirements
    min_length = models.PositiveIntegerField(default=12)
    max_length = models.PositiveIntegerField(default=128)
    require_uppercase = models.BooleanField(default=True)
    require_lowercase = models.BooleanField(default=True)
    require_digits = models.BooleanField(default=True)
    require_special_chars = models.BooleanField(default=True)
    special_chars = models.CharField(
        max_length=50, default="!@#$%^&*()_+-=[]{}|;:,.<>?"
    )

    # History and rotation
    password_history_count = models.PositiveIntegerField(default=5)
    max_age_days = models.PositiveIntegerField(default=90)
    min_age_hours = models.PositiveIntegerField(default=24)

    # Account lockout
    max_failed_attempts = models.PositiveIntegerField(default=5)
    lockout_duration_minutes = models.PositiveIntegerField(default=30)

    # Session settings
    session_timeout_minutes = models.PositiveIntegerField(default=30)
    max_concurrent_sessions = models.PositiveIntegerField(default=3)

    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default policy
            PasswordPolicy.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class UserPasswordHistory(models.Model):
    """Track password history for users"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_history"
    )
    password_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


class TrustedDevice(TimeStampedModel):
    """Trusted devices for reduced MFA requirements"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="trusted_devices"
    )
    device_id = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=100)
    device_fingerprint = models.CharField(max_length=128, unique=True)

    # Device info
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField()
    device_info = models.JSONField(default=dict, blank=True)

    # Trust settings
    is_active = models.BooleanField(default=True)
    trust_expires_at = models.DateTimeField()
    last_used = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-last_used"]

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    def is_expired(self):
        return timezone.now() > self.trust_expires_at
