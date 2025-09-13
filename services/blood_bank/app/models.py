from django.db import models

try:
    from django.contrib.postgres.indexes import GinIndex

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    GinIndex = None

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog

# Import custom encrypted fields
from .fields import EncryptedCharField, EncryptedTextField

# Blood type choices
BLOOD_TYPES = [
    ("O-", "O Negative"),
    ("O+", "O Positive"),
    ("A-", "A Negative"),
    ("A+", "A Positive"),
    ("B-", "B Negative"),
    ("B+", "B Positive"),
    ("AB-", "AB Negative"),
    ("AB+", "AB Positive"),
]

# Inventory status choices
INVENTORY_STATUS = [
    ("AVAILABLE", "Available"),
    ("RESERVED", "Reserved"),
    ("TRANSFUSED", "Transfused"),
    ("EXPIRED", "Expired"),
    ("QUARANTINED", "Quarantined"),
]

# Compatibility result choices
COMPATIBILITY_RESULTS = [
    ("COMPATIBLE", "Compatible"),
    ("INCOMPATIBLE", "Incompatible"),
    ("PENDING", "Pending"),
    ("ERROR", "Error"),
]


class TimestampedModel(models.Model):
    """Abstract base model with timestamps and audit logging"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = AuditlogHistoryField()

    class Meta:
        abstract = True


class Donor(TimestampedModel):
    """HIPAA-compliant Donor model with encrypted PII"""

    name = EncryptedCharField(max_length=255, verbose_name="Donor Name")
    dob = EncryptedCharField(max_length=10, verbose_name="Date of Birth")  # MM/DD/YYYY
    ssn = EncryptedCharField(
        max_length=11, verbose_name="Social Security Number"
    )  # XXX-XX-XXXX
    address = EncryptedTextField(verbose_name="Address")
    contact = EncryptedCharField(max_length=20, verbose_name="Contact Number")
    blood_type = models.CharField(
        max_length=3, choices=BLOOD_TYPES, verbose_name="Blood Type"
    )
    donation_history = models.JSONField(
        default=dict, blank=True, verbose_name="Donation History"
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        db_table = "blood_bank_donor"
        indexes = [
            models.Index(fields=["blood_type"]),
        ]
        verbose_name = "Donor"
        verbose_name_plural = "Donors"

    def __str__(self):
        return f"Donor: {{self.name}} ({{self.blood_type}})"


class BloodInventory(TimestampedModel):
    """Blood inventory tracking with expiry management"""

    donor = models.ForeignKey(
        Donor, on_delete=models.CASCADE, related_name="inventory_items"
    )
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    unit_id = models.CharField(max_length=50, unique=True, verbose_name="Unit ID")
    expiry_date = models.DateField(verbose_name="Expiry Date")
    status = models.CharField(
        max_length=20, choices=INVENTORY_STATUS, default="AVAILABLE"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity (units)")
    storage_location = models.CharField(
        max_length=100, blank=True, verbose_name="Storage Location"
    )

    class Meta:
        db_table = "blood_bank_inventory"
        indexes = [
            models.Index(fields=["blood_type", "status"]),
            models.Index(fields=["expiry_date"]),
            models.Index(fields=["status"]),
        ]
        verbose_name = "Blood Inventory"
        verbose_name_plural = "Blood Inventory"

    def __str__(self):
        return f"{{self.unit_id}} ({{self.blood_type}}) - {{self.status}}"


class TransfusionRecord(TimestampedModel):
    """Transfusion record linking inventory to patient"""

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="transfusions"
    )
    blood_unit = models.ForeignKey(
        BloodInventory, on_delete=models.CASCADE, related_name="transfusions"
    )
    transfusion_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Transfusion Date"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Units Transfused")
    notes = models.TextField(blank=True, verbose_name="Clinical Notes")
    performed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="transfusions_performed",
    )

    class Meta:
        db_table = "blood_bank_transfusion_record"
        verbose_name = "Transfusion Record"
        verbose_name_plural = "Transfusion Records"

    def __str__(self):
        return f"Transfusion: {{self.patient.name}} - {{self.blood_unit.unit_id}}"


class Crossmatch(TimestampedModel):
    """Blood compatibility crossmatch testing"""

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="crossmatches"
    )
    blood_unit = models.ForeignKey(
        BloodInventory, on_delete=models.CASCADE, related_name="crossmatches"
    )
    compatibility_result = models.CharField(
        max_length=20, choices=COMPATIBILITY_RESULTS, default="PENDING"
    )
    tested_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="crossmatches_performed",
    )
    notes = models.TextField(blank=True, verbose_name="Test Notes")

    class Meta:
        db_table = "blood_bank_crossmatch"
        verbose_name = "Crossmatch"
        verbose_name_plural = "Crossmatches"

    def __str__(self):
        return f"Crossmatch: {{self.patient.name}} - {{self.blood_unit.unit_id}} ({{self.compatibility_result}})"


# Register models with auditlog
auditlog.register(Donor)
auditlog.register(BloodInventory)
auditlog.register(TransfusionRecord)
auditlog.register(Crossmatch)
