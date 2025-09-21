from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import render

from core.permissions import RolePermission

from .models import DutyRoster, LeaveRequest, Shift
from .serializers import DutyRosterSerializer, LeaveRequestSerializer, ShiftSerializer


class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RolePermission]
    allowed_roles = ["HOSPITAL_ADMIN"]

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


class ShiftViewSet(TenantScopedViewSet):
    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)


class DutyRosterViewSet(TenantScopedViewSet):
    serializer_class = DutyRosterSerializer
    queryset = DutyRoster.objects.select_related("user", "shift").all()

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)


class LeaveRequestViewSet(TenantScopedViewSet):
    serializer_class = LeaveRequestSerializer
    queryset = LeaveRequest.objects.select_related("user").all()

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)
