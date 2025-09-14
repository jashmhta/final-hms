"""
DRF Serializers for the accounting module.
"""

<<<<<<< HEAD
from decimal import Decimal
=======
from django.utils import timezone
from rest_framework import serializers
>>>>>>> transform-refactor

from django.utils import timezone
from rest_framework import serializers

from .models import (
    AccountingAuditLog,
    AccountingInvoice,
    AccountingPayment,
<<<<<<< HEAD
    AccountingPeriod,
=======
>>>>>>> transform-refactor
    BankAccount,
    BankTransaction,
    BookLock,
    Budget,
    ChartOfAccounts,
    ComplianceDocument,
    CostCenter,
    Currency,
    Customer,
    DepreciationSchedule,
    Expense,
<<<<<<< HEAD
    ExportLog,
    FinancialYear,
    FixedAsset,
    ImportBatch,
=======
    FinancialYear,
    FixedAsset,
>>>>>>> transform-refactor
    InsuranceClaim,
    InvoiceLineItem,
    LedgerEntry,
    PayrollEntry,
    PricingTier,
<<<<<<< HEAD
    ProviderCommissionStructure,
=======
>>>>>>> transform-refactor
    RecurringInvoice,
    ReportSchedule,
    ServicePackage,
    ServicePackageItem,
    TaxConfiguration,
    TaxLiability,
    TDSEntry,
    Vendor,
    VendorPayout,
    VendorPayoutItem,
)


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")

    def validate(self, data):
        # Ensure only one base currency per hospital
        if data.get("is_base_currency") and self.instance is None:
            existing_base = Currency.objects.filter(
<<<<<<< HEAD
                hospital=self.context["request"].user.hospital, is_base_currency=True
=======
                hospital=self.context["request"].user.hospital,
                is_base_currency=True,
>>>>>>> transform-refactor
            ).exists()
            if existing_base:
                raise serializers.ValidationError(
                    "Only one base currency allowed per hospital"
                )
        return data


class TaxConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxConfiguration
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")


class ChartOfAccountsSerializer(serializers.ModelSerializer):
    balance = serializers.ReadOnlyField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = ChartOfAccounts
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")

    def get_children(self, obj):
        if obj.children.exists():
            return ChartOfAccountsSerializer(
                obj.children.all(), many=True, context=self.context
            ).data
        return []


class CostCenterSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source="manager.get_full_name", read_only=True)
<<<<<<< HEAD
=======
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor

    class Meta:
        model = CostCenter
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")


class VendorSerializer(serializers.ModelSerializer):
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")

    def get_outstanding_balance(self, obj):
        # Calculate outstanding payables
        from django.db.models import Sum

        total_expenses = (
            Expense.objects.filter(vendor=obj, is_paid=False).aggregate(
                total=Sum("net_amount_cents")
            )["total"]
            or 0
        )
        return total_expenses


class CustomerSerializer(serializers.ModelSerializer):
    outstanding_receivables = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")

    def get_outstanding_receivables(self, obj):
        from django.db.models import Sum

        total_receivables = (
            AccountingInvoice.objects.filter(
                customer=obj, status__in=["SENT", "OVERDUE", "PARTIAL"]
            ).aggregate(total=Sum("balance_cents"))["total"]
            or 0
        )
        return total_receivables


class ServicePackageItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = ServicePackageItem
        fields = "__all__"


class ServicePackageSerializer(serializers.ModelSerializer):
    items = ServicePackageItemSerializer(many=True, read_only=True)
    profit_margin = serializers.SerializerMethodField()

    class Meta:
        model = ServicePackage
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")

    def get_profit_margin(self, obj):
        if obj.cost_price_cents > 0:
            margin = (
<<<<<<< HEAD
                (obj.base_price_cents - obj.cost_price_cents) / obj.base_price_cents
=======
                (obj.base_price_cents - obj.cost_price_cents)
                / obj.base_price_cents
                # noqa: E501
>>>>>>> transform-refactor
            ) * 100
            return round(margin, 2)
        return 0.0


class PricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingTier
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    package_name = serializers.CharField(source="package.name", read_only=True)
    profit_margin = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceLineItem
        fields = "__all__"

    def get_profit_margin(self, obj):
        if obj.cost_price_cents > 0 and obj.unit_price_cents > 0:
            margin = (
<<<<<<< HEAD
                (obj.unit_price_cents - obj.cost_price_cents) / obj.unit_price_cents
=======
                (obj.unit_price_cents - obj.cost_price_cents)
                / obj.unit_price_cents
                # noqa: E501
>>>>>>> transform-refactor
            ) * 100
            return round(margin, 2)
        return 0.0


class AccountingInvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceLineItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
<<<<<<< HEAD
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    cost_center_name = serializers.CharField(source="cost_center.name", read_only=True)
    currency_symbol = serializers.CharField(source="currency.symbol", read_only=True)
=======
    # noqa: E501
    # noqa: E501
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    # noqa: E501
    # noqa: E501
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    cost_center_name = serializers.CharField(source="cost_center.name", read_only=True)
    # noqa: E501
    # noqa: E501
    currency_symbol = serializers.CharField(source="currency.symbol", read_only=True)
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor
    days_overdue = serializers.SerializerMethodField()

    class Meta:
        model = AccountingInvoice
        fields = "__all__"
        read_only_fields = (
            "hospital",
            "created_at",
            "updated_at",
            "invoice_number",
            "subtotal_cents",
            "tax_cents",
            "total_cents",
            "balance_cents",
        )

    def get_days_overdue(self, obj):
        if obj.status == "OVERDUE":
            return (timezone.now().date() - obj.due_date).days
        return 0

    def validate(self, data):
        # Validate split billing percentages
        total_percentage = (
            data.get("insurance_percentage", 0)
            + data.get("employer_percentage", 0)
            + data.get("patient_percentage", 100)
        )
        if total_percentage != 100:
            raise serializers.ValidationError(
                "Split billing percentages must total 100%"
            )
        return data


class AccountingPaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(
        source="invoice.invoice_number", read_only=True
    )
    received_by_name = serializers.CharField(
        source="received_by.get_full_name", read_only=True
    )
    bank_account_name = serializers.CharField(
        source="bank_account.account_name", read_only=True
    )
    currency_symbol = serializers.CharField(source="currency.symbol", read_only=True)
<<<<<<< HEAD
=======
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor

    class Meta:
        model = AccountingPayment
        fields = "__all__"
<<<<<<< HEAD
        read_only_fields = ("hospital", "created_at", "updated_at", "payment_number")
=======
        read_only_fields = (
            "hospital",
            "created_at",
            "updated_at",
            "payment_number",
        )
>>>>>>> transform-refactor


class ExpenseSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    cost_center_name = serializers.CharField(source="cost_center.name", read_only=True)
<<<<<<< HEAD
=======
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    approved_by_name = serializers.CharField(
        source="approved_by.get_full_name", read_only=True
    )
    currency_symbol = serializers.CharField(source="currency.symbol", read_only=True)
<<<<<<< HEAD
=======
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor

    class Meta:
        model = Expense
        fields = "__all__"
        read_only_fields = (
            "hospital",
            "created_at",
            "updated_at",
            "expense_number",
            "net_amount_cents",
        )


class BankAccountSerializer(serializers.ModelSerializer):
    currency_symbol = serializers.CharField(source="currency.symbol", read_only=True)
<<<<<<< HEAD
=======
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor
    unreconciled_count = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = "__all__"
        read_only_fields = (
            "hospital",
            "created_at",
            "updated_at",
            "current_balance_cents",
        )

    def get_unreconciled_count(self, obj):
        return obj.transactions.filter(is_reconciled=False).count()


class BankTransactionSerializer(serializers.ModelSerializer):
    bank_account_name = serializers.CharField(
        source="bank_account.account_name", read_only=True
    )
    reconciled_payment_number = serializers.CharField(
        source="reconciled_payment.payment_number", read_only=True
    )
    reconciled_expense_number = serializers.CharField(
        source="reconciled_expense.expense_number", read_only=True
    )

    class Meta:
        model = BankTransaction
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")


class FixedAssetSerializer(serializers.ModelSerializer):
    cost_center_name = serializers.CharField(source="cost_center.name", read_only=True)
