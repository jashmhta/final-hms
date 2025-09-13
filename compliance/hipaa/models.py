import django_fernet_fields
from django.contrib.auth.models import User
from django.db import models


class PatientConsent(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="consents")
    consent_type = models.CharField(
        max_length=100,
        choices=[
            ("treatment", "Treatment"),
            ("payment", "Payment"),
            ("operations", "Healthcare Operations"),
        ],
    )
    encrypted_consent_details = django_fernet_fields.EncryptedTextField()
    consent_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Consent {self.consent_type} for {self.patient.username}"


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    phi_accessed = django_fernet_fields.EncryptedTextField()  # Encrypted PHI details
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)
    session_id = models.CharField(max_length=100, null=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} by {self.user.username} at {self.timestamp}"


class BreachNotification(models.Model):
    breach_type = models.CharField(max_length=100)
    affected_patients_count = models.IntegerField()
    description = django_fernet_fields.EncryptedTextField()
    discovery_date = models.DateTimeField(auto_now_add=True)
    notification_sent = models.BooleanField(default=False)
    notification_date = models.DateTimeField(null=True, blank=True)
    notified_parties = models.TextField()  # e.g., 'patients, HHS'

    def __str__(self):
        return f"Breach {self.breach_type} - {self.affected_patients_count} patients"
