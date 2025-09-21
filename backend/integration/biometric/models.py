import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from encrypted_model_fields.fields import EncryptedTextField

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel

User = get_user_model()


class BiometricDevice(TimeStampedModel):
    DEVICE_TYPES = [
        ("FINGERPRINT", "Fingerprint Scanner"),
        ("FACIAL", "Facial Recognition Camera"),
        ("IRIS", "Iris Scanner"),
        ("PALM_VEIN", "Palm Vein Scanner"),
        ("MULTI_MODAL", "Multi-Modal Biometric"),
    ]
    MANUFACTURERS = [
        ("MORPHO", "Morpho (Idemia)"),
        ("SECUGEN", "SecuGen"),
        ("CROSSMATCH", "Crossmatch"),
        ("HIKVISION", "Hikvision"),
        ("DAHUA", "Dahua"),
        ("ZKTECO", "ZKTeco"),
        ("IRIS_ID", "IrisID"),
        ("LG", "LG Iris"),
        ("PANASONIC", "Panasonic"),
        ("FUJITSU", "Fujitsu"),
        ("OTHER", "Other Manufacturer"),
    ]
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("MAINTENANCE", "Under Maintenance"),
        ("OFFLINE", "Offline"),
        ("ERROR", "Error State"),
    ]
    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.CASCADE, related_name="biometric_devices")
    device_id = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=200)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    manufacturer = models.CharField(max_length=20, choices=MANUFACTURERS)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField(protocol="both", unpack_ipv4=False)
    port = models.PositiveIntegerField(default=80)
    connection_protocol = models.CharField(
        max_length=10,
        choices=[("HTTP", "HTTP"), ("HTTPS", "HTTPS"), ("TCP", "TCP"), ("USB", "USB")],
        default="HTTP",
    )
    api_key = EncryptedTextField(blank=True)
    username = EncryptedTextField(blank=True)
    password = EncryptedTextField(blank=True)
    location = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    device_purpose = models.CharField(
        max_length=100,
        choices=[
            ("PATIENT_ID", "Patient Identification"),
            ("STAFF_ATTENDANCE", "Staff Attendance"),
            ("ACCESS_CONTROL", "Access Control"),
            ("REGISTRATION", "Registration Kiosk"),
            ("MULTI_PURPOSE", "Multi-Purpose"),
        ],
        default="MULTI_PURPOSE",
    )
    max_users = models.PositiveIntegerField(default=10000)
    template_size = models.PositiveIntegerField(default=512)
    verification_speed = models.FloatField(default=1.0)
    false_acceptance_rate = models.FloatField(default=0.0001)
    false_rejection_rate = models.FloatField(default=0.01)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="INACTIVE")
    last_seen = models.DateTimeField(null=True, blank=True)
    last_maintenance = models.DateTimeField(null=True, blank=True)
    next_maintenance = models.DateTimeField(null=True, blank=True)
    total_scans = models.PositiveIntegerField(default=0)
    successful_scans = models.PositiveIntegerField(default=0)
    failed_scans = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "hospital"]
        unique_together = ["hospital", "name"]

    def __str__(self):
        return f"{self.name} ({self.hospital.name})"

    def update_last_seen(self):
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen"])

    def get_success_rate(self):
        if self.total_scans == 0:
            return 0.0
        return (self.successful_scans / self.total_scans) * 100

    def needs_maintenance(self):
        if not self.next_maintenance:
            return False
        return timezone.now() >= self.next_maintenance


class BiometricTemplate(TimeStampedModel):
    TEMPLATE_TYPES = [
        ("FINGERPRINT", "Fingerprint"),
        ("FACIAL", "Facial Features"),
        ("IRIS", "Iris Pattern"),
        ("PALM_VEIN", "Palm Vein"),
    ]
    FINGERS = [
        ("LEFT_THUMB", "Left Thumb"),
        ("LEFT_INDEX", "Left Index"),
        ("LEFT_MIDDLE", "Left Middle"),
        ("LEFT_RING", "Left Ring"),
        ("LEFT_PINKY", "Left Pinky"),
        ("RIGHT_THUMB", "Right Thumb"),
        ("RIGHT_INDEX", "Right Index"),
        ("RIGHT_MIDDLE", "Right Middle"),
        ("RIGHT_RING", "Right Ring"),
        ("RIGHT_PINKY", "Right Pinky"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="biometric_templates")
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, null=True, blank=True, related_name="biometric_templates"
    )
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    finger_position = models.CharField(max_length=20, choices=FINGERS, null=True, blank=True)
    template_data = EncryptedTextField()
    template_format = models.CharField(max_length=50, default="ISO_19794_2")
    quality_score = models.FloatField(default=0.0)
    image_data = models.BinaryField(null=True, blank=True)
    enrolled_device = models.ForeignKey(BiometricDevice, on_delete=models.SET_NULL, null=True, blank=True)
    enrolled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrolled_templates"
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_count = models.PositiveIntegerField(default=0)
    last_verified = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    anti_spoofing_score = models.FloatField(null=True, blank=True)
    liveness_detection = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [
            ("user", "template_type", "finger_position"),
            ("patient", "template_type", "finger_position"),
        ]

    def __str__(self):
        person = self.user or self.patient
        return f"{person} - {self.template_type}"

    def mark_verified(self):
        self.is_verified = True
        self.last_verified = timezone.now()
        self.verification_count += 1
        self.save(update_fields=["is_verified", "last_verified", "verification_count"])

    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class BiometricLog(TimeStampedModel):
    OPERATION_TYPES = [
        ("ENROLLMENT", "Template Enrollment"),
        ("VERIFICATION", "Identity Verification"),
        ("IDENTIFICATION", "Identity Identification"),
        ("UPDATE", "Template Update"),
        ("DELETE", "Template Deletion"),
        ("SYNC", "Device Sync"),
        ("ERROR", "System Error"),
    ]
    RESULT_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("TIMEOUT", "Timeout"),
        ("ERROR", "System Error"),
        ("CANCELLED", "Cancelled"),
    ]
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    device = models.ForeignKey(BiometricDevice, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="biometric_logs")
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.SET_NULL, null=True, blank=True, related_name="biometric_logs"
    )
    template_used = models.ForeignKey(BiometricTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    processing_time = models.FloatField(help_text="Processing time in seconds")
    confidence_score = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location_data = models.JSONField(null=True, blank=True)
    risk_score = models.FloatField(null=True, blank=True)
    anomaly_detected = models.BooleanField(default=False)
    requires_review = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["operation_type", "result"]),
            models.Index(fields=["device", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["patient", "created_at"]),
        ]

    def __str__(self):
        return f"{self.operation_type} - {self.result} ({self.device.name})"

    def get_high_risk_indicators(self):
        indicators = []
        if self.risk_score and self.risk_score > 0.7:
            indicators.append("High risk score")
        if self.anomaly_detected:
            indicators.append("Anomaly detected")
        if self.processing_time > 10.0:
            indicators.append("Slow processing time")
        if self.result == "FAILED" and self.confidence_score and self.confidence_score > 0.8:
            indicators.append("High confidence failure")
        return indicators