<<<<<<< HEAD
=======
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    annual_depreciation = serializers.SerializerMethodField()
    remaining_life = serializers.SerializerMethodField()

    class Meta:
        model = FixedAsset
        fields = "__all__"
        read_only_fields = (
            "hospital",
            "created_at",
            "updated_at",
            "current_book_value_cents",
            "accumulated_depreciation_cents",
        )

    def get_annual_depreciation(self, obj):
        return obj.calculate_annual_depreciation()

    def get_remaining_life(self, obj):
        years_passed = (timezone.now().date() - obj.purchase_date).days / 365.25
        # noqa: E501
        # noqa: E501
        return max(0, obj.useful_life_years - years_passed)


class DepreciationScheduleSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    asset_code = serializers.CharField(source="asset.asset_code", read_only=True)
<<<<<<< HEAD
=======
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor

    class Meta:
        model = DepreciationSchedule
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")


class PayrollEntrySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.get_full_name", read_only=True
    )
    cost_center_name = serializers.CharField(source="cost_center.name", read_only=True)
<<<<<<< HEAD
=======
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    approved_by_name = serializers.CharField(
        source="approved_by.get_full_name", read_only=True
    )

    class Meta:
        model = PayrollEntry
        fields = "__all__"
        read_only_fields = (
            "hospital",
            "created_at",
            "updated_at",
            "gross_salary_cents",
            "total_deductions_cents",
            "net_salary_cents",
            "employer_cost_cents",
        )


class InsuranceClaimSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(
        source="invoice.invoice_number", read_only=True
    )
    insurance_company_name = serializers.CharField(
        source="insurance_company.name", read_only=True
    )
    patient_name = serializers.CharField(
        source="invoice.patient.get_full_name", read_only=True
    )
    claim_age_days = serializers.SerializerMethodField()

    class Meta:
        model = InsuranceClaim
        fields = "__all__"
<<<<<<< HEAD
        read_only_fields = ("hospital", "created_at", "updated_at", "claim_number")
=======
        read_only_fields = (
            "hospital",
            "created_at",
            "updated_at",
            "claim_number",
        )
>>>>>>> transform-refactor

    def get_claim_age_days(self, obj):
        if obj.submission_date:
            return (timezone.now().date() - obj.submission_date).days
        return 0


class TDSEntrySerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    employee_name = serializers.CharField(
        source="employee.get_full_name", read_only=True
    )
    expense_number = serializers.CharField(
        source="expense.expense_number", read_only=True
    )

    class Meta:
        model = TDSEntry
        fields = "__all__"
<<<<<<< HEAD
        read_only_fields = ("hospital", "created_at", "updated_at", "tds_entry_number")
=======
        read_only_fields = (
            "hospital",
            "created_at",
            "updated_at",
            "tds_entry_number",
        )
>>>>>>> transform-refactor


class BookLockSerializer(serializers.ModelSerializer):
    locked_by_name = serializers.CharField(
        source="locked_by.get_full_name", read_only=True
    )

    class Meta:
        model = BookLock
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")


class VendorPayoutSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = VendorPayout
        fields = "__all__"
        read_only_fields = (
            "hospital",
            "created_at",
            "updated_at",
            "payout_number",
            "commission_cents",
            "gross_payout_cents",
            "net_payout_cents",
        )

    def get_items(self, obj):
        return VendorPayoutItemSerializer(
            obj.items.all(), many=True, context=self.context
        ).data


class VendorPayoutItemSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
<<<<<<< HEAD
=======
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor
    service_name = serializers.CharField(
        source="invoice_line_item.description", read_only=True
    )

    class Meta:
        model = VendorPayoutItem
        fields = "__all__"


