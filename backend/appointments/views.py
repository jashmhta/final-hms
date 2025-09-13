from datetime import datetime, time, timedelta

from core.permissions import ModuleEnabledPermission, RolePermission
from django.conf import settings
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Appointment,
    AppointmentHistory,
    AppointmentReminder,
    AppointmentStatus,
    AppointmentTemplate,
    Resource,
    WaitList,
)
from .serializers import (
    AppointmentBasicSerializer,
    AppointmentHistorySerializer,
    AppointmentReminderSerializer,
    AppointmentSerializer,
    AppointmentTemplateSerializer,
    ResourceSerializer,
    WaitListSerializer,
)


class AppointmentTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentTemplateSerializer
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["appointment_type", "is_active", "allows_online_booking"]
    search_fields = ["name", "description", "specialty_required"]
    ordering_fields = ["name", "appointment_type", "duration_minutes"]

    def get_queryset(self):
        user = self.request.user
        qs = AppointmentTemplate.objects.all()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None) is None:
            return qs.none()
        return qs.filter(hospital_id=user.hospital_id)


class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "resource_type",
        "is_active",
        "is_bookable",
        "requires_approval",
    ]
    search_fields = ["name", "description", "location"]
    ordering_fields = ["name", "resource_type", "capacity"]

    def get_queryset(self):
        user = self.request.user
        qs = Resource.objects.all()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None) is None:
            return qs.none()
        return qs.filter(hospital_id=user.hospital_id)

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        """Check resource availability for a given time period"""
        resource = self.get_object()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get existing bookings
        bookings = resource.appointmentresource_set.filter(
            start_time__date__lte=end_date, end_time__date__gte=start_date
        )

        availability_data = {
            "resource": ResourceSerializer(resource).data,
            "bookings": [
                {
                    "start_time": booking.start_time,
                    "end_time": booking.end_time,
                    "appointment_id": booking.appointment.id,
                    "notes": booking.notes,
                }
                for booking in bookings
            ],
        }

        return Response(availability_data)


