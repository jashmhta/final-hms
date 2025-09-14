import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status
from rest_framework.filters import DjangoFilterBackend, OrderingFilter
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models.appointment_model import Appointment
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentSerializer,
    AppointmentUpdateSerializer,
)
from .services.appointment_service import (
    AppointmentService,
    InvalidAppointmentError,
    SchedulingConflictError,
)

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for appointment listings."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class AppointmentListView(ListAPIView):
    """
    API endpoint for listing appointments.

    Follows SRP: Handles only HTTP request/response for listing, delegates business logic to service.
    Supports filtering by patient, provider, date, status, and pagination.

    Filters:
        - patient_id: Filter by patient
        - provider_id: Filter by provider
        - date: Filter by appointment date (YYYY-MM-DD)
        - status: Filter by appointment status
        - appointment_type: Filter by appointment type
    """

    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["patient_id", "provider_id", "status", "appointment_type"]
    ordering_fields = ["start_time", "end_time", "created_at", "status"]
    ordering = ["start_time"]

    def get_queryset(self):
        """
        Get filtered queryset with date filtering for appointments.

        Returns:
            Queryset of appointments with related patient/provider data
        """
        queryset = Appointment.objects.filter(is_active=True).select_related(
            "patient", "provider"
        )

        # Date filtering
        date_filter = self.request.query_params.get("date")
        if date_filter:
            try:
                appointment_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                start_of_day = timezone.datetime.combine(
                    appointment_date, datetime.min.time()
                )
                end_of_day = timezone.datetime.combine(
                    appointment_date, datetime.max.time()
                )
                queryset = queryset.filter(
                    start_time__gte=start_of_day, start_time__lte=end_of_day
                )
            except ValueError:
                logger.warning(f"Invalid date format: {date_filter}")
                # Return empty queryset for invalid date
                return Appointment.objects.none()

        return queryset

    def get_serializer_context(self) -> Dict[str, Any]:
        """Add request context to serializer."""
        context = super().get_serializer_context()
        context.update(
            {
                "request": self.request,
                "user": self.request.user,
            }
        )
        return context


class AppointmentCreateView(CreateAPIView):
    """
    API endpoint for creating new appointments.

    Follows SRP: Handles HTTP request/response, delegates business logic to AppointmentService.
    Performs comprehensive validation through service layer.

    Request Body:
        - patient_id (int): Patient identifier
        - provider_id (int): Provider identifier
        - start_time (datetime): Appointment start time (ISO format)
        - duration_minutes (int, optional): Duration in minutes (default: 30)
        - appointment_type (str, optional): Type of appointment (default: 'consultation')
        - notes (str, optional): Additional notes
    """

    serializer_class = AppointmentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Create appointment using service layer for business logic.

        Args:
            request: HTTP request with appointment data

        Returns:
            Response with created appointment data or error details
        """
        try:
            # Initialize service with dependency injection
            appointment_service = AppointmentService()

            # Extract data from validated serializer
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            # Create appointment through service layer
            appointment = appointment_service.create_appointment(
                patient_id=validated_data["patient_id"],
                provider_id=validated_data["provider_id"],
                start_time=validated_data["start_time"],
                duration=timedelta(minutes=validated_data.get("duration_minutes", 30)),
                appointment_type=validated_data.get("appointment_type", "consultation"),
                notes=validated_data.get("notes", ""),
            )

            # Serialize response
            response_serializer = AppointmentSerializer(appointment)

            logger.info(
                f'Appointment created successfully: {appointment.id} for patient {validated_data["patient_id"]}'
            )

            return Response(
                {
                    "message": "Appointment created successfully",
                    "data": response_serializer.data,
                    "id": str(appointment.id),
                },
                status=status.HTTP_201_CREATED,
            )

        except SchedulingConflictError as e:
            logger.warning(f"Scheduling conflict: {e}")
            return Response(
                {
                    "error": "Scheduling conflict",
                    "message": str(e),
                    "code": "SCHEDULING_CONFLICT",
                },
                status=status.HTTP_409_CONFLICT,
            )

        except InvalidAppointmentError as e:
            logger.warning(f"Invalid appointment: {e}")
            return Response(
                {
                    "error": "Invalid appointment",
                    "message": str(e),
                    "code": "INVALID_APPOINTMENT",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Unexpected error creating appointment: {e}")
            return Response(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "code": "INTERNAL_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AppointmentDetailView(RetrieveAPIView):
    """
    API endpoint for retrieving a specific appointment.

    Follows SRP: Handles retrieval of single appointment with related data.
    """

    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        """Get active appointments only."""
        return Appointment.objects.filter(is_active=True).select_related(
            "patient", "provider"
        )

    def retrieve(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve appointment details with service layer validation.

        Args:
            request: HTTP request
            args: Additional arguments
            kwargs: Keyword arguments including appointment ID

        Returns:
            Response with appointment data or 404 if not found
        """
        instance = self.get_object()

        # Use service layer for additional business logic if needed
        appointment_service = AppointmentService()
        appointment_data = appointment_service.get_appointment_details(instance)

        serializer = self.get_serializer(instance)
        return Response(
            {"data": serializer.data, "metadata": appointment_data.get("metadata", {})}
        )


