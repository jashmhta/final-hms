from django.db import models
from django.utils import timezone
try:
    from django.contrib.postgres.indexes import GinIndex
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    GinIndex = None
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from .fields import EncryptedCharField, EncryptedTextField
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
INVENTORY_STATUS = [
    ("AVAILABLE", "Available"),
    ("RESERVED", "Reserved"),
    ("TRANSFUSED", "Transfused"),
    ("EXPIRED", "Expired"),
    ("QUARANTINED", "Quarantined"),
]
COMPATIBILITY_RESULTS = [
    ("COMPATIBLE", "Compatible"),
    ("INCOMPATIBLE", "Incompatible"),
    ("PENDING", "Pending"),
    ("ERROR", "Error"),
]
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = AuditlogHistoryField()
    class Meta:
        abstract = True
class Donor(TimestampedModel):
    name = EncryptedCharField(max_length=255, verbose_name="Donor Name")
    dob = EncryptedCharField(max_length=10, verbose_name="Date of Birth")  
    ssn = EncryptedCharField(
        max_length=11, verbose_name="Social Security Number"
    )  
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
auditlog.register(Donor)
auditlog.register(BloodInventory)
auditlog.register(TransfusionRecord)
auditlog.register(Crossmatch)

# Enhanced SMS and Staff Contact Models for Enterprise Integration
from django.core.validators import RegexValidator
import json

