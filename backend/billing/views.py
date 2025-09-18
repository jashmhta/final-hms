import csv
import os
import requests
from core.permissions import ModuleEnabledPermission
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from facilities.models import Bed
from lxml import etree
from openpyxl import Workbook
from rest_framework import decorators, response, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from .models import Bill, BillLineItem, DepartmentBudget, Payment, ServiceCatalog
from appointments.models import Appointment
from patients.models import Patient
from django.db.models import Prefetch
from .serializers import (
    BillLineItemSerializer,
    BillSerializer,
    DepartmentBudgetSerializer,
    PaymentSerializer,
    ServiceCatalogSerializer,
)
class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = None
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
class BillViewSet(TenantScopedViewSet):
    serializer_class = BillSerializer
    queryset = (
        Bill.objects.select_related("patient", "appointment")
        .prefetch_related(
            "items",
            "payments",
            Prefetch(
                "patient",
                queryset=Patient.objects.only(
                    "id", "first_name", "last_name", "medical_record_number"
                ),
            ),
            Prefetch(
                "appointment",
                queryset=Appointment.objects.only(
                    "id", "appointment_number", "start_at"
                ),
            ),
        )
        .all()
    )
    required_module = "enable_accounting"
    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)
    @decorators.action(detail=True, methods=["post"])
    def submit_claim(self, request, pk=None):
        bill = self.get_object()
        bill.insurance_claim_status = "SUBMITTED"
        bill.save(update_fields=["insurance_claim_status"])
        return response.Response(BillSerializer(bill).data)
    @decorators.action(detail=True, methods=["post"])
    def set_discount(self, request, pk=None):
        user = request.user
        if not (
            user.is_superuser
            or getattr(user, "role", None)
            in ["SUPER_ADMIN", "HOSPITAL_ADMIN", "BILLING_CLERK"]
        ):
            raise PermissionDenied("Not allowed to set discount")
        opa_url = os.getenv("OPA_URL")
        if opa_url:
            try:
                d = requests.post(
                    f"{opa_url}/v1/data/hms/allow",
                    json={
                        "input": {
                            "path": "/api/billing/bills/set_discount",
                            "role": getattr(user, "role", None),
                        }
                    },
                    timeout=2,
                )
                if d.ok and d.json().get("result") is False:
                    raise PermissionDenied("Policy denied")
            except Exception:
                pass
        bill = self.get_object()
        try:
            discount_cents = int(request.data.get("discount_cents", 0))
        except Exception:
            raise PermissionDenied("Invalid discount")
        if discount_cents < 0:
            raise PermissionDenied("Invalid discount")
        bill.discount_cents = discount_cents
        bill.recalc()
        return response.Response(BillSerializer(bill).data)
class BillLineItemViewSet(TenantScopedViewSet):
    serializer_class = BillLineItemSerializer
    queryset = BillLineItem.objects.select_related("bill", "bill__patient").all()
    required_module = "enable_accounting"
    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)
class PaymentViewSet(TenantScopedViewSet):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.select_related("bill", "bill__patient").all()
    required_module = "enable_accounting"
    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)
class ServiceCatalogViewSet(TenantScopedViewSet):
    serializer_class = ServiceCatalogSerializer
    queryset = ServiceCatalog.objects.all()
    required_module = "enable_accounting"
    def perform_create(self, serializer):
        self.ensure_tenant_on_create(serializer)
    @decorators.action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        qs = self.get_queryset()
        response_obj = HttpResponse(content_type="text/csv")
        response_obj["Content-Disposition"] = (
            'attachment; filename="service_catalog.csv"'
        )
        writer = csv.writer(response_obj)
        writer.writerow(["Code", "Name", "Price (cents)", "Active"])
        for item in qs:
            writer.writerow([item.code, item.name, item.price_cents, item.active])
        return response_obj
