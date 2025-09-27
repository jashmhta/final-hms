"""
models module
"""

import os
from datetime import timedelta
from decimal import Decimal

from cryptography.fernet import Fernet
from django_auditlog.models import AuditlogHistoryField

from django.db import models
from django.db.models import Q
from django.utils import timezone

key_file = "/root/encryption_key.key"
if os.path.exists(key_file):
    with open(key_file, "rb") as f:
        encryption_key = f.read()
else:
    encryption_key = Fernet.generate_key()
    with open(key_file, "wb") as f:
        f.write(encryption_key)
fernet = Fernet(encryption_key)


class EncryptedDecimalField(models.Field):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 255
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, Decimal):
            value = str(value)
        return fernet.encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        try:
            decrypted = fernet.decrypt(value.encode()).decode()
            return Decimal(decrypted)
        except:
            return None


class PreAuthManager(models.Manager):
    def active(self):
        return self.filter(created_at__gte=timezone.now() - timedelta(days=365))


class PreAuth(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("submitted", "Submitted"),
    ]
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)
    claim_amount = EncryptedDecimalField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    tpa_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    auditlog = AuditlogHistoryField()
    objects = PreAuthManager()

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"PreAuth {{self.id}} - {{self.patient}}"


class ClaimManager(models.Manager):
    def active(self):
        return self.filter(created_at__gte=timezone.now() - timedelta(days=365))


class Claim(models.Model):
    id = models.AutoField(primary_key=True)
    preauth = models.ForeignKey(
        PreAuth, on_delete=models.CASCADE, related_name="claims"
    )
    diagnosis_codes = models.JSONField(default=list)
    procedure_codes = models.JSONField(default=list)
    billed_amount = EncryptedDecimalField()
    paid_amount = EncryptedDecimalField(default=0)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    auditlog = AuditlogHistoryField()
    objects = ClaimManager()

    class Meta:
        indexes = [
            models.Index(fields=["preauth"]),
        ]

    def __str__(self):
        return f"Claim {{self.id}} - {{self.preauth}}"


class ReimbursementManager(models.Manager):
    def recent(self):
        return self.filter(
            payment_date__gte=timezone.now().date() - timedelta(days=365)
        )


class Reimbursement(models.Model):
    id = models.AutoField(primary_key=True)
    claim = models.ForeignKey(
        Claim, on_delete=models.CASCADE, related_name="reimbursements"
    )
    amount = EncryptedDecimalField()
    payment_date = models.DateField()
    tpa_transaction_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    auditlog = AuditlogHistoryField()
    objects = ReimbursementManager()

    class Meta:
        indexes = [
            models.Index(fields=["payment_date"]),
            models.Index(fields=["tpa_transaction_id"]),
        ]

    def __str__(self):
        return f"Reimbursement {{self.id}} - {{self.claim}}"


class Patient(models.Model):
    patient_id = models.CharField(max_length=20, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    insurance_number = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Male"), ("F", "Female"), ("O", "Other")],
        blank=True,
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "mock_patients"
        verbose_name = "Mock Patient"
        verbose_name_plural = "Mock Patients"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_insurance_info(self):
        return {
            "patient_id": self.patient_id,
            "insurance_number": self.insurance_number,
            "full_name": self.get_full_name(),
        }