class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "status",
        "appointment_type",
        "priority",
        "is_telehealth",
        "is_recurring",
        "primary_provider",
        "patient",
        "confirmation_required",
    ]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "primary_provider__first_name",
        "primary_provider__last_name",
        "reason",
        "appointment_number",
    ]
    ordering_fields = ["start_at", "created_at", "priority", "status"]

    def get_serializer_class(self):
        if self.action == "list":
            return AppointmentBasicSerializer
        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related(
            "patient", "primary_provider", "hospital", "template"
        ).all()

        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            queryset = qs
        elif getattr(user, "hospital_id", None) is None:
            queryset = qs.none()
        else:
            queryset = qs.filter(hospital_id=user.hospital_id)

        # Role-based filtering for non-admin users
        if not (
            user.is_superuser
            or getattr(user, "role", None) in ["SUPER_ADMIN", "HOSPITAL_ADMIN", "ADMIN"]
        ):
            if hasattr(user, "patient_profile"):
                # Patient can only see their own appointments
                queryset = queryset.filter(patient=user.patient_profile)
            elif user.role in ["DOCTOR", "NURSE"]:
                # Healthcare providers can see appointments they're involved in
                queryset = queryset.filter(
                    Q(primary_provider=user) | Q(additional_providers=user)
                ).distinct()
            else:
                # Others get no appointments unless explicitly authorized
                queryset = queryset.none()

        # Date range filtering
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            queryset = queryset.filter(start_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_at__date__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        provided_hospital = serializer.validated_data.get("hospital")

        if not (
            user.is_superuser
            or getattr(user, "hospital_id", None)
            or getattr(user, "role", None) == "SUPER_ADMIN"
        ):
            raise PermissionDenied(
                "User must belong to a hospital to create appointments"
            )

        if (
            provided_hospital
            and not (user.is_superuser or user.role == "SUPER_ADMIN")
            and provided_hospital.id != user.hospital_id
        ):
            raise PermissionDenied("Cannot create appointment for another hospital")

        serializer.save(
            hospital_id=(
                provided_hospital.id if provided_hospital else user.hospital_id
            ),
            scheduled_by=user,
        )

    @action(detail=False, methods=["get"])
    def today(self, request):
        """Get all appointments for today"""
        today = timezone.now().date()
        appointments = self.get_queryset().filter(start_at__date=today)
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Get upcoming appointments"""
        now = timezone.now()
        days = int(request.query_params.get("days", 7))  # Default to 7 days
        end_date = now + timedelta(days=days)

        appointments = (
            self.get_queryset()
            .filter(
                start_at__gte=now,
                start_at__lte=end_date,
                status__in=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED],
            )
            .order_by("start_at")
        )

        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """Get appointment statistics"""
        queryset = self.get_queryset()

        # Date range for statistics
        start_date = request.query_params.get(
            "start_date", timezone.now().date() - timedelta(days=30)
        )
        end_date = request.query_params.get("end_date", timezone.now().date())

        stats_queryset = queryset.filter(
            start_at__date__gte=start_date, start_at__date__lte=end_date
        )

        stats = {
            "total_appointments": stats_queryset.count(),
            "completed": stats_queryset.filter(
                status=AppointmentStatus.COMPLETED
            ).count(),
            "cancelled": stats_queryset.filter(
                status=AppointmentStatus.CANCELLED
            ).count(),
            "no_shows": stats_queryset.filter(status=AppointmentStatus.NO_SHOW).count(),
            "scheduled": stats_queryset.filter(
                status=AppointmentStatus.SCHEDULED
            ).count(),
            "confirmed": stats_queryset.filter(
                status=AppointmentStatus.CONFIRMED
            ).count(),
            "by_type": list(
                stats_queryset.values("appointment_type").annotate(count=Count("id"))
            ),
            "by_provider": list(
                stats_queryset.values(
                    "primary_provider__first_name", "primary_provider__last_name"
                ).annotate(count=Count("id"))[:10]
            ),
        }

        return Response(stats)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm an appointment"""
        appointment = self.get_object()
        if appointment.status != AppointmentStatus.SCHEDULED:
            return Response(
                {"error": "Only scheduled appointments can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = AppointmentStatus.CONFIRMED
        appointment.confirmed_at = timezone.now()
        appointment.confirmed_by = request.user
        appointment.save()

        # Create history entry
        AppointmentHistory.objects.create(
            appointment=appointment,
            action="CONFIRMED",
            changed_by=request.user,
            notes=request.data.get("notes", ""),
        )

        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def check_in(self, request, pk=None):
        """Check in patient for appointment"""
        appointment = self.get_object()
        if appointment.status not in [
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
        ]:
            return Response(
                {"error": "Cannot check in this appointment"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.check_in(request.user)

        # Create history entry
        AppointmentHistory.objects.create(
            appointment=appointment,
            action="CHECKED_IN",
            changed_by=request.user,
            notes=request.data.get("notes", ""),
        )

        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """Start the appointment"""
        appointment = self.get_object()
        if appointment.status != AppointmentStatus.CHECKED_IN:
            return Response(
                {"error": "Patient must be checked in first"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = AppointmentStatus.IN_PROGRESS
        appointment.save()

        # Create history entry
        AppointmentHistory.objects.create(
            appointment=appointment,
            action="STARTED",
            changed_by=request.user,
            notes=request.data.get("notes", ""),
        )

        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, RolePermission],
    )
    def complete(self, request, pk=None):
        """Complete the appointment"""
        self.allowed_roles = ["DOCTOR", "NURSE", "HOSPITAL_ADMIN"]
        appointment = self.get_object()

        if appointment.status not in [
            AppointmentStatus.IN_PROGRESS,
            AppointmentStatus.CHECKED_IN,
        ]:
            return Response(
                {"error": "Appointment must be in progress or checked in"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = AppointmentStatus.COMPLETED
        appointment.save()

        # Generate bill if not exists
        try:
            from billing.models import Bill, BillLineItem, ServiceCatalog

            bill = Bill.objects.filter(appointment=appointment).first()
            if bill is None:
                bill = Bill.objects.create(
                    hospital=appointment.hospital,
                    patient=appointment.patient,
                    appointment=appointment,
                )
                service = ServiceCatalog.objects.filter(
                    hospital=appointment.hospital, code="CONSULT", active=True
                ).first()
                unit_price = service.price_cents if service else 0
                BillLineItem.objects.create(
                    hospital=appointment.hospital,
                    bill=bill,
                    description="Consultation",
                    quantity=1,
                    unit_price_cents=unit_price,
                )
        except Exception:
            pass

        # Create history entry
        AppointmentHistory.objects.create(
            appointment=appointment,
            action="COMPLETED",
            changed_by=request.user,
            notes=request.data.get("notes", ""),
        )

        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, RolePermission],
    )
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        self.allowed_roles = ["DOCTOR", "NURSE", "HOSPITAL_ADMIN"]
        appointment = self.get_object()

        if not appointment.can_be_cancelled():
            return Response(
                {"error": "This appointment cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_by = request.user
        appointment.cancelled_at = timezone.now()
        appointment.cancellation_reason = request.data.get("reason", "")
        appointment.cancellation_notes = request.data.get("notes", "")
        appointment.save()

        # Create history entry
        AppointmentHistory.objects.create(
            appointment=appointment,
            action="CANCELLED",
            changed_by=request.user,
            notes=f"Reason: {appointment.cancellation_reason}",
        )

        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reschedule(self, request, pk=None):
        """Reschedule an appointment"""
        appointment = self.get_object()
        new_start_time = request.data.get("start_at")
        new_end_time = request.data.get("end_at")

        if not new_start_time or not new_end_time:
            return Response(
                {"error": "start_at and end_at are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_start = appointment.start_at
        old_end = appointment.end_at

        appointment.start_at = new_start_time
        appointment.end_at = new_end_time
        appointment.status = AppointmentStatus.RESCHEDULED
        appointment.save()

        # Create history entry
        AppointmentHistory.objects.create(
            appointment=appointment,
            action="RESCHEDULED",
            field_changed="start_at, end_at",
            old_value=f"{old_start} - {old_end}",
            new_value=f"{new_start_time} - {new_end_time}",
            changed_by=request.user,
            notes=request.data.get("notes", ""),
        )

        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_no_show(self, request, pk=None):
        """Mark appointment as no-show"""
        appointment = self.get_object()
        appointment.mark_as_no_show(request.user)

        # Create history entry
        AppointmentHistory.objects.create(
            appointment=appointment,
            action="NO_SHOW",
            changed_by=request.user,
            notes=request.data.get("notes", ""),
        )

        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def available_slots(self, request):
        """Get available appointment slots for a provider"""
        self.throttle_scope = "slots"
        # Params: doctor (id), date=YYYY-MM-DD
        doctor_id = request.query_params.get("doctor")
        date_str = request.query_params.get("date")
        if not (doctor_id and date_str):
            return Response({"detail": "doctor and date are required"}, status=400)

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Invalid date"}, status=400)

        slot_minutes = settings.DEFAULT_APPOINTMENT_SLOT_MINUTES

        # Get roster shift times for the doctor (if any), else default 9-17
        from hr.models import DutyRoster

        roster = (
            DutyRoster.objects.filter(user_id=doctor_id, date=target_date)
            .select_related("shift")
            .first()
        )
        if roster and roster.shift:
            start_t: time = roster.shift.start_time
            end_t: time = roster.shift.end_time
        else:
            start_t = time(9, 0)
            end_t = time(17, 0)

        # Build list of candidate slots and exclude overlaps
        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(target_date, start_t), tz)
        end_dt = timezone.make_aware(datetime.combine(target_date, end_t), tz)
        slots = []
        current = start_dt

        # Use primary_provider instead of doctor for the enhanced model
        existing = Appointment.objects.filter(
            primary_provider_id=doctor_id,
            start_at__date=target_date,
            status__in=[
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.IN_PROGRESS,
            ],
        ).values_list("start_at", "end_at")

        while current + timedelta(minutes=slot_minutes) <= end_dt:
            next_dt = current + timedelta(minutes=slot_minutes)
            overlap = False
            for s, e in existing:
                if s < next_dt and e > current:
                    overlap = True
                    break
            if not overlap and current > timezone.now():
                slots.append(
                    {"start_at": current.isoformat(), "end_at": next_dt.isoformat()}
                )
            current = next_dt

        return Response({"doctor": int(doctor_id), "date": date_str, "slots": slots})


class WaitListViewSet(viewsets.ModelViewSet):
    serializer_class = WaitListSerializer
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["provider", "appointment_type", "priority", "is_active"]
    search_fields = ["patient__first_name", "patient__last_name", "reason"]
    ordering_fields = ["priority", "created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = WaitList.objects.all()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None) is None:
            return qs.none()
        return qs.filter(hospital_id=user.hospital_id)

    @action(detail=True, methods=["post"])
    def notify(self, request, pk=None):
        """Notify patient about available appointment slot"""
        waitlist_entry = self.get_object()

        # Implementation would send notification to patient
        waitlist_entry.notified_count += 1
        waitlist_entry.last_notification = timezone.now()
        waitlist_entry.save()

        return Response(
            {
                "message": "Patient notified successfully",
                "notified_count": waitlist_entry.notified_count,
            }
        )


class AppointmentReminderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AppointmentReminderSerializer
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["appointment", "reminder_type", "status"]
    ordering_fields = ["scheduled_for", "sent_at"]

    def get_queryset(self):
        user = self.request.user
        qs = AppointmentReminder.objects.select_related("appointment").all()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None) is None:
            return qs.none()
        return qs.filter(appointment__hospital_id=user.hospital_id)


class AppointmentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AppointmentHistorySerializer
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["appointment", "action", "changed_by"]
    ordering_fields = ["-timestamp"]

    def get_queryset(self):
        user = self.request.user
        qs = AppointmentHistory.objects.select_related(
            "appointment", "changed_by"
        ).all()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None) is None:
            return qs.none()
        return qs.filter(appointment__hospital_id=user.hospital_id)