class StaffContact(models.Model):
    """
    Staff contact model for emergency notifications
    HIPAA compliant with limited data retention
    """
    ROLE_CHOICES = [
        ('BLOOD_BANK_TECH', 'Blood Bank Technician'),
        ('LAB_SUPERVISOR', 'Laboratory Supervisor'),
        ('HEMATOLOGIST', 'Hematologist'),
        ('NURSE_MANAGER', 'Nurse Manager'),
        ('PHYSICIAN', 'Physician'),
        ('ADMINISTRATOR', 'Administrator'),
    ]

    name = models.CharField(max_length=100, verbose_name="Full Name")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Role")
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        verbose_name="Phone Number"
    )
    email = models.EmailField(blank=True, null=True, verbose_name="Email Address")
    department = models.CharField(max_length=50, default="Blood Bank", verbose_name="Department")
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    is_on_call = models.BooleanField(default=False, verbose_name="Currently On Call")
    receives_blood_bank_alerts = models.BooleanField(default=True, verbose_name="Receives Blood Bank Alerts")
    receives_expiry_alerts = models.BooleanField(default=True, verbose_name="Receives Expiry Alerts")
    receives_emergency_alerts = models.BooleanField(default=True, verbose_name="Receives Emergency Alerts")

    # Availability scheduling
    shift_start = models.TimeField(blank=True, null=True, verbose_name="Shift Start Time")
    shift_end = models.TimeField(blank=True, null=True, verbose_name="Shift End Time")
    work_days = models.CharField(
        max_length=20,
        blank=True,
        help_text="Comma-separated days (e.g., 'Mon,Tue,Wed,Thu,Fri')",
        verbose_name="Work Days"
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_by = models.CharField(max_length=50, blank=True, verbose_name="Created By")
    last_contacted = models.DateTimeField(blank=True, null=True, verbose_name="Last Contacted")

    class Meta:
        verbose_name = "Staff Contact"
        verbose_name_plural = "Staff Contacts"
        ordering = ['name', 'role']

    def __str__(self):
        return f"{self.name} ({self.role})"

    def is_available_now(self):
        """Check if staff member is currently available"""
        if not self.is_active:
            return False

        now = timezone.now()
        current_time = now.time()
        current_day = now.strftime('%a')[:3]  # Mon, Tue, etc.

        # Check if today is a work day
        if self.work_days:
            work_days = [day.strip().title() for day in self.work_days.split(',')]
            if current_day not in work_days:
                return False

        # Check if within shift hours
        if self.shift_start and self.shift_end:
            if self.shift_start <= self.shift_end:
                # Normal shift (e.g., 9 AM - 5 PM)
                return self.shift_start <= current_time <= self.shift_end
            else:
                # Overnight shift (e.g., 11 PM - 7 AM)
                return current_time >= self.shift_start or current_time <= self.shift_end

        return True  # Available if no shift restrictions

    def contact_for_alert_type(self, alert_type):
        """Check if this contact should receive specific alert types"""
        alert_type_mapping = {
            'expiry': self.receives_expiry_alerts,
            'emergency': self.receives_emergency_alerts,
            'blood_bank': self.receives_blood_bank_alerts,
        }
        return alert_type_mapping.get(alert_type, True)

class SMSLog(models.Model):
    """
    SMS communication log for HIPAA compliance audit trail
    Limited data retention with privacy protection
    """
    MESSAGE_TYPES = [
        ('NOTIFICATION', 'General Notification'),
        ('ALERT', 'System Alert'),
        ('EMERGENCY', 'Emergency Alert'),
        ('REMINDER', 'Reminder'),
        ('BLOOD_BANK_EXPIRY', 'Blood Bank Expiry Alert'),
        ('BLOOD_BANK_EMERGENCY', 'Blood Bank Emergency'),
    ]

    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
        ('UNKNOWN', 'Unknown'),
    ]

    # Privacy-compliant fields (limited PII)
    recipient_last_4 = models.CharField(max_length=4, verbose_name="Recipient (Last 4 digits)")
    message_preview = models.CharField(max_length=50, verbose_name="Message Preview")
    message_id = models.CharField(max_length=100, unique=True, verbose_name="Message ID")
    provider = models.CharField(max_length=20, verbose_name="SMS Provider")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Status")
    message_type = models.CharField(max_length=30, choices=MESSAGE_TYPES, verbose_name="Message Type")
    priority = models.CharField(max_length=10, default='normal', verbose_name="Priority")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Sent At")
    delivered_at = models.DateTimeField(blank=True, null=True, verbose_name="Delivered At")

    # Additional metadata
    cost = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True, verbose_name="Cost")
    error_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Error Code")
    error_message = models.TextField(blank=True, null=True, verbose_name="Error Message")
    callback_url = models.URLField(blank=True, null=True, verbose_name="Callback URL")

    # Reference fields
    purpose = models.CharField(max_length=100, verbose_name="Purpose")
    reference_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Reference ID")
    user_initiated = models.BooleanField(default=False, verbose_name="User Initiated")

    class Meta:
        verbose_name = "SMS Log"
        verbose_name_plural = "SMS Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['message_type']),
        ]

    def __str__(self):
        return f"SMS to ...{self.recipient_last_4} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def mark_as_sent(self):
        """Mark SMS as sent"""
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])

    def mark_as_delivered(self):
        """Mark SMS as delivered"""
        self.status = 'DELIVERED'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])

    def mark_as_failed(self, error_code=None, error_message=None):
        """Mark SMS as failed"""
        self.status = 'FAILED'
        self.error_code = error_code
        self.error_message = error_message
        self.save(update_fields=['status', 'error_code', 'error_message'])

class LogEntry(models.Model):
    """
    Blood Bank operation log for audit trail
    """
    ACTION_CHOICES = [
        ('INVENTORY_UPDATE', 'Inventory Update'),
        ('ALERT_SENT', 'Alert Sent'),
        ('EXPIRY_CHECK', 'Expiry Check'),
        ('DONATION_RECEIVED', 'Donation Received'),
        ('BLOOD_ISSUED', 'Blood Issued'),
        ('SYSTEM_ALERT', 'System Alert'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, verbose_name="Action")
    details = models.TextField(verbose_name="Details")
    user = models.CharField(max_length=50, blank=True, null=True, verbose_name="User")
    blood_unit_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Blood Unit ID")

    class Meta:
        verbose_name = "Log Entry"
        verbose_name_plural = "Log Entries"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"