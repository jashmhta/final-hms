import json
import uuid
from datetime import datetime, timedelta

from core.models import TenantModel
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedTextField


class AppointmentStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CHECKED_IN = "CHECKED_IN", "Checked In"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    NO_SHOW = "NO_SHOW", "No Show"
    CANCELLED = "CANCELLED", "Cancelled"
    RESCHEDULED = "RESCHEDULED", "Rescheduled"
    ON_HOLD = "ON_HOLD", "On Hold"


class AppointmentType(models.TextChoices):
    ROUTINE = "ROUTINE", "Routine Visit"
    FOLLOW_UP = "FOLLOW_UP", "Follow-up"
    ANNUAL_PHYSICAL = "ANNUAL_PHYSICAL", "Annual Physical"
    CONSULTATION = "CONSULTATION", "Consultation"
    PROCEDURE = "PROCEDURE", "Procedure"
    EMERGENCY = "EMERGENCY", "Emergency"
    URGENT = "URGENT", "Urgent Care"
    TELEHEALTH = "TELEHEALTH", "Telehealth"
    PREVENTIVE = "PREVENTIVE", "Preventive Care"
    SPECIALIST = "SPECIALIST", "Specialist Visit"
    SURGICAL = "SURGICAL", "Surgical Consultation"
    DIAGNOSTIC = "DIAGNOSTIC", "Diagnostic"
    THERAPY = "THERAPY", "Therapy Session"
    VACCINATION = "VACCINATION", "Vaccination"
    LAB_WORK = "LAB_WORK", "Lab Work"
    IMAGING = "IMAGING", "Imaging"


class Priority(models.TextChoices):
    LOW = "LOW", "Low"
    NORMAL = "NORMAL", "Normal"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent"
    EMERGENT = "EMERGENT", "Emergent"


class RecurrencePattern(models.TextChoices):
    NONE = "NONE", "None"
    DAILY = "DAILY", "Daily"
    WEEKLY = "WEEKLY", "Weekly"
    BIWEEKLY = "BIWEEKLY", "Bi-weekly"
    MONTHLY = "MONTHLY", "Monthly"
    QUARTERLY = "QUARTERLY", "Quarterly"
    ANNUALLY = "ANNUALLY", "Annually"
    CUSTOM = "CUSTOM", "Custom"


class AppointmentTemplate(TenantModel):
    """Templates for common appointment types"""

    name = models.CharField(max_length=200)
    appointment_type = models.CharField(max_length=20, choices=AppointmentType.choices)
    duration_minutes = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True)

    # Default settings
    allows_online_booking = models.BooleanField(default=True)
    requires_preparation = models.BooleanField(default=False)
    preparation_instructions = models.TextField(blank=True)

    # Specialty requirements
    specialty_required = models.CharField(max_length=100, blank=True)
    equipment_required = models.JSONField(default=list, blank=True)

    # Scheduling rules
    advance_booking_days = models.PositiveIntegerField(default=1)
    cancellation_hours = models.PositiveIntegerField(default=24)

    # Cost information
    base_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["hospital", "appointment_type"]),
        ]

    def __str__(self):
        return f"{self.hospital.name} - {self.name}"