class AccountingViewSet(TenantScopedViewSet):
    serializer_class = BillSerializer
    queryset = Bill.objects.all()
    required_module = "enable_accounting"
    @decorators.action(detail=False, methods=["get"], url_path="department-pl")
    def department_pl(self, request):
        qs = self.get_queryset()
        qs = qs.prefetch_related("items")
        dept_totals = (
            BillLineItem.objects.filter(bill__in=qs)
            .values("department")
            .annotate(total=Sum("amount_cents"))
        )
        data = {row["department"]: row["total"] or 0 for row in dept_totals}
        return response.Response({"department_totals_cents": data})
    @decorators.action(detail=False, methods=["get"], url_path="export-bills")
    def export_bills_csv(self, request):
        qs = self.get_queryset().prefetch_related("items", "payments")
        response_obj = HttpResponse(content_type="text/csv")
        response_obj["Content-Disposition"] = 'attachment; filename="bills.csv"'
        writer = csv.writer(response_obj)
        writer.writerow(
            ["Bill ID", "Patient ID", "Total", "Discount", "Net", "Paid", "Status"]
        )
        for b in qs:
            writer.writerow(
                [
                    b.id,
                    b.patient_id,
                    b.total_cents,
                    b.discount_cents,
                    b.net_cents,
                    b.paid_cents,
                    b.status,
                ]
            )
        return response_obj
    @decorators.action(detail=False, methods=["get"], url_path="export-bills-xlsx")
    def export_bills_xlsx(self, request):
        qs = self.get_queryset().prefetch_related("items", "payments")
        wb = Workbook()
        ws = wb.active
        ws.title = "Bills"
        ws.append(
            ["Bill ID", "Patient ID", "Total", "Discount", "Net", "Paid", "Status"]
        )
        for b in qs:
            ws.append(
                [
                    b.id,
                    b.patient_id,
                    b.total_cents,
                    b.discount_cents,
                    b.net_cents,
                    b.paid_cents,
                    b.status,
                ]
            )
        resp = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        resp["Content-Disposition"] = 'attachment; filename="bills.xlsx"'
        wb.save(resp)
        return resp
    @decorators.action(detail=False, methods=["get"], url_path="tally-xml")
    def export_tally_xml(self, request):
        qs = self.get_queryset()
        root = etree.Element("ENVELOPE")
        body = etree.SubElement(root, "BODY")
        import_data = etree.SubElement(body, "IMPORTDATA")
        reqdesc = etree.SubElement(import_data, "REQUESTDESC")
        reqdata = etree.SubElement(import_data, "REQUESTDATA")
        for b in qs:
            tally_msg = etree.SubElement(reqdata, "TALLYMESSAGE")
            voucher = etree.SubElement(tally_msg, "VOUCHER", VCHTYPE="Sales")
            etree.SubElement(voucher, "DATE").text = "20240101"
            etree.SubElement(voucher, "PARTYNAME").text = f"Patient-{b.patient_id}"
            etree.SubElement(voucher, "AMOUNT").text = str(b.net_cents / 100.0)
        xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        resp = HttpResponse(xml_bytes, content_type="application/xml")
        resp["Content-Disposition"] = 'attachment; filename="tally.xml"'
        return resp
    @decorators.action(detail=False, methods=["get"], url_path="consolidated-pl")
    def consolidated_pl(self, request):
        qs = self.get_queryset().prefetch_related("items")
        revenue = qs.aggregate(total=Sum("net_cents"))["total"] or 0
        from .models import Asset
        user = request.user
        assets = Asset.objects.filter(hospital_id=getattr(user, "hospital_id", None))
        depreciation = sum(a.annual_depreciation_cents() for a in assets)
        total_beds = Bed.objects.filter(
            hospital_id=getattr(user, "hospital_id", None)
        ).count()
        occupied_beds = Bed.objects.filter(
            hospital_id=getattr(user, "hospital_id", None), is_occupied=True
        ).count()
        occupancy_rate = (occupied_beds / total_beds) if total_beds else 0.0
        pl = revenue - depreciation
        return response.Response(
            {
                "revenue_cents": int(revenue),
                "depreciation_cents": int(depreciation),
                "profit_cents": int(pl),
                "beds": total_beds,
                "occupied_beds": occupied_beds,
                "occupancy_rate": occupancy_rate,
            }
        )
    @decorators.action(detail=False, methods=["get"], url_path="referral-income")
    def referral_income(self, request):
        total = (
            self.get_queryset()
            .exclude(referral_source="")
            .aggregate(total=Sum("net_cents"))["total"]
            or 0
        )
        return response.Response({"referral_income_cents": int(total)})
    @decorators.action(detail=False, methods=["get"], url_path="outsourced-breakdown")
    def outsourced_breakdown(self, request):
        qs = self.get_queryset()
        outsourced = (
            BillLineItem.objects.filter(bill__in=qs, is_outsourced=True).aggregate(
                total=Sum("amount_cents")
            )["total"]
            or 0
        )
        inhouse = (
            BillLineItem.objects.filter(bill__in=qs, is_outsourced=False).aggregate(
                total=Sum("amount_cents")
            )["total"]
            or 0
        )
        return response.Response(
            {"outsourced_cents": int(outsourced), "inhouse_cents": int(inhouse)}
        )
class DepartmentBudgetViewSet(TenantScopedViewSet):
    serializer_class = DepartmentBudgetSerializer
    queryset = DepartmentBudget.objects.all()
    required_module = "enable_accounting"
    @decorators.action(detail=False, methods=["get"], url_path="utilization")
    def utilization(self, request):
        period = request.query_params.get("period")
        dept = request.query_params.get("department")
        qs = self.get_queryset()
        if period:
            qs = qs.filter(period=period)
        if dept:
            qs = qs.filter(department=dept)
        budget = qs.aggregate(total=Sum("budget_cents"))["total"] or 0
        items = BillLineItem.objects.all()
        if dept:
            items = items.filter(department=dept)
        if period:
            from django.db.models import F
            from django.db.models.functions import TruncMonth
            items = items.filter(bill__updated_at__startswith=period)
        spend = items.aggregate(total=Sum("amount_cents"))["total"] or 0
        pct = float(spend) / float(budget) * 100.0 if budget else 0.0
        return response.Response(
            {
                "budget_cents": int(budget),
                "spend_cents": int(spend),
                "utilization_pct": pct,
            }
        )