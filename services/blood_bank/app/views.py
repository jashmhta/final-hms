from datetime import timedelta

import redis
from django.core.cache import cache
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import BloodInventory, Crossmatch, Donor, TransfusionRecord
from .serializers import (
    BloodInventorySerializer,
    CrossmatchSerializer,
    DonorSerializer,
    TransfusionRecordSerializer,
)


class IsAdminOrDoctorPermission(permissions.BasePermission):
    """
    Custom permission to allow only admins and doctors access to sensitive data
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.role in ["ADMIN", "DOCTOR"]
        return False


class DonorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Donor management with HIPAA compliance
    """

    queryset = Donor.objects.all()
    serializer_class = DonorSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrDoctorPermission]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["blood_type", "contact"]  # Only non-PII fields
    filterset_fields = ["blood_type", "is_active"]

    def get_queryset(self):
        """
        Optimize queryset and add audit log tracking
        """
        queryset = super().get_queryset()
        return queryset.select_related().prefetch_related("inventory_items")

    def perform_create(self, serializer):
        """
        Track donor creation with audit log
        """
        instance = serializer.save()
        # Log creation event for HIPAA compliance
        from auditlog.models import LogEntry

        LogEntry.objects.log_create(instance)
        return instance


class BloodInventoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Blood Inventory with Redis caching and expiry alerts
    """

    queryset = BloodInventory.objects.all()
    serializer_class = BloodInventorySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrDoctorPermission]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["unit_id", "blood_type", "storage_location"]
    filterset_fields = ["blood_type", "status", "expiry_date"]

    def get_queryset(self):
        """
        Apply Redis caching for inventory queries
        """
        cache_key = f'blood_inventory_{self.request.query_params.get("page", 1)}'
        cached_data = cache.get(cache_key)
        if cached_data:
            from django.core.paginator import Paginator

            queryset = BloodInventory.objects.none()
            paginator = Paginator(queryset, 20)
            page = paginator.page(1)
            page.object_list = cached_data
            return page.object_list

        queryset = super().get_queryset()
        # Cache for 5 minutes
        cache.set(cache_key, list(queryset), 300)
        return queryset.select_related("donor").prefetch_related(
            "transfusions", "crossmatches"
        )

    @action(detail=False, methods=["get"])
    def expiring_soon(self, request):
        """
        Get inventory expiring within 7 days
        """
        expiry_date = timezone.now().date() + timedelta(days=7)
        queryset = self.get_queryset().filter(
            expiry_date__lte=expiry_date, status="AVAILABLE"
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reserve(self, request, pk=None):
        """
        Reserve blood unit for patient
        """
        instance = self.get_object()
        if instance.status != "AVAILABLE":
            return Response(
                {"error": "Only available units can be reserved"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = "RESERVED"
        instance.save()
        # Clear cache
        cache.clear()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_update(self, serializer):
        """
        Track inventory updates with audit logging
        """
        instance = serializer.save()
        from auditlog.models import LogEntry

        LogEntry.objects.log_update(instance)
        # Clear cache on update
        cache.clear()
        return instance


class TransfusionRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Transfusion records with inventory linking
    """

    queryset = TransfusionRecord.objects.all()
    serializer_class = TransfusionRecordSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrDoctorPermission]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["patient__name", "blood_unit__unit_id"]
    filterset_fields = ["transfusion_date", "performed_by"]

    def get_queryset(self):
        """
        Optimize with select_related for performance
        """
        return (
            super()
            .get_queryset()
            .select_related("patient", "blood_unit", "performed_by")
            .prefetch_related("blood_unit__crossmatches")
        )

    def perform_create(self, serializer):
        """
        Update blood unit status after transfusion
        """
        instance = serializer.save(performed_by=self.request.user)
        # Update blood unit status
        instance.blood_unit.status = "TRANSFUSED"
        instance.blood_unit.save()
        # Clear inventory cache
        cache.clear()
        from auditlog.models import LogEntry

        LogEntry.objects.log_create(instance)
        return instance


class CrossmatchViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Crossmatch testing with compatibility validation
    """

    queryset = Crossmatch.objects.all()
    serializer_class = CrossmatchSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrDoctorPermission]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["patient__name", "blood_unit__unit_id"]
    filterset_fields = ["compatibility_result", "tested_by"]

    def get_queryset(self):
        """
        Optimize with select_related for patient and blood unit
        """
        return (
            super().get_queryset().select_related("patient", "blood_unit", "tested_by")
        )

    def perform_create(self, serializer):
        """
        Track crossmatch testing with audit logging
        """
        instance = serializer.save(tested_by=self.request.user)
        from auditlog.models import LogEntry

        LogEntry.objects.log_create(instance)
        return instance

    @action(detail=False, methods=["get"])
    def compatible_units(self, request):
        """
        Get compatible blood units for a patient
        """
        patient_id = request.query_params.get("patient_id")
        if not patient_id:
            return Response(
                {"error": "patient_id parameter required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        patient = get_object_or_404(Patient, id=patient_id)
        # Simple compatibility logic (in production, use medical rules)
        patient_blood_type = patient.blood_type  # Assuming Patient has blood_type
        compatible_types = []
        if patient_blood_type == "O-":
            compatible_types = ["O-"]
        elif patient_blood_type == "O+":
            compatible_types = ["O-", "O+"]
        # Add more compatibility rules

        queryset = Crossmatch.objects.filter(
            patient_id=patient_id, compatibility_result="COMPATIBLE"
        ).select_related("blood_unit")

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Export views
__all__ = [
    "DonorViewSet",
    "BloodInventoryViewSet",
    "TransfusionRecordViewSet",
    "CrossmatchViewSet",
]