class LedgerEntrySerializer(serializers.ModelSerializer):
    debit_account_name = serializers.CharField(
        source="debit_account.account_name", read_only=True
    )
    credit_account_name = serializers.CharField(
        source="credit_account.account_name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    amount_currency = serializers.ReadOnlyField()

    class Meta:
        model = LedgerEntry
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at", "entry_id")


class FinancialYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialYear
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")

    def validate(self, data):
        if data.get("start_date") and data.get("end_date"):
            if data["start_date"] >= data["end_date"]:
                raise serializers.ValidationError("Start date must be before end date")
        # noqa: E501
        # noqa: E501
        return data


class BudgetSerializer(serializers.ModelSerializer):
    financial_year_name = serializers.CharField(
        source="financial_year.name", read_only=True
    )
    cost_center_name = serializers.CharField(source="cost_center.name", read_only=True)
<<<<<<< HEAD
    account_name = serializers.CharField(source="account.account_name", read_only=True)
=======
    # noqa: E501
    # noqa: E501
    account_name = serializers.CharField(source="account.account_name", read_only=True)
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor

    class Meta:
        model = Budget
        fields = "__all__"
        read_only_fields = (
            "hospital",
            "created_at",
            "updated_at",
            "variance_cents",
            "variance_percentage",
        )


class ComplianceDocumentSerializer(serializers.ModelSerializer):
    is_expiring_soon = serializers.ReadOnlyField()
    days_to_expiry = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceDocument
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")

    def get_days_to_expiry(self, obj):
        if obj.expiry_date:
            return (obj.expiry_date - timezone.now().date()).days
        return None


# Report Serializers


class TrialBalanceSerializer(serializers.Serializer):
    """Serializer for trial balance report"""

    account_code = serializers.CharField()
    account_name = serializers.CharField()
    account_type = serializers.CharField()
    debit_balance_cents = serializers.IntegerField()
    credit_balance_cents = serializers.IntegerField()


class ProfitLossSerializer(serializers.Serializer):
    """Serializer for P&L report"""

    period = serializers.CharField()
    income = serializers.ListField(child=serializers.DictField())
    expenses = serializers.ListField(child=serializers.DictField())
    total_income_cents = serializers.IntegerField()
    total_expenses_cents = serializers.IntegerField()
    net_profit_cents = serializers.IntegerField()


class BalanceSheetSerializer(serializers.Serializer):
    """Serializer for balance sheet report"""

    as_of_date = serializers.DateField()
    assets = serializers.DictField()
    liabilities = serializers.DictField()
    equity = serializers.DictField()


class AgeingReportSerializer(serializers.Serializer):
    """Serializer for ageing reports"""

    as_of_date = serializers.DateField()
    ageing_buckets = serializers.DictField()
    bucket_totals = serializers.DictField()
    grand_total = serializers.IntegerField()


class DepartmentProfitabilitySerializer(serializers.Serializer):
    """Serializer for department profitability report"""

    cost_center_code = serializers.CharField()
    cost_center_name = serializers.CharField()
    revenue_cents = serializers.IntegerField()
    expenses_cents = serializers.IntegerField()
    profit_cents = serializers.IntegerField()
    profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2)


# Bulk operation serializers


class BulkInvoiceCreateSerializer(serializers.Serializer):
    """Serializer for bulk invoice creation"""

    invoices = AccountingInvoiceSerializer(many=True)

    def create(self, validated_data):
        invoices_data = validated_data["invoices"]
        created_invoices = []

        for invoice_data in invoices_data:
            invoice = AccountingInvoice.objects.create(**invoice_data)
            created_invoices.append(invoice)

        return {"invoices": created_invoices}


class BankReconciliationSerializer(serializers.Serializer):
    """Serializer for bank reconciliation operations"""

    bank_account = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all()
    )
    tolerance_cents = serializers.IntegerField(default=100, min_value=0)

    def validate(self, data):
        # Ensure user has access to this bank account
        user = self.context["request"].user
        if data["bank_account"].hospital != user.hospital:
            raise serializers.ValidationError("Access denied to this bank account")
        # noqa: E501
        # noqa: E501
        return data


class ExportRequestSerializer(serializers.Serializer):
    """Serializer for export requests"""

    EXPORT_FORMATS = [
        ("EXCEL", "Excel"),
        ("CSV", "CSV"),
        ("TALLY_XML", "Tally XML"),
        ("GST_JSON", "GST JSON"),
        ("ITR_EXCEL", "ITR Excel"),
    ]

    REPORT_TYPES = [
        ("TRIAL_BALANCE", "Trial Balance"),
        ("PROFIT_LOSS", "Profit & Loss"),
        ("BALANCE_SHEET", "Balance Sheet"),
        ("INVOICES", "Invoices"),
        ("PAYMENTS", "Payments"),
        ("EXPENSES", "Expenses"),
        ("PAYROLL", "Payroll"),
        ("ASSETS", "Assets"),
        ("AGING_REPORT", "Aging Report"),
        ("GST_RETURN", "GST Return"),
        ("TDS_RETURN", "TDS Return"),
    ]

    export_format = serializers.ChoiceField(choices=EXPORT_FORMATS)
    report_type = serializers.ChoiceField(choices=REPORT_TYPES)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    as_of_date = serializers.DateField(required=False)
    cost_center = serializers.PrimaryKeyRelatedField(
        queryset=CostCenter.objects.all(), required=False
    )

    def validate(self, data):
        # Validate date ranges
        if data.get("start_date") and data.get("end_date"):
            if data["start_date"] > data["end_date"]:
                raise serializers.ValidationError("Start date cannot be after end date")
