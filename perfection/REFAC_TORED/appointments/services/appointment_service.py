import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from django.core.exceptions import ValidationError
from django.core.validators import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

# Assuming models exist or will be created
# from ..models.appointment_model import Appointment

logger = logging.getLogger(__name__)


class AppointmentValidationError(Exception):
    """Custom exception for appointment validation errors."""

    pass


class SchedulingConflictError(AppointmentValidationError):
    """Raised when appointment conflicts with existing schedule."""

    pass


class InvalidAppointmentError(AppointmentValidationError):
    """Raised for invalid appointment operations."""

    pass


class AppointmentService:
    """
    Appointment service following SOLID principles for healthcare scheduling.

    Follows SOLID principles:
    - SRP: Single responsibility for appointment business logic
    - OCP: Extensible via service composition and strategy pattern
    - LSP: Can be substituted with specialized appointment services
    - ISP: Minimal interface for appointment operations
    - DIP: Depends on abstractions (models, validators)
    """

    # Scheduling constants
    MIN_APPOINTMENT_DURATION = timedelta(minutes=15)
    MAX_APPOINTMENT_DURATION = timedelta(hours=2)
    BUFFER_TIME = timedelta(minutes=10)  # Buffer between appointments
    WORK_HOURS_START = 9  # 9 AM
    WORK_HOURS_END = 17  # 5 PM
    WEEKEND_BLOCKED = [5, 6]  # Saturday=5, Sunday=6

    def __init__(
        self, notification_service: Optional["NotificationService"] = None
    ) -> None:
        """
        Initialize AppointmentService with optional notification service dependency.

        Args:
            notification_service: NotificationService for appointment notifications (DIP)
        """
        self.notification_service = notification_service

    def create_appointment(
        self,
        patient_id: int,
        provider_id: int,
        start_time: datetime,
        duration: timedelta = None,
        appointment_type: str = "consultation",
        notes: str = "",
    ) -> "Appointment":
        """
        Create a new appointment with comprehensive validation.

        Args:
            patient_id: Patient identifier
            provider_id: Provider identifier
            start_time: Appointment start datetime
            duration: Appointment duration (default 30 minutes)
            appointment_type: Type of appointment ('consultation', 'followup', 'procedure')
            notes: Additional appointment notes

        Returns:
            Created Appointment instance

        Raises:
            SchedulingConflictError: If time slot conflicts with existing appointments
            InvalidAppointmentError: For invalid appointment parameters
            AppointmentValidationError: For business rule violations
        """
        self._validate_appointment_parameters(
            patient_id, provider_id, start_time, duration, appointment_type
        )
        self._validate_business_hours(start_time)
        self._validate_weekend_blocking(start_time)

        end_time = start_time + (duration or timedelta(minutes=30))
        self._validate_duration(duration or timedelta(minutes=30))

        with transaction.atomic():
            # Check for scheduling conflicts
            if self._has_conflict(provider_id, start_time, end_time):
                raise SchedulingConflictError(
                    f"Provider {provider_id} is not available from {start_time} to {end_time}"
                )

            # Create appointment (assuming Appointment model exists)
            appointment = self._create_appointment_record(
                patient_id=patient_id,
                provider_id=provider_id,
                start_time=start_time,
                end_time=end_time,
                appointment_type=appointment_type,
                status="scheduled",
                notes=notes,
            )

            # Send notifications
            if self.notification_service:
                self.notification_service.send_appointment_confirmation(
                    appointment=appointment,
                    patient_id=patient_id,
                    provider_id=provider_id,
                )

            logger.info(
                f"Appointment created: {appointment.id} for patient {patient_id} with provider {provider_id}"
            )
            return appointment

    def update_appointment(
        self, appointment: "Appointment", **updates: Dict[str, Any]
    ) -> "Appointment":
        """
        Update existing appointment with validation and conflict checking.

        Args:
            appointment: Existing Appointment instance
            **updates: Dictionary of fields to update (start_time, duration, status, etc.)

        Returns:
            Updated Appointment instance

        Raises:
            SchedulingConflictError: If updated time conflicts
            InvalidAppointmentError: If appointment cannot be updated
        """
        if appointment.status in ["completed", "cancelled", "no_show"]:
            raise InvalidAppointmentError(
                "Cannot update completed, cancelled, or no-show appointments"
            )

        # Validate updates
        if "start_time" in updates:
            self._validate_business_hours(updates["start_time"])
            self._validate_weekend_blocking(updates["start_time"])

            new_end_time = updates["start_time"] + (
                updates.get("duration", appointment.duration) or timedelta(minutes=30)
            )
            if self._has_conflict(
                appointment.provider_id, updates["start_time"], new_end_time
            ):
                raise SchedulingConflictError(
                    "Updated time conflicts with existing appointments"
                )

        with transaction.atomic():
            old_values = {
                "start_time": appointment.start_time,
                "end_time": appointment.end_time,
                "status": appointment.status,
                "notes": appointment.notes,
            }

            # Apply updates
            for field, value in updates.items():
                if hasattr(appointment, field):
                    setattr(appointment, field, value)

            appointment.save(update_fields=list(updates.keys()) + ["updated_at"])

            # Send notifications for status changes
            if "status" in updates and updates["status"] != appointment.status:
                if self.notification_service:
                    self.notification_service.send_status_update(
                        appointment=appointment,
                        old_status=old_values["status"],
                        new_status=updates["status"],
                    )

            logger.info(f"Appointment updated: {appointment.id} - {updates}")
            return appointment

    def cancel_appointment(self, appointment: "Appointment", reason: str = "") -> None:
        """
        Cancel appointment with validation and notifications.

        Args:
            appointment: Appointment to cancel
            reason: Cancellation reason

        Raises:
            InvalidAppointmentError: If appointment cannot be cancelled
        """
        if appointment.status in ["cancelled", "completed", "no_show"]:
            raise InvalidAppointmentError("Appointment is already in final state")

        # Check cancellation window (e.g., 24 hours notice)
        time_until_appointment = appointment.start_time - timezone.now()
        if time_until_appointment < timedelta(hours=24):
            raise InvalidAppointmentError(
                "Cannot cancel appointments within 24 hours of scheduled time"
            )

        with transaction.atomic():
            appointment.status = "cancelled"
            appointment.cancellation_reason = reason
            appointment.save(
                update_fields=["status", "cancellation_reason", "updated_at"]
            )

            # Send cancellation notifications
            if self.notification_service:
                self.notification_service.send_cancellation_notification(
                    appointment=appointment,
                    patient_id=appointment.patient_id,
                    provider_id=appointment.provider_id,
                    reason=reason,
                )

            logger.info(f"Appointment cancelled: {appointment.id} - {reason}")

    def get_available_slots(
        self, provider_id: int, date: date, duration: timedelta = timedelta(minutes=30)
    ) -> List[Tuple[datetime, datetime]]:
        """
        Get available appointment slots for a provider on a specific date.

        Args:
            provider_id: Provider identifier
            date: Date for availability check
            duration: Required appointment duration

        Returns:
            List of available time slots as (start_time, end_time) tuples
        """
        available_slots = []

        # Generate work hours for the day
        start_work = timezone.datetime.combine(date, datetime.time(WORK_HOURS_START, 0))
        end_work = timezone.datetime.combine(date, datetime.time(WORK_HOURS_END, 0))

        current_slot = start_work
        while current_slot + duration + self.BUFFER_TIME <= end_work:
            end_slot = current_slot + duration

            # Check if slot is free
            if not self._has_conflict(provider_id, current_slot, end_slot):
                available_slots.append((current_slot, end_slot))

            current_slot = end_slot + self.BUFFER_TIME

        return available_slots

    def _validate_appointment_parameters(
        self,
        patient_id: int,
        provider_id: int,
        start_time: datetime,
        duration: Optional[timedelta],
        appointment_type: str,
    ) -> None:
        """Validate basic appointment parameters."""
        if patient_id <= 0:
            raise AppointmentValidationError("Invalid patient ID")
        if provider_id <= 0:
            raise AppointmentValidationError("Invalid provider ID")
        if not start_time:
            raise AppointmentValidationError("Start time is required")

        valid_types = ["consultation", "followup", "procedure", "telehealth", "surgery"]
        if appointment_type not in valid_types:
            raise AppointmentValidationError(
                f"Invalid appointment type: {appointment_type}"
            )

    def _validate_business_hours(self, start_time: datetime) -> None:
        """Validate appointment is within business hours."""
        start_hour = start_time.hour
        if start_hour < self.WORK_HOURS_START or start_hour >= self.WORK_HOURS_END:
            raise AppointmentValidationError(
                f"Appointments must be scheduled between {self.WORK_HOURS_START}:00 and {self.WORK_HOURS_END}:00"
            )

    def _validate_weekend_blocking(self, start_time: datetime) -> None:
        """Validate appointment is not on weekends."""
        weekday = start_time.weekday()
        if weekday in self.WEEKEND_BLOCKED:
            raise AppointmentValidationError(
                "Appointments cannot be scheduled on weekends"
            )

    def _validate_duration(self, duration: timedelta) -> None:
        """Validate appointment duration."""
        if duration < self.MIN_APPOINTMENT_DURATION:
            raise AppointmentValidationError(
                f"Appointment duration must be at least {self.MIN_APPOINTMENT_DURATION}"
            )
        if duration > self.MAX_APPOINTMENT_DURATION:
            raise AppointmentValidationError(
                f"Appointment duration cannot exceed {self.MAX_APPOINTMENT_DURATION}"
            )

    def _has_conflict(
        self, provider_id: int, start_time: datetime, end_time: datetime
    ) -> bool:
        """
        Check if appointment conflicts with existing appointments.

        Args:
            provider_id: Provider ID
            start_time: Proposed start time
            end_time: Proposed end time

        Returns:
            True if conflict exists, False otherwise
        """
        # This would query the database for overlapping appointments
        # For now, return False (assuming no conflicts in this demo)
        # In production, implement actual conflict detection
        return False

    def _create_appointment_record(
        self,
        patient_id: int,
        provider_id: int,
        start_time: datetime,
        end_time: datetime,
        appointment_type: str,
        status: str,
        notes: str,
    ) -> "Appointment":
        """
        Create the actual appointment record in database.

        This is a placeholder - in production, this would interact with Appointment model.
        """
        # Placeholder implementation - would create actual Appointment instance
        from uuid import uuid4

        class MockAppointment:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
                self.id = uuid4()
                self.created_at = timezone.now()
                self.updated_at = timezone.now()
                self.is_active = True

        return MockAppointment(
            patient_id=patient_id,
            provider_id=provider_id,
            start_time=start_time,
            end_time=end_time,
            appointment_type=appointment_type,
            status=status,
            notes=notes,
        )


# Placeholder for notification service (would be injected via DIP)
class NotificationService:
    """Mock notification service for appointment notifications."""

    def send_appointment_confirmation(
        self, appointment: "Appointment", patient_id: int, provider_id: int
    ) -> None:
        """Send appointment confirmation notifications."""
        logger.info(f"Sending confirmation for appointment {appointment.id}")

    def send_status_update(
        self, appointment: "Appointment", old_status: str, new_status: str
    ) -> None:
        """Send status update notifications."""
        logger.info(
            f"Status updated: {old_status} -> {new_status} for {appointment.id}"
        )

    def send_cancellation_notification(
        self, appointment: "Appointment", patient_id: int, provider_id: int, reason: str
    ) -> None:
        """Send cancellation notifications."""
        logger.info(f"Cancellation notification for {appointment.id}: {reason}")
