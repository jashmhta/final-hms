from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import Hospital, HospitalPlan, Plan
from .serializers import HospitalPlanSerializer, HospitalSerializer, PlanSerializer

# Create your views here.


class IsSuperAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        base = super().has_permission(request, view)
        return base and (
            request.user.is_superuser
            or getattr(request.user, "role", None) == "SUPER_ADMIN"
        )


class HospitalViewSet(viewsets.ModelViewSet):
    serializer_class = HospitalSerializer
    queryset = Hospital.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "code"

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None):
            return qs.filter(id=user.hospital_id)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN"):
            raise PermissionDenied("Only super admin can create hospitals")
        serializer.save()


class PlanViewSet(viewsets.ModelViewSet):
    serializer_class = PlanSerializer
    queryset = Plan.objects.all()
    permission_classes = [IsSuperAdmin]


class HospitalPlanViewSet(viewsets.ModelViewSet):
    serializer_class = HospitalPlanSerializer
    queryset = HospitalPlan.objects.select_related("hospital", "plan").all()
    permission_classes = [IsSuperAdmin]
