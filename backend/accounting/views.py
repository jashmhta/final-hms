"""
views module
"""

import json
from datetime import timedelta

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Q, Sum
from django.http import HttpResponse
from django.utils import timezone

from users.models import UserRole

from .models import (
    AccountingAuditLog,
    AccountingInvoice,
    AccountingPayment,
    BankAccount,
    BankTransaction,
    BookLock,
    Budget,
    ChartOfAccounts,
    ComplianceDocument,
    CostCenter,
    Currency,
    Customer,
    Expense,
    FinancialYear,
    FixedAsset,
    InsuranceClaim,
    LedgerEntry,
    PayrollEntry,
    PricingTier,
    RecurringInvoice,
    ServicePackage,
    TaxConfiguration,
    TDSEntry,
    Vendor,
    VendorPayout,
)
from .serializers import (
    AccountingAuditLogSerializer,
    AccountingInvoiceSerializer,
    AccountingPaymentSerializer,
    BankAccountSerializer,
    BankReconciliationSerializer,
    BankTransactionSerializer,
    BookLockSerializer,
    BudgetSerializer,
    ChartOfAccountsSerializer,
    ComplianceDocumentSerializer,
    CostCenterSerializer,
    CurrencySerializer,
    CustomerSerializer,
    DashboardSummarySerializer,
    ExpenseSerializer,
    ExportRequestSerializer,
    FinancialYearSerializer,
    FixedAssetSerializer,
    InsuranceClaimSerializer,
    LedgerEntrySerializer,
    PayrollEntrySerializer,
    PricingTierSerializer,
    RecurringInvoiceSerializer,
    ServicePackageSerializer,
    TaxConfigurationSerializer,
    TDSEntrySerializer,
    VendorPayoutSerializer,
    VendorSerializer,
)
from .utils import (
    AgeingReportGenerator,
    BankReconciliationHelper,
    DepreciationCalculator,
    DoubleEntryBookkeeping,
    ExportEngine,
    ReportGenerator,
    TaxCalculator,
)


class HospitalFilterMixin:
    def get_queryset(self):
        return super().get_queryset().filter(hospital=self.request.user.hospital)

    def perform_create(self, serializer):
        serializer.save(hospital=self.request.user.hospital)


class AccountingPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.HOSPITAL_ADMIN,
        ]:
            return True
        if request.user.role == UserRole.BILLING_CLERK:
            allowed_views = ["invoice", "payment", "customer"]
            return view.basename in allowed_views
        if request.user.role == UserRole.DOCTOR:
            return view.action in ["list", "retrieve"] and "report" in view.basename
        return False


class CurrencyViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["is_active", "is_base_currency"]


class TaxConfigurationViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = TaxConfiguration.objects.all()
    serializer_class = TaxConfigurationSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["tax_type", "is_active"]


class ChartOfAccountsViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = ChartOfAccounts.objects.all()
    serializer_class = ChartOfAccountsSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["account_type", "account_subtype", "is_active"]
    search_fields = ["account_code", "account_name"]
    ordering_fields = ["account_code", "account_name"]

    @action(detail=False, methods=["get"])
    def hierarchy(self, request):
        root_accounts = self.get_queryset().filter(parent_account=None)
        serializer = self.get_serializer(root_accounts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def ledger(self, request, pk=None):
        account = self.get_object()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        entries_filter = Q(debit_account=account) | Q(credit_account=account)
        if start_date:
            entries_filter &= Q(transaction_date__gte=start_date)
        if end_date:
            entries_filter &= Q(transaction_date__lte=end_date)
        entries = LedgerEntry.objects.filter(entries_filter).order_by(
            "transaction_date"
        )
        serializer = LedgerEntrySerializer(entries, many=True)
        return Response(
            {
                "account": ChartOfAccountsSerializer(account).data,
                "entries": serializer.data,
                "opening_balance": account.balance,
                "closing_balance": account.balance,
            }
        )


class CostCenterViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer
    permission_classes = [AccountingPermission]
    search_fields = ["code", "name"]

    @action(detail=True, methods=["get"])
    def profitability(self, request, pk=None):
        cost_center = self.get_object()
        start_date = request.query_params.get(
            "start_date", timezone.now().date().replace(day=1)
        )
        end_date = request.query_params.get("end_date", timezone.now().date())
        revenue = (
            AccountingInvoice.objects.filter(
                cost_center=cost_center,
                invoice_date__gte=start_date,
                invoice_date__lte=end_date,
                status__in=["PAID", "PARTIAL"],
            ).aggregate(total=Sum("total_cents"))["total"]
            or 0
        )
        expenses = (
            Expense.objects.filter(
                cost_center=cost_center,
                expense_date__gte=start_date,
                expense_date__lte=end_date,
                is_approved=True,
            ).aggregate(total=Sum("net_amount_cents"))["total"]
            or 0
        )
        profit = revenue - expenses
        margin = (profit / revenue * 100) if revenue > 0 else 0
        return Response(
            {
                "cost_center": self.get_serializer(cost_center).data,
                "period": f"{start_date} to {end_date}",
                "revenue_cents": revenue,
                "expenses_cents": expenses,
                "profit_cents": profit,
                "profit_margin": round(margin, 2),
            }
        )


class ServicePackageViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = ServicePackage.objects.all()
    serializer_class = ServicePackageSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["is_active"]
    search_fields = ["package_code", "name"]


class PricingTierViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = PricingTier.objects.all()
    serializer_class = PricingTierSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["is_active"]
    search_fields = ["tier_code", "name"]


class VendorViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["is_active", "tds_category"]
    search_fields = ["vendor_code", "name", "gstin", "pan"]

    @action(detail=True, methods=["get"])
    def outstanding_payables(self, request, pk=None):
        vendor = self.get_object()
        expenses = Expense.objects.filter(vendor=vendor, is_paid=False)
        serializer = ExpenseSerializer(expenses, many=True)
        total_outstanding = (
            expenses.aggregate(total=Sum("net_amount_cents"))["total"] or 0
        )
        return Response(
            {
                "vendor": VendorSerializer(vendor).data,
                "expenses": serializer.data,
                "total_outstanding_cents": total_outstanding,
            }
        )


class CustomerViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["customer_type", "is_active"]
    search_fields = ["customer_code", "name", "gstin"]


class AccountingInvoiceViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = AccountingInvoice.objects.all()
    serializer_class = AccountingInvoiceSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["invoice_type", "status", "cost_center"]
    search_fields = ["invoice_number"]
    ordering_fields = ["invoice_date", "due_date", "total_cents"]

    def perform_create(self, serializer):
        serializer.save(
            hospital=self.request.user.hospital, created_by=self.request.user
        )

    @action(detail=True, methods=["post"])
    def send_invoice(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status == "DRAFT":
            invoice.status = "SENT"
            invoice.save()
            DoubleEntryBookkeeping.post_invoice_entries(invoice)
            return Response({"status": "Invoice sent successfully"})
        return Response(
            {"error": "Invoice cannot be sent in current status"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def cancel_invoice(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status in ["DRAFT", "SENT"]:
            invoice.status = "CANCELLED"
            invoice.save()
            return Response({"status": "Invoice cancelled successfully"})
        return Response(
            {"error": "Invoice cannot be cancelled in current status"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        overdue_invoices = self.get_queryset().filter(
            status="OVERDUE", balance_cents__gt=0
        )
        serializer = self.get_serializer(overdue_invoices, many=True)
        return Response(serializer.data)


class AccountingPaymentViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = AccountingPayment.objects.all()
    serializer_class = AccountingPaymentSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["payment_method", "status"]
    search_fields = ["payment_number", "reference_number"]

    def perform_create(self, serializer):
        serializer.save(
            hospital=self.request.user.hospital, received_by=self.request.user
        )


class ExpenseViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["category", "is_approved", "is_paid", "cost_center"]
    search_fields = ["expense_number", "description"]

    def perform_create(self, serializer):
        serializer.save(
            hospital=self.request.user.hospital, created_by=self.request.user
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        expense = self.get_object()
        if not expense.is_approved:
            expense.is_approved = True
            expense.approved_by = request.user
            expense.save()
            return Response({"status": "Expense approved successfully"})
        return Response(
            {"error": "Expense already approved"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["get"])
    def pending_approval(self, request):
        pending_expenses = self.get_queryset().filter(is_approved=False)
        serializer = self.get_serializer(pending_expenses, many=True)
        return Response(serializer.data)


class PayrollEntryViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = PayrollEntry.objects.all()
    serializer_class = PayrollEntrySerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["status", "cost_center"]
    search_fields = ["employee__first_name", "employee__last_name"]

    def perform_create(self, serializer):
        serializer.save(
            hospital=self.request.user.hospital, created_by=self.request.user
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        payroll = self.get_object()
        if payroll.status == "DRAFT":
            payroll.status = "APPROVED"
            payroll.approved_by = request.user
            payroll.save()
            return Response({"status": "Payroll approved successfully"})
        return Response(
            {"error": "Payroll cannot be approved in current status"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["get"])
    def salary_slip(self, request, pk=None):
        payroll = self.get_object()
        salary_slip_data = {
            "employee": payroll.employee.get_full_name(),
            "employee_id": payroll.employee.username,
            "pay_period": f"{payroll.pay_period_start} to " f"{payroll.pay_period_end}",
            "pay_date": payroll.pay_date,
            "earnings": {
                "basic_salary": payroll.basic_salary_cents / 100,
                "hra": payroll.hra_cents / 100,
                "medical_allowance": payroll.medical_allowance_cents / 100,
                "transport_allowance": payroll.transport_allowance_cents / 100,
                "other_allowances": payroll.other_allowances_cents / 100,
                "overtime": (payroll.overtime_hours * payroll.overtime_rate_cents)
                / 100,
                "bonus": payroll.bonus_cents / 100,
                "incentive": payroll.incentive_cents / 100,
            },
            "deductions": {
                "pf_employee": payroll.pf_employee_cents / 100,
                "esi_employee": payroll.esi_employee_cents / 100,
                "professional_tax": payroll.professional_tax_cents / 100,
                "tds": payroll.tds_cents / 100,
                "advance_deduction": payroll.advance_deduction_cents / 100,
                "other_deductions": payroll.other_deductions_cents / 100,
            },
            "totals": {
                "gross_salary": payroll.gross_salary_cents / 100,
                "total_deductions": payroll.total_deductions_cents / 100,
                "net_salary": payroll.net_salary_cents / 100,
            },
        }
        return Response(salary_slip_data)


class FixedAssetViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = FixedAsset.objects.all()
    serializer_class = FixedAssetSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["category", "cost_center", "is_active"]
    search_fields = ["asset_code", "name"]

    def perform_create(self, serializer):
        asset = serializer.save(hospital=self.request.user.hospital)
        asset.current_book_value_cents = asset.purchase_cost_cents
        asset.save()

    @action(detail=True, methods=["get"])
    def depreciation_schedule(self, request, pk=None):
        asset = self.get_object()
        schedule = DepreciationCalculator.generate_depreciation_schedule(asset)
        return Response(schedule)

    @action(detail=True, methods=["post"])
    def dispose(self, request, pk=None):
        asset = self.get_object()
        disposal_data = request.data
        asset.disposal_date = disposal_data.get("disposal_date")
        asset.disposal_amount_cents = disposal_data.get("disposal_amount_cents", 0)
        asset.disposal_method = disposal_data.get("disposal_method", "")
        asset.is_active = False
        asset.save()
        return Response({"status": "Asset disposed successfully"})


class BankAccountViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["account_type", "is_active"]
    search_fields = ["account_name", "account_number"]


class BankTransactionViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = BankTransaction.objects.all()
    serializer_class = BankTransactionSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["bank_account", "transaction_type", "is_reconciled"]

    @action(detail=False, methods=["post"])
    def auto_reconcile(self, request):
        serializer = BankReconciliationSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            bank_account = serializer.validated_data["bank_account"]
            tolerance = serializer.validated_data["tolerance_cents"]
            matched_count = BankReconciliationHelper.auto_match_transactions(
                bank_account, tolerance
            )
            return Response(
                {
                    "status": "Auto reconciliation completed",
                    "matched_transactions": matched_count,
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def manual_reconcile(self, request, pk=None):
        bank_txn = self.get_object()
        reconcile_data = request.data
        if reconcile_data.get("payment_id"):
            payment = AccountingPayment.objects.get(id=reconcile_data["payment_id"])
            bank_txn.reconciled_payment = payment
        elif reconcile_data.get("expense_id"):
            expense = Expense.objects.get(id=reconcile_data["expense_id"])
            bank_txn.reconciled_expense = expense
        bank_txn.is_reconciled = True
        bank_txn.reconciled_by = request.user
        bank_txn.reconciled_at = timezone.now()
        bank_txn.save()
        return Response({"status": "Transaction reconciled successfully"})


class InsuranceClaimViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = InsuranceClaim.objects.all()
    serializer_class = InsuranceClaimSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["status", "insurance_company"]
    search_fields = ["claim_number", "policy_number"]

    @action(detail=True, methods=["post"])
    def submit_claim(self, request, pk=None):
        claim = self.get_object()
        if claim.status == "DRAFT":
            claim.status = "SUBMITTED"
            claim.submission_date = timezone.now().date()
            claim.save()
            return Response({"status": "Claim submitted successfully"})
        return Response(
            {"error": "Claim cannot be submitted in current status"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["get"])
    def pending_claims(self, request):
        pending_claims = self.get_queryset().filter(
            status__in=["SUBMITTED", "UNDER_REVIEW"]
        )
        serializer = self.get_serializer(pending_claims, many=True)
        total_pending = (
            pending_claims.aggregate(total=Sum("claim_amount_cents"))["total"] or 0
        )
        return Response(
            {
                "claims": serializer.data,
                "total_pending_cents": total_pending,
                "count": pending_claims.count(),
            }
        )


class TDSEntryViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = TDSEntry.objects.all()
    serializer_class = TDSEntrySerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["section"]

    def perform_create(self, serializer):
        serializer.save(
            hospital=self.request.user.hospital, created_by=self.request.user
        )


class BookLockViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = BookLock.objects.all()
    serializer_class = BookLockSerializer
    permission_classes = [AccountingPermission]

    def perform_create(self, serializer):
        serializer.save(
            hospital=self.request.user.hospital, locked_by=self.request.user
        )


class ReportsAPIView(APIView):
    permission_classes = [AccountingPermission]

    def get(self, request):
        reports = [
            {"name": "trial_balance", "title": "Trial Balance"},
            {"name": "profit_loss", "title": "Profit & Loss Statement"},
            {"name": "balance_sheet", "title": "Balance Sheet"},
            {"name": "cash_flow", "title": "Cash Flow Statement"},
            {"name": "aging_report", "title": "Aging Report"},
            {
                "name": "department_profitability",
                "title": "Department Profitability",
            },
            {
                "name": "asset_depreciation",
                "title": "Asset Depreciation Report",
            },
        ]
        return Response(reports)

    def post(self, request):
        report_type = request.data.get("report_type")
        hospital = request.user.hospital
        if report_type == "trial_balance":
            as_of_date = request.data.get("as_of_date", timezone.now().date())
            report_data = ReportGenerator.generate_trial_balance(hospital, as_of_date)
            return Response(report_data)
        elif report_type == "profit_loss":
            start_date = request.data.get("start_date")
            end_date = request.data.get("end_date")
            if not start_date or not end_date:
                return Response(
                    {"error": "start_date and end_date are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            report_data = ReportGenerator.generate_profit_loss(
                hospital, start_date, end_date
            )
            return Response(report_data)
        elif report_type == "balance_sheet":
            as_of_date = request.data.get("as_of_date", timezone.now().date())
            report_data = ReportGenerator.generate_balance_sheet(hospital, as_of_date)
            return Response(report_data)
        elif report_type == "aging_report":
            as_of_date = request.data.get("as_of_date", timezone.now().date())
            report_data = AgeingReportGenerator.generate_receivables_ageing(
                hospital, as_of_date
            )
            return Response(report_data)
        else:
            return Response(
                {"error": "Invalid report type"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DashboardAPIView(APIView):
    permission_classes = [AccountingPermission]

    def get(self, request):
        hospital = request.user.hospital
        current_month_start = timezone.now().date().replace(day=1)
        current_date = timezone.now().date()
        total_revenue = (
            AccountingInvoice.objects.filter(
                hospital=hospital,
                invoice_date__gte=current_month_start,
                invoice_date__lte=current_date,
                status__in=["PAID", "PARTIAL"],
            ).aggregate(total=Sum("total_cents"))["total"]
            or 0
        )
        total_expenses = (
            Expense.objects.filter(
                hospital=hospital,
                expense_date__gte=current_month_start,
                expense_date__lte=current_date,
                is_approved=True,
            ).aggregate(total=Sum("net_amount_cents"))["total"]
            or 0
        )
        outstanding_receivables = (
            AccountingInvoice.objects.filter(
                hospital=hospital,
                status__in=["SENT", "OVERDUE", "PARTIAL"],
                balance_cents__gt=0,
            ).aggregate(total=Sum("balance_cents"))["total"]
            or 0
        )
        outstanding_payables = (
            Expense.objects.filter(hospital=hospital, is_paid=False).aggregate(
                total=Sum("net_amount_cents")
            )["total"]
            or 0
        )
        cash_balance = (
            BankAccount.objects.filter(hospital=hospital, is_active=True).aggregate(
                total=Sum("current_balance_cents")
            )["total"]
            or 0
        )
        overdue_invoices_count = AccountingInvoice.objects.filter(
            hospital=hospital, status="OVERDUE"
        ).count()
        pending_expense_approvals_count = Expense.objects.filter(
            hospital=hospital, is_approved=False
        ).count()
        unreconciled_transactions_count = BankTransaction.objects.filter(
            bank_account__hospital=hospital, is_reconciled=False
        ).count()
        expiring_documents_count = ComplianceDocument.objects.filter(
            hospital=hospital,
            is_active=True,
            expiry_date__lte=current_date + timedelta(days=30),
            expiry_date__gte=current_date,
        ).count()
        dashboard_data = {
            "total_revenue_cents": total_revenue,
            "total_expenses_cents": total_expenses,
            "net_profit_cents": total_revenue - total_expenses,
            "outstanding_receivables_cents": outstanding_receivables,
            "outstanding_payables_cents": outstanding_payables,
            "cash_balance_cents": cash_balance,
            "overdue_invoices_count": overdue_invoices_count,
            "pending_expense_approvals_count": pending_expense_approvals_count,
            "unreconciled_transactions_count": unreconciled_transactions_count,
            "expiring_documents_count": expiring_documents_count,
        }
        serializer = DashboardSummarySerializer(dashboard_data)
        return Response(serializer.data)


class ExportAPIView(APIView):
    permission_classes = [AccountingPermission]

    def post(self, request):
        serializer = ExportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        hospital = request.user.hospital
        try:
            if data["report_type"] == "TRIAL_BALANCE":
                report_data = ReportGenerator.generate_trial_balance(
                    hospital, data["as_of_date"]
                )
                filename = f"trial_balance_{data['as_of_date']}"
            elif data["report_type"] == "PROFIT_LOSS":
                report_data = ReportGenerator.generate_profit_loss(
                    hospital, data["start_date"], data["end_date"]
                )
                filename = f"profit_loss_{data['start_date']}_to_{data['end_date']}"
            elif data["report_type"] == "BALANCE_SHEET":
                report_data = ReportGenerator.generate_balance_sheet(
                    hospital, data["as_of_date"]
                )
                filename = f"balance_sheet_{data['as_of_date']}"
            elif data["report_type"] == "INVOICES":
                invoices = AccountingInvoice.objects.filter(
                    hospital=hospital,
                    invoice_date__gte=data["start_date"],
                    invoice_date__lte=data["end_date"],
                )
                report_data = AccountingInvoiceSerializer(invoices, many=True).data
                filename = f"invoices_{data['start_date']}_to_{data['end_date']}"
            elif data["report_type"] == "GST_RETURN":
                report_data = ExportEngine.export_gst_returns(
                    hospital, data["start_date"], data["end_date"], "GSTR1"
                )
                filename = f"gst_return_{data['start_date']}_to_{data['end_date']}"
            else:
                return Response(
                    {"error": "Report type not implemented"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if data["export_format"] == "JSON":
                response = HttpResponse(
                    json.dumps(report_data, indent=2, default=str),
                    content_type="application/json",
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="{filename}.json"'
                )
            elif data["export_format"] == "EXCEL":
                if isinstance(report_data, list):
                    headers = list(report_data[0].keys()) if report_data else []
                    rows = [list(row.values()) for row in report_data]
                else:
                    headers = ["Field", "Value"]
                    rows = [
                        [k, v]
                        for k, v in report_data.items()
                        if not isinstance(v, (dict, list))
                    ]
                excel_buffer = ExportEngine.export_to_excel(rows, headers, filename)
                response = HttpResponse(
                    excel_buffer.getvalue(),
                    content_type=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet",
                    ),
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="{filename}.xlsx"'
                )
            elif data["export_format"] == "TALLY_XML":
                xml_data = ExportEngine.export_to_tally_xml(report_data, "SALES")
                response = HttpResponse(xml_data, content_type="application/xml")
                response["Content-Disposition"] = (
                    f'attachment; filename="{filename}.xml"'
                )
            else:
                return Response(
                    {"error": "Export format not supported"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return response
        except Exception as e:
            return Response(
                {"error": f"Export failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DepreciationProcessingAPIView(APIView):
    permission_classes = [AccountingPermission]

    def post(self, request):
        hospital = request.user.hospital
        processing_date = request.data.get("processing_date", timezone.now().date())
        try:
            processed_count = DepreciationCalculator.process_monthly_depreciation(
                hospital,
                processing_date,
            )
            return Response(
                {
                    "status": "Depreciation processed successfully",
                    "assets_processed": processed_count,
                    "processing_date": processing_date,
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Depreciation processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TaxLiabilityAPIView(APIView):
    permission_classes = [AccountingPermission]

    def post(self, request):
        hospital = request.user.hospital
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        tax_type = request.data.get("tax_type", "GST")
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            liability_data = TaxCalculator.get_tax_liability_for_period(
                hospital, start_date, end_date, tax_type
            )
            return Response(liability_data)
        except Exception as e:
            return Response(
                {"error": f"Tax calculation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VendorPayoutViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = VendorPayout.objects.all()
    serializer_class = VendorPayoutSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["vendor", "status"]

    def perform_create(self, serializer):
        serializer.save(
            hospital=self.request.user.hospital, created_by=self.request.user
        )


class RecurringInvoiceViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = RecurringInvoice.objects.all()
    serializer_class = RecurringInvoiceSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["frequency", "is_active"]

    def perform_create(self, serializer):
        serializer.save(
            hospital=self.request.user.hospital, created_by=self.request.user
        )


class ComplianceDocumentViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = ComplianceDocument.objects.all()
    serializer_class = ComplianceDocumentSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["document_type", "is_active"]

    @action(detail=False, methods=["get"])
    def expiring_soon(self, request):
        expiring_docs = self.get_queryset().filter(
            expiry_date__lte=timezone.now().date() + timedelta(days=30),
            expiry_date__gte=timezone.now().date(),
            is_active=True,
        )
        serializer = self.get_serializer(expiring_docs, many=True)
        return Response(serializer.data)


class FinancialYearViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = FinancialYear.objects.all()
    serializer_class = FinancialYearSerializer
    permission_classes = [AccountingPermission]

    @action(detail=False, methods=["get"])
    def current(self, request):
        current_fy = self.get_queryset().filter(is_current=True).first()
        if current_fy:
            serializer = self.get_serializer(current_fy)
            return Response(serializer.data)
        return Response(
            {"error": "No current financial year configured"},
            status=status.HTTP_404_NOT_FOUND,
        )


class BudgetViewSet(HospitalFilterMixin, viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["financial_year", "cost_center"]

    def perform_create(self, serializer):
        serializer.save(
            hospital=self.request.user.hospital, created_by=self.request.user
        )

    @action(detail=False, methods=["post"])
    def update_actuals(self, request):
        financial_year = request.data.get("financial_year")
        if not financial_year:
            return Response(
                {"error": "financial_year is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        budgets = self.get_queryset().filter(financial_year=financial_year)
        updated_count = 0
        for budget in budgets:
            actual_amount = (
                LedgerEntry.objects.filter(
                    hospital=request.user.hospital,
                    transaction_date__gte=budget.financial_year.start_date,
                    transaction_date__lte=budget.financial_year.end_date,
                )
                .filter(
                    Q(debit_account=budget.account) | Q(credit_account=budget.account)
                )
                .aggregate(total=Sum("amount_cents"))["total"]
                or 0
            )
            budget.actual_amount_cents = actual_amount
            budget.calculate_variance()
            updated_count += 1
        return Response(
            {
                "status": "Budget actuals updated successfully",
                "updated_count": updated_count,
            }
        )


class LedgerEntryViewSet(HospitalFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = LedgerEntry.objects.all()
    serializer_class = LedgerEntrySerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["transaction_date", "debit_account", "credit_account"]
    search_fields = ["description", "reference_number"]
    ordering_fields = ["transaction_date"]


class AccountingAuditLogViewSet(HospitalFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AccountingAuditLog.objects.all()
    serializer_class = AccountingAuditLogSerializer
    permission_classes = [AccountingPermission]
    filterset_fields = ["user", "action_type", "table_name"]
    ordering_fields = ["timestamp"]
