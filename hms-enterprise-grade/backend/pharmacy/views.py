import requests
from core.permissions import ModuleEnabledPermission
from django.db import models
from django.shortcuts import render
from django.utils import timezone
from rest_framework import decorators, response, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import InventoryTransaction, Medication, Prescription
from .serializers import (
    InventoryTransactionSerializer,
    MedicationSerializer,
    PrescriptionSerializer,
)

# Create your views here.


class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_pharmacy"

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


class MedicationViewSet(TenantScopedViewSet):
    serializer_class = MedicationSerializer
    queryset = Medication.objects.all()
    filterset_fields = ["name"]
    search_fields = ["name"]

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)

    @decorators.action(detail=False, methods=["get"])
    def low_stock(self, request):
        self.throttle_scope = "inventory"
        qs = self.get_queryset().filter(stock_quantity__lt=models.F("min_stock_level"))
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = MedicationSerializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = MedicationSerializer(qs, many=True)
        return response.Response(ser.data)

    @decorators.action(detail=False, methods=["post"])
    def auto_reorder(self, request):
        qs = self.get_queryset().filter(stock_quantity__lt=models.F("min_stock_level"))
        provider_url = request.data.get("provider_url") or ""
        token = request.data.get("token") or ""
        placed = []
        for m in qs:
            try:
                if provider_url:
                    requests.post(
                        provider_url,
                        json={
                            "item": m.name,
                            "qty": int(m.min_stock_level) - int(m.stock_quantity) + 1,
                        },
                        headers={"Authorization": f"Bearer {token}"} if token else {},
                        timeout=5,
                    )
                placed.append({"medication": m.name})
            except Exception:
                continue
        return response.Response({"orders": placed})


class PrescriptionViewSet(TenantScopedViewSet):
    serializer_class = PrescriptionSerializer
    queryset = Prescription.objects.select_related(
        "patient", "doctor", "medication", "encounter"
    ).all()

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)
        prescription = self.get_queryset().order_by("-id").first()

    @decorators.action(detail=True, methods=["post"])
    def dispense(self, request, pk=None):
        obj = self.get_object()
        if obj.is_dispensed:
            return response.Response({"detail": "Already dispensed"}, status=400)
        med = obj.medication
        if med.stock_quantity < obj.quantity:
            return response.Response({"detail": "Insufficient stock"}, status=400)
        med.stock_quantity -= obj.quantity
        med.save(update_fields=["stock_quantity"])
        obj.is_dispensed = True
        from django.utils import timezone as djtz

        obj.dispensed_at = djtz.now()
        obj.save(update_fields=["is_dispensed", "dispensed_at"])
        return response.Response(PrescriptionSerializer(obj).data)


class InventoryTransactionViewSet(TenantScopedViewSet):
    serializer_class = InventoryTransactionSerializer
    queryset = InventoryTransaction.objects.select_related("medication").all()

    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)
        transaction = self.get_queryset().order_by("-id").first()
        med = transaction.medication
        med.stock_quantity = med.stock_quantity + transaction.change
        med.save(update_fields=["stock_quantity"])
