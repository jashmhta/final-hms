import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


# Assuming BaseModel is shared or create local version
class BaseModel(models.Model):
    """Abstract base model with common fields for all appointment entities."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {self.id}"

    def soft_delete(self) -> None:
        """Mark as inactive instead of hard delete."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])


class Appointment(BaseModel):
    """
    Appointment model for healthcare scheduling system.

    Follows SRP: Handles only appointment data persistence and basic validation.
    Complex scheduling logic delegated to AppointmentService.

    Fields:
        patient: Foreign key to Patient model
        provider: Foreign key to Provider model
        start_time: Appointment start datetime
        end_time: Appointment end datetime
        appointment_type: Type of appointment (consultation, followup, procedure)
        status: Appointment status (scheduled, confirmed, completed, cancelled)
        duration: Appointment duration in minutes
        notes: Additional appointment information
        cancellation_reason: Reason for cancellation (if applicable)
        confirmation_sent: Whether confirmation notification was sent
        metadata: JSON field for additional appointment data
    """

    APPOINTMENT_TYPES = [
        ("consultation", "Consultation"),
        ("followup", "Follow-up"),
        ("procedure", "Procedure"),
        ("telehealth", "Telehealth"),
        ("surgery", "Surgery"),
        ("diagnostic", "Diagnostic Test"),
    ]

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("confirmed", "Confirmed"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("no_show", "No Show"),
        ("rescheduled", "Rescheduled"),
    ]

    # Assuming Patient and Provider models exist in other modules
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="appointments",
        help_text="Patient for this appointment",
    )
    provider = models.ForeignKey(
        "providers.Provider",
        on_delete=models.CASCADE,
        related_name="appointments",
        help_text="Healthcare provider for this appointment",
    )
    start_time = models.DateTimeField(help_text="Appointment start time")
    end_time = models.DateTimeField(help_text="Appointment end time")
    appointment_type = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPES,
        default="consultation",
        help_text="Type of appointment",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
        help_text="Current status of appointment",
    )
    duration_minutes = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(120)],
        help_text="Appointment duration in minutes",
    )
    notes = models.TextField(blank=True, help_text="Additional appointment notes")
    cancellation_reason = models.CharField(
        max_length=200, blank=True, null=True, help_text="Reason for cancellation"
    )
    confirmation_sent = models.BooleanField(
        default=False, help_text="Whether confirmation notification was sent"
    )
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional appointment metadata"
    )

    class Meta:
        db_table = "appointments"
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        indexes = [
            models.Index(fields=["patient", "is_active"]),
            models.Index(fields=["provider", "is_active"]),
            models.Index(fields=["start_time", "end_time"]),
            models.Index(fields=["status", "start_time"]),
            models.Index(fields=["appointment_type"]),
            models.Index(fields=["provider", "start_time", "status"]),
            models.Index(fields=["patient", "start_time", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    status__in=[
                        "scheduled",
                        "confirmed",
                        "in_progress",
                        "completed",
                        "cancelled",
                        "no_show",
                        "rescheduled",
                    ]
                ),
                name="valid_appointment_status",
            ),
            models.CheckConstraint(
                check=models.Q(start_time__lt=models.F("end_time")),
                name="valid_time_range",
            ),
        ]

    def clean(self) -> None:
        """
        Validate appointment data integrity.
        Complex business validation should be in AppointmentService.
        """
        super().clean()

        # Validate time range
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

        # Validate duration consistency
        calculated_duration = (self.end_time - self.start_time).total_seconds() / 60
        if (
            abs(calculated_duration - self.duration_minutes) > 1
        ):  # Allow 1 minute tolerance
            raise ValidationError("Duration minutes must match calculated time range")

        # Validate appointment type
        if self.appointment_type not in dict(self.APPOINTMENT_TYPES).keys():
            raise ValidationError(f"Invalid appointment type: {self.appointment_type}")

        # Status-specific validation
        if self.status == "cancelled" and not self.cancellation_reason:
            raise ValidationError(
                "Cancellation reason is required for cancelled appointments"
            )

        # Prevent scheduling in past
        if self.start_time < timezone.now():
            if self.status not in ["in_progress", "completed"]:
                raise ValidationError("Cannot schedule appointments in the past")

    def update_status(self, new_status: str, notes: Optional[str] = None) -> None:
        """
        Update appointment status with validation.
        Status change logic should be in AppointmentService.
        """
        if new_status not in dict(self.STATUS_CHOICES).keys():
            raise ValueError(f"Invalid status: {new_status}")

        old_status = self.status
        self.status = new_status
        if notes:
            self.notes += f"\nStatus changed from {old_status} to {new_status}: {notes}"
        self.save(update_fields=["status", "notes", "updated_at"])

    @property
    def duration(self) -> timedelta:
        """Calculate appointment duration as timedelta."""
        return self.end_time - self.start_time

    @property
    def is_confirmed(self) -> bool:
        """Check if appointment is confirmed."""
        return self.status in ["confirmed", "in_progress", "completed"]

    @property
    def is_finalized(self) -> bool:
        """Check if appointment is in final state (cannot be modified)."""
        return self.status in ["completed", "cancelled", "no_show"]

    def get_conflict_overlap(
        self, other_appointment: "Appointment"
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Check for time overlap with another appointment.
        Returns overlap range if exists, None otherwise.
        """
        if (
            self.start_time < other_appointment.end_time
            and self.end_time > other_appointment.start_time
            and self.provider_id == other_appointment.provider_id
        ):

            overlap_start = max(self.start_time, other_appointment.start_time)
            overlap_end = min(self.end_time, other_appointment.end_time)
            return (overlap_start, overlap_end)
        return None

    @classmethod
    def get_overlapping_appointments(
        cls, provider_id: int, start_time: datetime, end_time: datetime
    ) -> List["Appointment"]:
        """
        Get all appointments that overlap with given time range for a provider.
        """
        return cls.objects.filter(
            provider_id=provider_id,
            start_time__lt=end_time,
            end_time__gt=start_time,
            is_active=True,
        ).select_related("patient", "provider")

    @classmethod
    def get_appointments_by_date(
        cls, date: datetime.date, status: Optional[str] = None
    ) -> List["Appointment"]:
        """
        Get all appointments for a specific date.
        """
        start_of_day = timezone.datetime.combine(date, datetime.time(0, 0))
        end_of_day = timezone.datetime.combine(date, datetime.time(23, 59, 59))

        queryset = (
            cls.objects.filter(
                start_time__gte=start_of_day, start_time__lte=end_of_day, is_active=True
            )
            .select_related("patient", "provider")
            .prefetch_related("metadata")
        )

        if status:
            queryset = queryset.filter(status=status)

        return list(queryset)

    def mark_as_no_show(self) -> None:
        """
        Mark appointment as no-show (patient didn't arrive).
        This should be called by AppointmentService with appropriate validation.
        """
        if self.status not in ["scheduled", "confirmed"]:
            raise ValueError(
                "Can only mark scheduled or confirmed appointments as no-show"
            )

        if self.start_time > timezone.now():
            raise ValueError("Cannot mark future appointments as no-show")

        self.status = "no_show"
        self.save(update_fields=["status", "updated_at"])