<<<<<<< HEAD
=======
        # noqa: E501
        # noqa: E501
>>>>>>> transform-refactor

        # Some reports require date ranges
        period_required_reports = [
            "PROFIT_LOSS",
            "INVOICES",
            "PAYMENTS",
            "EXPENSES",
            "GST_RETURN",
        ]
        if data["report_type"] in period_required_reports:
            if not (data.get("start_date") and data.get("end_date")):
                raise serializers.ValidationError(
                    f"{data['report_type']} requires start_date and end_date"
                )

        # Some reports require as_of_date
<<<<<<< HEAD
        snapshot_required_reports = ["TRIAL_BALANCE", "BALANCE_SHEET", "AGING_REPORT"]
=======
        snapshot_required_reports = [
            "TRIAL_BALANCE",
            "BALANCE_SHEET",
            "AGING_REPORT",
        ]
>>>>>>> transform-refactor
        if data["report_type"] in snapshot_required_reports:
            if not data.get("as_of_date"):
                raise serializers.ValidationError(
                    f"{data['report_type']} requires as_of_date"
                )

        return data


# Dashboard serializers


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for accounting dashboard summary"""

    total_revenue_cents = serializers.IntegerField()
    total_expenses_cents = serializers.IntegerField()
    net_profit_cents = serializers.IntegerField()
    outstanding_receivables_cents = serializers.IntegerField()
    outstanding_payables_cents = serializers.IntegerField()
    cash_balance_cents = serializers.IntegerField()
    overdue_invoices_count = serializers.IntegerField()
    pending_expense_approvals_count = serializers.IntegerField()
    unreconciled_transactions_count = serializers.IntegerField()
    expiring_documents_count = serializers.IntegerField()


class CashFlowSerializer(serializers.Serializer):
    """Serializer for cash flow data"""

    period = serializers.CharField()
    opening_balance_cents = serializers.IntegerField()
    cash_inflow_cents = serializers.IntegerField()
    cash_outflow_cents = serializers.IntegerField()
    closing_balance_cents = serializers.IntegerField()
    inflow_details = serializers.ListField(child=serializers.DictField())
    outflow_details = serializers.ListField(child=serializers.DictField())


class ReconciliationStatusSerializer(serializers.Serializer):
    """Serializer for bank reconciliation status"""

    bank_account_name = serializers.CharField()
    last_reconciled_date = serializers.DateField()
    unreconciled_transactions_count = serializers.IntegerField()
    unreconciled_amount_cents = serializers.IntegerField()
    book_balance_cents = serializers.IntegerField()
    bank_balance_cents = serializers.IntegerField()
    difference_cents = serializers.IntegerField()


# Enhanced serializers for complex operations


class RecurringInvoiceSerializer(serializers.ModelSerializer):
    template_invoice_number = serializers.CharField(
        source="template_invoice.invoice_number", read_only=True
    )
    days_until_next = serializers.SerializerMethodField()

    class Meta:
        model = RecurringInvoice
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")

    def get_days_until_next(self, obj):
        if obj.next_billing_date:
            return (obj.next_billing_date - timezone.now().date()).days
        return None


class TaxLiabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxLiability
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")


class ReportScheduleSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    next_run_in_days = serializers.SerializerMethodField()

    class Meta:
        model = ReportSchedule
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")

    def get_next_run_in_days(self, obj):
        if obj.next_generation:
            return (obj.next_generation.date() - timezone.now().date()).days
        return None


class AccountingAuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
<<<<<<< HEAD
=======
    # noqa: E501
    # noqa: E501
>>>>>>> transform-refactor

    class Meta:
        model = AccountingAuditLog
        fields = "__all__"
        read_only_fields = ("hospital", "created_at", "updated_at")