class Resource(TenantModel):
    """Bookable resources like rooms, equipment, etc."""

    name = models.CharField(max_length=200)
    resource_type = models.CharField(
        max_length=20,
        choices=[
            ("ROOM", "Room"),
            ("EQUIPMENT", "Equipment"),
            ("BED", "Bed"),
            ("VEHICLE", "Vehicle"),
            ("STAFF", "Staff"),
            ("OTHER", "Other"),
        ],
    )

    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(default=1)

    # Availability
    is_bookable = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)

    # Scheduling constraints
    min_booking_duration = models.PositiveIntegerField(
        default=15, help_text="Minimum booking duration in minutes"
    )
    max_booking_duration = models.PositiveIntegerField(
        default=480, help_text="Maximum booking duration in minutes"
    )

    # Cost
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["hospital", "resource_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.resource_type})"


class Appointment(TenantModel):
    """Enhanced appointment model with enterprise features"""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    appointment_number = models.CharField(max_length=50, db_index=True, default="TEMP")

    # Patient & Provider
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="appointments"
    )
    primary_provider = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="primary_appointments",
        null=True,
    )
    additional_providers = models.ManyToManyField(
        "users.User", blank=True, related_name="additional_appointments"
    )

    # Appointment Details
    appointment_type = models.CharField(
        max_length=20, choices=AppointmentType.choices, default=AppointmentType.ROUTINE
    )
    template = models.ForeignKey(
        AppointmentTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Timing
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)

    # Status & Priority
    status = models.CharField(
        max_length=16,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.NORMAL
    )

    # Clinical Information
    reason = models.CharField(max_length=255, blank=True)
    chief_complaint = EncryptedTextField(blank=True)
    clinical_notes = EncryptedTextField(blank=True)

    # Scheduling Information
    scheduled_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_appointments",
    )
    confirmation_required = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_appointments",
    )

    # Check-in Information
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checked_in_appointments",
    )

    # Location & Resources
    location = models.CharField(max_length=200, blank=True)
    room = models.CharField(max_length=100, blank=True)
    resources = models.ManyToManyField(
        Resource, blank=True, through="AppointmentResource"
    )

    # Insurance & Billing
    insurance_authorization = models.CharField(max_length=100, blank=True)
    copay_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Communication
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    patient_instructions = models.TextField(blank=True)
    preparation_instructions = models.TextField(blank=True)

    # Telehealth
    is_telehealth = models.BooleanField(default=False)
    telehealth_link = models.URLField(blank=True)
    telehealth_platform = models.CharField(max_length=50, blank=True)

    # Recurring Appointments
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=15, choices=RecurrencePattern.choices, default=RecurrencePattern.NONE
    )
    recurrence_end_date = models.DateField(null=True, blank=True)
    parent_appointment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recurring_appointments",
    )
    series_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Cancellation Information
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_appointments",
    )
    cancellation_reason = models.CharField(max_length=200, blank=True)
    cancellation_notes = models.TextField(blank=True)

    # No-show tracking
    no_show_at = models.DateTimeField(null=True, blank=True)
    no_show_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Administrative
    is_confidential = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Workflow
    requires_interpretation = models.BooleanField(default=False)
    interpreter_language = models.CharField(max_length=50, blank=True)
    requires_transportation = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["hospital", "primary_provider", "start_at"]),
            models.Index(fields=["hospital", "patient", "start_at"]),
            models.Index(fields=["status", "start_at"]),
            models.Index(fields=["appointment_type", "start_at"]),
            models.Index(fields=["series_id"]),
            models.Index(fields=["uuid"]),
            models.Index(fields=["appointment_number"]),
        ]
        ordering = ["start_at"]

    def clean(self):
        if self.end_at <= self.start_at:
            raise ValidationError("end_at must be after start_at")

        # Check for overlapping appointments for the same provider
        if self.status not in [AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]:
            overlapping = Appointment.objects.filter(
                hospital=self.hospital,
                primary_provider=self.primary_provider,
                status__in=[
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.CHECKED_IN,
                    AppointmentStatus.IN_PROGRESS,
                ],
            ).exclude(pk=self.pk)
            overlapping = overlapping.filter(
                start_at__lt=self.end_at, end_at__gt=self.start_at
            )

            if overlapping.exists():
                raise ValidationError("Overlapping appointment for this provider")

    def save(self, *args, **kwargs):
        # Generate appointment number if not provided
        if not self.appointment_number:
            import time

            timestamp = str(int(time.time()))
            self.appointment_number = f"APT{timestamp[-8:]}"

        # Set duration based on start/end times
        if self.start_at and self.end_at:
            duration = (self.end_at - self.start_at).total_seconds() / 60
            self.duration_minutes = int(duration)

        # Generate series ID for recurring appointments
        if self.is_recurring and not self.series_id:
            self.series_id = uuid.uuid4()

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.patient} with {self.primary_provider} at {timezone.localtime(self.start_at)}"

    def get_duration_display(self):
        """Return human-readable duration"""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        return f"{minutes}m"

    def can_be_cancelled(self):
        """Check if appointment can be cancelled based on timing and status"""
        if self.status in [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        ]:
            return False

        # Check if within cancellation window
        if self.template and self.template.cancellation_hours:
            cutoff = self.start_at - timedelta(hours=self.template.cancellation_hours)
            return timezone.now() < cutoff

        return True

    def mark_as_no_show(self, user=None):
        """Mark appointment as no-show"""
        self.status = AppointmentStatus.NO_SHOW
        self.no_show_at = timezone.now()
        if user:
            self.cancelled_by = user
        self.save()

    def check_in(self, user):
        """Check in the patient for the appointment"""
        self.status = AppointmentStatus.CHECKED_IN
        self.checked_in_at = timezone.now()
        self.checked_in_by = user
        self.save()

    # Backward compatibility properties
    @property
    def doctor(self):
        """Backward compatibility for existing code using 'doctor' field"""
        return self.primary_provider

    @doctor.setter
    def doctor(self, value):
        """Backward compatibility setter for 'doctor' field"""
        self.primary_provider = value

    @property
    def notes(self):
        """Backward compatibility for existing code using 'notes' field"""
        return self.clinical_notes

    @notes.setter
    def notes(self, value):
        """Backward compatibility setter for 'notes' field"""
        self.clinical_notes = value


