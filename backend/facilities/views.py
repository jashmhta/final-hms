from rest_framework import decorators, response, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import render

from core.permissions import ModuleEnabledPermission, RolePermission

from .models import Bed, Ward
from .serializers import BedSerializer, WardSerializer


class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RolePermission, ModuleEnabledPermission]
    allowed_roles = ["HOSPITAL_ADMIN"]
    required_module = "enable_ipd"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None) is None:
            return qs.none()
        return qs.filter(hospital_id=user.hospital_id)

    def ensure_tenant_on_create(self, serializer):
        user = self.request.user
        provided_hospital = serializer.validated_data.get("hospital")
        if not (
            user.is_superuser or getattr(user, "hospital_id", None) or getattr(user, "role", None) == "SUPER_ADMIN"
        ):
            raise PermissionDenied("User must belong to a hospital to create")
        if (
            provided_hospital
            and not (user.is_superuser or user.role == "SUPER_ADMIN")
            and provided_hospital.id != user.hospital_id
        ):
            raise PermissionDenied("Cannot create for another hospital")
        serializer.save(hospital_id=(provided_hospital.id if provided_hospital else user.hospital_id))


class WardViewSet(TenantScopedViewSet):
    serializer_class = WardSerializer
    queryset = Ward.objects.all()

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)


class BedViewSet(TenantScopedViewSet):
    serializer_class = BedSerializer
    queryset = Bed.objects.select_related("ward", "occupant").all()

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)

    @decorators.action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        bed = self.get_object()
        patient_id = request.data.get("patient")
        if not patient_id:
            raise PermissionDenied("patient is required")
        bed.occupant_id = patient_id
        bed.is_occupied = True
        bed.save(update_fields=["occupant_id", "is_occupied"])
        return response.Response(BedSerializer(bed).data)

    @decorators.action(detail=True, methods=["post"])
    def release(self, request, pk=None):
        bed = self.get_object()
        bed.occupant = None
        bed.is_occupied = False
        bed.save(update_fields=["occupant", "is_occupied"])
        return response.Response(BedSerializer(bed).data)
