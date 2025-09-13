from core.permissions import ModuleEnabledPermission
from django.shortcuts import render
from rest_framework import decorators, response, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import LabOrder, LabResult, LabTest
from .serializers import LabOrderSerializer, LabResultSerializer, LabTestSerializer

# Create your views here.


class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_diagnostics"

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
            user.is_superuser
            or getattr(user, "hospital_id", None)
            or getattr(user, "role", None) == "SUPER_ADMIN"
        ):
            raise PermissionDenied("User must belong to a hospital to create")
        if (
            provided_hospital
            and not (user.is_superuser or user.role == "SUPER_ADMIN")
            and provided_hospital.id != user.hospital_id
        ):
            raise PermissionDenied("Cannot create for another hospital")
        serializer.save(
            hospital_id=(
                provided_hospital.id if provided_hospital else user.hospital_id
            )
        )


class LabTestViewSet(TenantScopedViewSet):
    serializer_class = LabTestSerializer
    queryset = LabTest.objects.all()

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)


class LabOrderViewSet(TenantScopedViewSet):
    serializer_class = LabOrderSerializer
    queryset = LabOrder.objects.select_related("patient", "doctor", "test").all()

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)


class LabResultViewSet(TenantScopedViewSet):
    serializer_class = LabResultSerializer
    queryset = LabResult.objects.select_related("order", "order__patient").all()

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)

    @decorators.action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        import csv

        from django.http import HttpResponse

        qs = self.get_queryset()
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="lab_results.csv"'
        writer = csv.writer(resp)
        writer.writerow(["Order ID", "Patient ID", "Test", "Result", "Recorded At"])
        for r in qs:
            writer.writerow(
                [
                    r.order_id,
                    r.order.patient_id if r.order and r.order.patient_id else "",
                    getattr(r.order, "test_id", ""),
                    getattr(r, "value", ""),
                    getattr(r, "created_at", ""),
                ]
            )
        return resp
