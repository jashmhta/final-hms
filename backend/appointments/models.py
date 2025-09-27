"""
models module
"""

import uuid
from datetime import timedelta

from encrypted_model_fields.fields import EncryptedTextField

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import TenantModel


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
    name = models.CharField(max_length=200)
    appointment_type = models.CharField(max_length=20, choices=AppointmentType.choices)
    duration_minutes = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True)
    allows_online_booking = models.BooleanField(default=True)
    requires_preparation = models.BooleanField(default=False)
    preparation_instructions = models.TextField(blank=True)
    specialty_required = models.CharField(max_length=100, blank=True)
    equipment_required = models.JSONField(default=list, blank=True)
    advance_booking_days = models.PositiveIntegerField(default=1)
    cancellation_hours = models.PositiveIntegerField(default=24)
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
    is_bookable = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    min_booking_duration = models.PositiveIntegerField(
        default=15, help_text="Minimum booking duration in minutes"
    )
    max_booking_duration = models.PositiveIntegerField(
        default=480, help_text="Maximum booking duration in minutes"
    )
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
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    appointment_number = models.CharField(max_length=50, db_index=True, default="TEMP")
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="appointments",
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
    appointment_type = models.CharField(
        max_length=20,
        choices=AppointmentType.choices,
        default=AppointmentType.ROUTINE,
    )
    template = models.ForeignKey(
        AppointmentTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(
        max_length=16,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.NORMAL
    )
    reason = models.CharField(max_length=255, blank=True)
    chief_complaint = EncryptedTextField(blank=True)
    clinical_notes = EncryptedTextField(blank=True)
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
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checked_in_appointments",
    )
    location = models.CharField(max_length=200, blank=True)
    room = models.CharField(max_length=100, blank=True)
    resources = models.ManyToManyField(
        Resource, blank=True, through="AppointmentResource"
    )
    insurance_authorization = models.CharField(max_length=100, blank=True)
    copay_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    patient_instructions = models.TextField(blank=True)
    preparation_instructions = models.TextField(blank=True)
    is_telehealth = models.BooleanField(default=False)
    telehealth_link = models.URLField(blank=True)
    telehealth_platform = models.CharField(max_length=50, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=15,
        choices=RecurrencePattern.choices,
        default=RecurrencePattern.NONE,
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
    no_show_at = models.DateTimeField(null=True, blank=True)
    no_show_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_confidential = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
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
            models.Index(fields=["hospital", "status", "start_at"]),
            models.Index(fields=["hospital", "primary_provider", "status", "start_at"]),
            models.Index(fields=["hospital", "patient", "status"]),
            models.Index(fields=["hospital", "appointment_type", "status"]),
            models.Index(fields=["hospital", "is_telehealth", "start_at"]),
            models.Index(fields=["hospital", "priority", "start_at"]),
            models.Index(fields=["hospital", "created_at"]),
            models.Index(fields=["hospital", "start_at", "end_at"]),
            models.Index(fields=["hospital", "primary_provider", "start_at", "status"]),
            models.Index(fields=["hospital", "patient", "start_at", "status"]),
            models.Index(fields=["hospital", "appointment_type", "start_at", "status"]),
        ]
        ordering = ["start_at"]

    def clean(self):
        if self.end_at <= self.start_at:
            raise ValidationError("end_at must be after start_at")
        if self.status not in [
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        ]:
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
        if not self.appointment_number:
            import time

            timestamp = str(int(time.time()))
            self.appointment_number = f"APT{timestamp[-8:]}"
        if self.start_at and self.end_at:
            duration = (self.end_at - self.start_at).total_seconds() / 60
            self.duration_minutes = int(duration)
        if self.is_recurring and not self.series_id:
            self.series_id = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{self.patient} with {self.primary_provider} at "
            f"{timezone.localtime(self.start_at)}"
        )

    def get_duration_display(self):
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        return f"{minutes}m"

    def can_be_cancelled(self):
        if self.status in [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        ]:
            return False
        if self.template and self.template.cancellation_hours:
            cutoff = self.start_at - timedelta(hours=self.template.cancellation_hours)
            return timezone.now() < cutoff
        return True

    def mark_as_no_show(self, user=None):
        self.status = AppointmentStatus.NO_SHOW
        self.no_show_at = timezone.now()
        if user:
            self.cancelled_by = user
        self.save()

    def check_in(self, user):
        self.status = AppointmentStatus.CHECKED_IN
        self.checked_in_at = timezone.now()
        self.checked_in_by = user
        self.save()

    @property
    def doctor(self):
        return self.primary_provider

    @doctor.setter
    def doctor(self, value):
        self.primary_provider = value

    @property
    def notes(self):
        return self.clinical_notes

    @notes.setter
    def notes(self, value):
        self.clinical_notes = value


class AppointmentResource(models.Model):
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
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="waitlist_entries",
    )
    provider = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="waitlist_entries"
    )
    appointment_type = models.CharField(max_length=20, choices=AppointmentType.choices)
    preferred_date_from = models.DateField()
    preferred_date_to = models.DateField()
    preferred_times = models.JSONField(
        default=list, help_text="List of preferred time slots"
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.NORMAL
    )
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
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
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
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
    field_changed = models.CharField(max_length=50, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    notes = models.TextField(blank=True)
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


class SurgeryType(TenantModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    estimated_duration = models.PositiveIntegerField(default=60)
    complexity_level = models.CharField(
        max_length=20, choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High")]
    )
    requires_anesthesia = models.BooleanField(default=True)
    anesthesia_type = models.CharField(max_length=50, blank=True)
    required_equipment = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["hospital", "is_active"]),
        ]

    def __str__(self):
        return self.name


class OTStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    CONFIRMED = "CONFIRMED", "Confirmed"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    DELAYED = "DELAYED", "Delayed"


class OTSlot(TenantModel):
    ot_room = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="ot_slots",
        limit_choices_to={"resource_type": "ROOM"},
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)
    max_cases = models.PositiveIntegerField(default=1)
    scheduled_cases = models.PositiveIntegerField(default=0)
    surgery_type_allowed = models.ManyToManyField(SurgeryType, blank=True)
    requires_anesthesia = models.BooleanField(default=True)
    equipment_needed = models.JSONField(default=list, blank=True)
    scheduled_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["ot_room", "start_time"]),
            models.Index(fields=["is_available", "start_time"]),
        ]

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")
        if self.duration_minutes <= 0:
            raise ValidationError("Duration must be positive")

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            self.duration_minutes = int(
                (self.end_time - self.start_time).total_seconds() / 60
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OT Slot {self.ot_room.name} - {self.start_time}"

    def get_remaining_capacity(self):
        return self.max_cases - self.scheduled_cases

    def is_fully_booked(self):
        return self.scheduled_cases >= self.max_cases

    def can_accommodate_case(self, surgery_type, duration):
        if not self.is_available:
            return False
        if self.is_fully_booked():
            return False
        if surgery_type not in self.surgery_type_allowed.all():
            return False
        if duration > self.duration_minutes:
            return False
        return True


class OTBooking(TenantModel):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name="ot_booking"
    )
    ot_slot = models.ForeignKey(
        OTSlot, on_delete=models.CASCADE, related_name="bookings"
    )
    lead_surgeon = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="lead_ot_bookings",
        limit_choices_to={"role": "SURGEON"},
    )
    assisting_surgeon = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assisting_ot_bookings",
        limit_choices_to={"role": "SURGEON"},
    )
    anesthesiologist = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anesthesiologist_ot_bookings",
        limit_choices_to={"role": "ANESTHESIOLOGIST"},
    )
    scrub_nurse = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scrub_ot_bookings",
        limit_choices_to={"role": "NURSE"},
    )
    circulating_nurse = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="circulating_ot_bookings",
        limit_choices_to={"role": "NURSE"},
    )
    procedure_name = models.CharField(max_length=255)
    procedure_code = models.CharField(max_length=50, blank=True)
    estimated_duration = models.PositiveIntegerField()
    actual_duration = models.PositiveIntegerField(null=True, blank=True)
    surgery_type = models.ForeignKey(SurgeryType, on_delete=models.PROTECT)
    anesthesia_type = models.CharField(max_length=50, blank=True)
    anesthesia_notes = models.TextField(blank=True)
    pre_op_checklist_completed = models.BooleanField(default=False)
    time_out_completed = models.BooleanField(default=False)
    pre_op_labs_reviewed = models.BooleanField(default=False)
    informed_consent = models.BooleanField(default=False)
    incision_time = models.DateTimeField(null=True, blank=True)
    closure_time = models.DateTimeField(null=True, blank=True)
    blood_loss_ml = models.PositiveIntegerField(null=True, blank=True)
    fluids_given_ml = models.PositiveIntegerField(null=True, blank=True)
    specimens_sent = models.TextField(blank=True)
    complications = models.TextField(blank=True)
    recovery_room_assigned = models.BooleanField(default=False)
    post_op_orders = models.TextField(blank=True)
    pain_management_plan = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=OTStatus.choices, default=OTStatus.SCHEDULED
    )
    booked_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booked_ot_bookings",
    )
    confirmed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_ot_bookings",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.NORMAL
    )
    is_confidential = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ot_slot", "status"]),
            models.Index(fields=["appointment", "status"]),
        ]

    def clean(self):
        if self.appointment and self.ot_slot:
            if not (
                self.appointment.start_at == self.ot_slot.start_time
                and self.appointment.end_at == self.ot_slot.end_time
            ):
                raise ValidationError("Appointment timing must match OT slot")
        if (
            self.ot_slot
            and self.surgery_type not in self.ot_slot.surgery_type_allowed.all()
        ):
            raise ValidationError("Surgery type not allowed in this OT slot")
        if self.estimated_duration > self.ot_slot.duration_minutes:
            raise ValidationError("Estimated duration exceeds slot time")

    def save(self, *args, **kwargs):
        if self.ot_slot:
            if self.pk is None:
                self.ot_slot.scheduled_cases += 1
                self.ot_slot.is_available = (
                    self.ot_slot.scheduled_cases < self.ot_slot.max_cases
                )
                self.ot_slot.save()
            else:
                old = OTBooking.objects.get(pk=self.pk)
                if old.ot_slot != self.ot_slot:
                    old.ot_slot.scheduled_cases -= 1
                    old.ot_slot.save()
                    self.ot_slot.scheduled_cases += 1
                    self.ot_slot.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.ot_slot:
            self.ot_slot.scheduled_cases -= 1
            self.ot_slot.is_available = (
                self.ot_slot.scheduled_cases < self.ot_slot.max_cases
            )
            self.ot_slot.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return (
            f"OT Booking {self.appointment.appointment_number} - {self.procedure_name}"
        )

    def is_ready_for_surgery(self):
        return (
            self.pre_op_checklist_completed
            and self.time_out_completed
            and self.pre_op_labs_reviewed
            and self.informed_consent
        )

    def calculate_actual_duration(self):
        if self.incision_time and self.closure_time:
            duration = (self.closure_time - self.incision_time).total_seconds() / 60
            self.actual_duration = int(duration)
            self.save()
            return self.actual_duration
        return None