class AppointmentUpdateView(UpdateAPIView):
    """
    API endpoint for updating existing appointments.

    Follows SRP: Handles HTTP request/response for updates, delegates to service.
    Supports partial updates and status changes.

    Request Body:
        - start_time (datetime, optional): New start time
        - duration_minutes (int, optional): New duration
        - status (str, optional): New status (requires permission)
        - notes (str, optional): Additional notes
    """

    serializer_class = AppointmentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        """Get active appointments that can be updated."""
        return Appointment.objects.filter(is_active=True)

    def update(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Update appointment using service layer for business logic.

        Args:
            request: HTTP request with update data
            args: Additional arguments
            kwargs: Keyword arguments including appointment ID

        Returns:
            Response with updated appointment or error details
        """
        try:
            instance = self.get_object()

            # Validate serializer
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(
                    {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )

            # Prepare updates
            updates = {}
            if "start_time" in serializer.validated_data:
                updates["start_time"] = serializer.validated_data["start_time"]
                duration = timedelta(
                    minutes=serializer.validated_data.get(
                        "duration_minutes", instance.duration_minutes
                    )
                )
                updates["end_time"] = updates["start_time"] + duration

            if "duration_minutes" in serializer.validated_data:
                duration = timedelta(
                    minutes=serializer.validated_data["duration_minutes"]
                )
                updates["end_time"] = instance.start_time + duration
                updates["duration_minutes"] = serializer.validated_data[
                    "duration_minutes"
                ]

            if "status" in serializer.validated_data:
                updates["status"] = serializer.validated_data["status"]

            if "notes" in serializer.validated_data:
                updates["notes"] = serializer.validated_data["notes"]

            # Update through service layer
            appointment_service = AppointmentService()
            updated_appointment = appointment_service.update_appointment(
                appointment=instance, **updates
            )

            # Serialize response
            response_serializer = AppointmentSerializer(updated_appointment)

            logger.info(f"Appointment updated: {updated_appointment.id} - {updates}")

            return Response(
                {
                    "message": "Appointment updated successfully",
                    "data": response_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except SchedulingConflictError as e:
            return Response(
                {
                    "error": "Scheduling conflict",
                    "message": str(e),
                    "code": "SCHEDULING_CONFLICT",
                },
                status=status.HTTP_409_CONFLICT,
            )

        except InvalidAppointmentError as e:
            return Response(
                {
                    "error": "Invalid appointment update",
                    "message": str(e),
                    "code": "INVALID_UPDATE",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(
                f'Unexpected error updating appointment {kwargs.get("id")}: {e}'
            )
            return Response(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "code": "INTERNAL_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AppointmentCancelView(DestroyAPIView):
    """
    API endpoint for cancelling appointments.

    Follows SRP: Handles cancellation requests, delegates to service layer.

    Request Body:
        - reason (str, optional): Cancellation reason
    """

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        """Get appointments that can be cancelled."""
        return Appointment.objects.filter(is_active=True)

    def delete(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Cancel appointment using service layer.

        Args:
            request: HTTP request with cancellation reason
            args: Additional arguments
            kwargs: Keyword arguments including appointment ID

        Returns:
            Response confirming cancellation or error details
        """
        try:
            instance = self.get_object()
            reason = request.data.get("reason", "")

            # Cancel through service layer
            appointment_service = AppointmentService()
            appointment_service.cancel_appointment(appointment=instance, reason=reason)

            logger.info(f"Appointment cancelled: {instance.id} - {reason}")

            return Response(
                {
                    "message": "Appointment cancelled successfully",
                    "appointment_id": str(instance.id),
                    "reason": reason,
                },
                status=status.HTTP_200_OK,
            )

        except InvalidAppointmentError as e:
            return Response(
                {
                    "error": "Cannot cancel appointment",
                    "message": str(e),
                    "code": "INVALID_CANCELLATION",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(
                f'Unexpected error cancelling appointment {kwargs.get("id")}: {e}'
            )
            return Response(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "code": "INTERNAL_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProviderAvailabilityView(APIView):
    """
    API endpoint for getting provider availability.

    Follows SRP: Handles availability queries, delegates to service layer.

    Query Parameters:
        - provider_id (int): Provider identifier
        - date (str): Date for availability (YYYY-MM-DD)
        - duration_minutes (int, optional): Required duration (default: 30)
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Get available appointment slots for a provider.

        Args:
            request: HTTP request with query parameters

        Returns:
            Response with available time slots
        """
        try:
            provider_id = request.query_params.get("provider_id")
            date_str = request.query_params.get("date")
            duration_minutes = int(request.query_params.get("duration_minutes", 30))

            if not provider_id or not date_str:
                return Response(
                    {
                        "error": "Missing required parameters",
                        "required": ["provider_id", "date"],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Parse date
            try:
                appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format", "expected": "YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get availability through service layer
            appointment_service = AppointmentService()
            available_slots = appointment_service.get_available_slots(
                provider_id=int(provider_id),
                date=appointment_date,
                duration=timedelta(minutes=duration_minutes),
            )

            # Format response
            slots_data = [
                {
                    "start_time": slot[0].isoformat(),
                    "end_time": slot[1].isoformat(),
                    "duration_minutes": duration_minutes,
                }
                for slot in available_slots
            ]

            logger.info(
                f"Availability retrieved for provider {provider_id} on {date_str}: {len(slots_data)} slots"
            )

            return Response(
                {
                    "provider_id": int(provider_id),
                    "date": date_str,
                    "duration_minutes": duration_minutes,
                    "available_slots": slots_data,
                    "total_slots": len(slots_data),
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            logger.warning(f"Invalid parameters for availability: {e}")
            return Response(
                {"error": "Invalid parameters", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Unexpected error getting availability: {e}")
            return Response(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