class AppointmentResource(models.Model):
    """Through model for appointment-resource relationship"""

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ["appointment", "resource"]
        indexes = [
            models.Index(fields=["resource", "start_time"]),
        ]

    def clean(self):
        # Check resource availability
        overlapping = AppointmentResource.objects.filter(
            resource=self.resource,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError(
                f"Resource {self.resource.name} is not available during this time"
            )


class WaitList(TenantModel):
    """Patient wait list for appointments"""

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="waitlist_entries"
    )
    provider = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="waitlist_entries"
    )
    appointment_type = models.CharField(max_length=20, choices=AppointmentType.choices)

    # Preferences
    preferred_date_from = models.DateField()
    preferred_date_to = models.DateField()
    preferred_times = models.JSONField(
        default=list, help_text="List of preferred time slots"
    )

    # Priority & Notes
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.NORMAL
    )
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    notified_count = models.PositiveIntegerField(default=0)
    last_notification = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_waitlist_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "created_at"]
        indexes = [
            models.Index(fields=["hospital", "provider", "is_active"]),
            models.Index(fields=["priority", "created_at"]),
        ]

    def __str__(self):
        return f"Waitlist: {self.patient} for {self.provider}"


class AppointmentReminder(models.Model):
    """Automated appointment reminders"""

    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="reminders"
    )

    reminder_type = models.CharField(
        max_length=15,
        choices=[
            ("EMAIL", "Email"),
            ("SMS", "SMS"),
            ("PHONE", "Phone Call"),
            ("PORTAL", "Patient Portal"),
            ("PUSH", "Push Notification"),
        ],
    )

    # Scheduling
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)

    # Content
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)

    # Status
    status = models.CharField(
        max_length=10,
        choices=[
            ("PENDING", "Pending"),
            ("SENT", "Sent"),
            ("FAILED", "Failed"),
            ("CANCELLED", "Cancelled"),
        ],
        default="PENDING",
    )

    # Response tracking
    delivered_at = models.DateTimeField(null=True, blank=True)
    response_received = models.BooleanField(default=False)
    response_type = models.CharField(
        max_length=15,
        choices=[
            ("CONFIRM", "Confirmed"),
            ("RESCHEDULE", "Reschedule Request"),
            ("CANCEL", "Cancellation"),
            ("OTHER", "Other"),
        ],
        blank=True,
    )
    response_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_for"]
        indexes = [
            models.Index(fields=["appointment", "status"]),
            models.Index(fields=["scheduled_for", "status"]),
        ]

    def __str__(self):
        return f"{self.reminder_type} reminder for {self.appointment}"


class AppointmentHistory(models.Model):
    """Track appointment changes and history"""

    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="history"
    )

    action = models.CharField(
        max_length=15,
        choices=[
            ("CREATED", "Created"),
            ("UPDATED", "Updated"),
            ("CONFIRMED", "Confirmed"),
            ("CHECKED_IN", "Checked In"),
            ("STARTED", "Started"),
            ("COMPLETED", "Completed"),
            ("CANCELLED", "Cancelled"),
            ("RESCHEDULED", "Rescheduled"),
            ("NO_SHOW", "No Show"),
        ],
    )

    # Change details
    field_changed = models.CharField(max_length=50, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    # Actor information
    changed_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["appointment", "-timestamp"]),
            models.Index(fields=["action", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.appointment} - {self.action} at {self.timestamp}"
