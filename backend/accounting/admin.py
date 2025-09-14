"""
Django Admin configuration for accounting module.
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

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
    DepreciationSchedule,
    Expense,
    ExportLog,
    FinancialYear,
    FixedAsset,
    ImportBatch,
    InsuranceClaim,
    InvoiceLineItem,
    LedgerEntry,
    PayrollEntry,
    PricingTier,
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

# Configuration Models Admin


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "symbol",
        "exchange_rate",
        "is_base_currency",
        "is_active",
        "hospital",
    ]
    list_filter = ["is_base_currency", "is_active", "hospital"]
    search_fields = ["code", "name"]
    ordering = ["code"]


@admin.register(TaxConfiguration)
class TaxConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        "tax_type",
        "rate",
        "description",
        "effective_from",
        "effective_to",
        "is_active",
    ]
    list_filter = ["tax_type", "is_active", "effective_from"]
    ordering = ["-effective_from", "tax_type"]


@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
    list_display = [
        "account_code",
        "account_name",
        "account_type",
        "account_subtype",
        "parent_account",
        "is_active",
    ]
    list_filter = ["account_type", "account_subtype", "is_active"]
    search_fields = ["account_code", "account_name"]
    ordering = ["account_code"]
    readonly_fields = ["balance"]

    def balance(self, obj):
        return f"₹ {obj.balance / 100:,.2f}"

    balance.short_description = "Current Balance"


# type: ignore[attr-defined]


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "manager", "is_active", "hospital"]
    list_filter = ["is_active", "hospital"]
    search_fields = ["code", "name"]
    ordering = ["code"]


# Master Data Admin


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        "vendor_code",
        "name",
        "gstin",
        "pan",
        "tds_rate",
        "payment_terms_days",
        "is_active",
    ]
    list_filter = ["is_active", "tds_category"]
    search_fields = ["vendor_code", "name", "gstin", "pan"]
    ordering = ["name"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "vendor_code",
                    "name",
                    "contact_person",
                    "email",
                    "phone",
                    "address",
                )
            },
        ),
        (
            "Tax Information",
            {"fields": ("gstin", "pan", "tds_category", "tds_rate")},
        ),
        ("Payment Terms", {"fields": ("payment_terms_days", "is_active")}),
    )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        "customer_code",
        "name",
        "customer_type",
        "gstin",
        "credit_limit_display",
        "is_active",
    ]
    list_filter = ["customer_type", "is_active"]
    search_fields = ["customer_code", "name", "gstin"]
    ordering = ["name"]

    def credit_limit_display(self, obj):
        return f"₹ {obj.credit_limit_cents / 100:,.2f}"

    credit_limit_display.short_description = "Credit Limit"


# type: ignore[attr-defined]


# Transaction Admin


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 0
    readonly_fields = [
        "subtotal_cents",
        "taxable_cents",
        "tax_cents",
        "total_cents",
    ]


@admin.register(AccountingInvoice)
class AccountingInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "invoice_type",
        "invoice_date",
        "status",
        "total_display",
        "balance_display",
    ]
    list_filter = ["invoice_type", "status", "invoice_date", "cost_center"]
    search_fields = ["invoice_number"]
    ordering = ["-invoice_date"]
    inlines = [InvoiceLineItemInline]
    readonly_fields = [
        "invoice_number",
        "subtotal_cents",
        "tax_cents",
        "total_cents",
        "balance_cents",
    ]

    def total_display(self, obj):
        return f"₹ {obj.total_cents / 100:,.2f}"

    total_display.short_description = "Total Amount"
    # type: ignore[attr-defined]

    def balance_display(self, obj):
        return f"₹ {obj.balance_cents / 100:,.2f}"

    balance_display.short_description = "Balance"


# type: ignore[attr-defined]


@admin.register(AccountingPayment)
class AccountingPaymentAdmin(admin.ModelAdmin):
    list_display = [
        "payment_number",
        "payment_date",
        "invoice",
        "amount_display",
        "payment_method",
        "status",
    ]
    list_filter = ["payment_method", "status", "payment_date"]
    search_fields = ["payment_number", "reference_number"]
    ordering = ["-payment_date"]

    def amount_display(self, obj):
        return f"₹ {obj.amount_cents / 100:,.2f}"

    amount_display.short_description = "Amount"


# type: ignore[attr-defined]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "expense_number",
        "expense_date",
        "vendor",
        "category",
        "amount_display",
        "is_approved",
        "is_paid",
    ]
    list_filter = [
        "category",
        "is_approved",
        "is_paid",
        "expense_date",
        "cost_center",
    ]
    search_fields = ["expense_number", "description"]
    ordering = ["-expense_date"]

    def amount_display(self, obj):
        return f"₹ {obj.net_amount_cents / 100:,.2f}"

    amount_display.short_description = "Net Amount"


# type: ignore[attr-defined]


# Banking Admin


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        "account_name",
        "account_number",
        "bank_name",
        "account_type",
        "balance_display",
        "is_active",
    ]
    list_filter = ["account_type", "is_active", "bank_name"]
    search_fields = ["account_name", "account_number", "ifsc_code"]

    def balance_display(self, obj):
        return f"₹ {obj.current_balance_cents / 100:,.2f}"

    balance_display.short_description = "Current Balance"


# type: ignore[attr-defined]


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "bank_account",
        "transaction_date",
        "transaction_type",
        "amount_display",
        "description",
        "is_reconciled",
    ]
    list_filter = [
        "transaction_type",
        "is_reconciled",
        "transaction_date",
        "bank_account",
    ]
    search_fields = ["description", "reference_number"]
    ordering = ["-transaction_date"]

    def amount_display(self, obj):
        return f"₹ {obj.amount_cents / 100:,.2f}"

    amount_display.short_description = "Amount"


# type: ignore[attr-defined]


# Assets Admin


@admin.register(FixedAsset)
class FixedAssetAdmin(admin.ModelAdmin):
    list_display = [
        "asset_code",
        "name",
        "category",
        "purchase_date",
        "cost_display",
        "book_value_display",
        "is_active",
    ]
    list_filter = ["category", "is_active", "purchase_date", "cost_center"]
    search_fields = ["asset_code", "name"]
    ordering = ["asset_code"]

    def cost_display(self, obj):
        return f"₹ {obj.purchase_cost_cents / 100:,.2f}"

    cost_display.short_description = "Purchase Cost"
    # type: ignore[attr-defined]

    def book_value_display(self, obj):
        return f"₹ {obj.current_book_value_cents / 100:,.2f}"

    book_value_display.short_description = "Current Book Value"


# type: ignore[attr-defined]


@admin.register(DepreciationSchedule)
class DepreciationScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "asset",
        "depreciation_date",
        "depreciation_display",
        "book_value_display",
        "is_processed",
    ]
    list_filter = ["is_processed", "depreciation_date", "asset__category"]
    ordering = ["-depreciation_date"]
    readonly_fields = [
        "depreciation_amount_cents",
        "accumulated_depreciation_cents",
        "book_value_cents",
    ]

    def depreciation_display(self, obj):
        return f"₹ {obj.depreciation_amount_cents / 100:,.2f}"

    depreciation_display.short_description = "Depreciation"
    # type: ignore[attr-defined]

    def book_value_display(self, obj):
        return f"₹ {obj.book_value_cents / 100:,.2f}"

    book_value_display.short_description = "Book Value"


# type: ignore[attr-defined]


# Payroll Admin


@admin.register(PayrollEntry)
class PayrollEntryAdmin(admin.ModelAdmin):
    list_display = [
        "employee",
        "pay_period_display",
        "gross_display",
        "deductions_display",
        "net_display",
        "status",
    ]
    list_filter = ["status", "pay_date", "cost_center"]
    search_fields = ["employee__first_name", "employee__last_name"]
    ordering = ["-pay_date"]
    readonly_fields = [
        "gross_salary_cents",
        "total_deductions_cents",
        "net_salary_cents",
        "employer_cost_cents",
    ]

    def pay_period_display(self, obj):
        return f"{obj.pay_period_start} to {obj.pay_period_end}"

    pay_period_display.short_description = "Pay Period"
    # type: ignore[attr-defined]

    def gross_display(self, obj):
        return f"₹ {obj.gross_salary_cents / 100:,.2f}"

    gross_display.short_description = "Gross Salary"
    # type: ignore[attr-defined]

    def deductions_display(self, obj):
        return f"₹ {obj.total_deductions_cents / 100:,.2f}"

    deductions_display.short_description = "Total Deductions"
    # type: ignore[attr-defined]

    def net_display(self, obj):
        return f"₹ {obj.net_salary_cents / 100:,.2f}"

    net_display.short_description = "Net Salary"


# type: ignore[attr-defined]


# Insurance Admin


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = [
        "claim_number",
        "invoice",
        "insurance_company",
        "claim_amount_display",
        "status",
        "submission_date",
    ]
    list_filter = ["status", "submission_date", "insurance_company"]
    search_fields = ["claim_number", "policy_number", "authorization_number"]
    ordering = ["-submission_date"]

    def claim_amount_display(self, obj):
        return f"₹ {obj.claim_amount_cents / 100:,.2f}"

    claim_amount_display.short_description = "Claim Amount"


# type: ignore[attr-defined]


# Compliance Admin


@admin.register(TDSEntry)
class TDSEntryAdmin(admin.ModelAdmin):
    list_display = [
        "tds_entry_number",
        "section",
        "deduction_date",
        "deductee_display",
        "gross_amount_display",
        "tds_amount_display",
    ]
    list_filter = ["section", "deduction_date"]
    search_fields = ["tds_entry_number"]
    ordering = ["-deduction_date"]

    def deductee_display(self, obj):
        return str(obj.vendor or obj.employee)

    deductee_display.short_description = "Deductee"
    # type: ignore[attr-defined]

    def gross_amount_display(self, obj):
        return f"₹ {obj.gross_amount_cents / 100:,.2f}"

    gross_amount_display.short_description = "Gross Amount"
    # type: ignore[attr-defined]

    def tds_amount_display(self, obj):
        return f"₹ {obj.tds_amount_cents / 100:,.2f}"

    tds_amount_display.short_description = "TDS Amount"


# type: ignore[attr-defined]


@admin.register(ComplianceDocument)
class ComplianceDocumentAdmin(admin.ModelAdmin):
    list_display = [
        "document_type",
        "document_number",
        "issuing_authority",
        "issue_date",
        "expiry_date",
        "status_display",
    ]
    list_filter = ["document_type", "is_active", "expiry_date"]
    search_fields = ["document_number", "issuing_authority"]
    ordering = ["expiry_date"]

    def status_display(self, obj):
        if obj.is_expiring_soon:
            return format_html(
                '<span style="color: orange;">Expiring Soon</span>'
            )  # noqa: E501
        elif obj.expiry_date and obj.expiry_date < timezone.now().date():
            return format_html('<span style="color: red;">Expired</span>')
        else:
            return format_html('<span style="color: green;">Active</span>')

    status_display.short_description = "Status"


# type: ignore[attr-defined]


# Financial Year Admin


@admin.register(FinancialYear)
class FinancialYearAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "start_date",
        "end_date",
        "is_current",
        "is_locked",
        "hospital",
    ]
    list_filter = ["is_current", "is_locked", "hospital"]
    ordering = ["-start_date"]


# Ledger Admin


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = [
        "entry_id_short",
        "transaction_date",
        "description",
        "debit_account",
        "credit_account",
        "amount_display",
    ]
    list_filter = [
        "transaction_date",
        "debit_account__account_type",
        "credit_account__account_type",
    ]
    search_fields = ["description", "reference_number"]
    ordering = ["-transaction_date"]
    readonly_fields = ["entry_id", "amount_currency"]

    def entry_id_short(self, obj):
        return f"LE-{obj.entry_id.hex[:8]}"

    entry_id_short.short_description = "Entry ID"
    # type: ignore[attr-defined]

    def amount_display(self, obj):
        return f"₹ {obj.amount_cents / 100:,.2f}"

    amount_display.short_description = "Amount"


# type: ignore[attr-defined]


# Audit Admin


@admin.register(AccountingAuditLog)
class AccountingAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "user",
        "action_type",
        "table_name",
        "record_id",
    ]
    list_filter = ["action_type", "table_name", "timestamp"]
    search_fields = ["user__username", "table_name", "record_id"]
    ordering = ["-timestamp"]
    readonly_fields = ["timestamp"]

    def has_add_permission(self, request):
        return False  # Audit logs should not be manually added

    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be modified

    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should not be deleted


# Book Lock Admin


@admin.register(BookLock)
class BookLockAdmin(admin.ModelAdmin):
    list_display = ["lock_date", "lock_type", "locked_by", "created_at"]
    list_filter = ["lock_type", "lock_date"]
    ordering = ["-lock_date"]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing lock
            return ["lock_date", "lock_type", "locked_by"]
        return []


# Budget Admin


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = [
        "financial_year",
        "cost_center",
        "account",
        "budgeted_display",
        "actual_display",
        "variance_display",
    ]
    list_filter = ["financial_year", "cost_center"]
    search_fields = ["account__account_name", "cost_center__name"]
    readonly_fields = ["variance_cents", "variance_percentage"]

    def budgeted_display(self, obj):
        return f"₹ {obj.budgeted_amount_cents / 100:,.2f}"

    budgeted_display.short_description = "Budgeted"
    # type: ignore[attr-defined]

    def actual_display(self, obj):
        return f"₹ {obj.actual_amount_cents / 100:,.2f}"

    actual_display.short_description = "Actual"
    # type: ignore[attr-defined]

    def variance_display(self, obj):
        variance = obj.variance_cents / 100
        color = "green" if variance >= 0 else "red"
        return format_html(
            '<span style="color: {};">₹ {:,.2f} ({:.1f}%)</span>',
            color,
            variance,
            obj.variance_percentage,
        )

    variance_display.short_description = "Variance"


# type: ignore[attr-defined]


# Service Package Admin


class ServicePackageItemInline(admin.TabularInline):
    model = ServicePackageItem
    extra = 0


@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = [
        "package_code",
        "name",
        "package_type",
        "base_price_display",
        "profit_margin_display",
        "is_active",
    ]
    list_filter = ["package_type", "is_active"]
    search_fields = ["package_code", "name"]
    inlines = [ServicePackageItemInline]

    def base_price_display(self, obj):
        return f"₹ {obj.base_price_cents / 100:,.2f}"

    base_price_display.short_description = "Base Price"
    # type: ignore[attr-defined]

    def profit_margin_display(self, obj):
        if obj.cost_price_cents > 0:
            margin = (
                (obj.base_price_cents - obj.cost_price_cents)
                / obj.base_price_cents  # noqa: E501
            ) * 100
            return f"{margin:.1f}%"
        return "N/A"

    profit_margin_display.short_description = "Profit Margin"


# type: ignore[attr-defined]


# Vendor Payout Admin


class VendorPayoutItemInline(admin.TabularInline):
    model = VendorPayoutItem
    extra = 0


@admin.register(VendorPayout)
class VendorPayoutAdmin(admin.ModelAdmin):
    list_display = [
        "payout_number",
        "vendor",
        "payout_date",
        "gross_payout_display",
        "net_payout_display",
        "status",
    ]
    list_filter = ["status", "payout_date", "vendor"]
    search_fields = ["payout_number"]
    ordering = ["-payout_date"]
    inlines = [VendorPayoutItemInline]

    def gross_payout_display(self, obj):
        return f"₹ {obj.gross_payout_cents / 100:,.2f}"

    gross_payout_display.short_description = "Gross Payout"
    # type: ignore[attr-defined]

    def net_payout_display(self, obj):
        return f"₹ {obj.net_payout_cents / 100:,.2f}"

    net_payout_display.short_description = "Net Payout"


# type: ignore[attr-defined]


# Import/Export Admin


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = [
        "import_type",
        "file_name",
        "total_records",
        "successful_records",
        "failed_records",
        "import_status",
    ]
    list_filter = ["import_type", "import_status", "created_at"]
    ordering = ["-created_at"]
    readonly_fields = ["total_records", "successful_records", "failed_records"]

    def has_change_permission(self, request, obj=None):
        return False  # Import batches should not be modified after creation


@admin.register(ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    list_display = [
        "export_type",
        "report_name",
        "exported_by",
        "created_at",
        "file_size_display",
    ]
    list_filter = ["export_type", "created_at"]
    ordering = ["-created_at"]

    def file_size_display(self, obj):
        size_mb = obj.file_size_bytes / (1024 * 1024)
        return f"{size_mb:.2f} MB"

    file_size_display.short_description = "File Size"


# type: ignore[attr-defined]


# Advanced Models Admin


@admin.register(RecurringInvoice)
class RecurringInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "template_invoice",
        "frequency",
        "next_billing_date",
        "last_generated_date",
        "is_active",
    ]
    list_filter = ["frequency", "is_active"]
    ordering = ["next_billing_date"]


@admin.register(TaxLiability)
class TaxLiabilityAdmin(admin.ModelAdmin):
    list_display = [
        "period_display",
        "tax_type",
        "net_liability_display",
        "return_filed",
    ]
    list_filter = ["tax_type", "return_filed", "period_start"]
    ordering = ["-period_start"]

    def period_display(self, obj):
        return f"{obj.period_start} to {obj.period_end}"

    period_display.short_description = "Period"
    # type: ignore[attr-defined]

    def net_liability_display(self, obj):
        return f"₹ {obj.net_tax_liability_cents / 100:,.2f}"

    net_liability_display.short_description = "Net Tax Liability"


# type: ignore[attr-defined]


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "report_name",
        "report_type",
        "frequency",
        "next_generation",
        "is_active",
    ]
    list_filter = ["report_type", "frequency", "is_active"]
    ordering = ["next_generation"]


# Pricing Tier Admin


@admin.register(PricingTier)
class PricingTierAdmin(admin.ModelAdmin):
    list_display = [
        "tier_code",
        "name",
        "tier_type",
        "discount_percentage",
        "markup_percentage",
        "is_active",
    ]
    list_filter = ["tier_type", "is_active"]
    search_fields = ["tier_code", "name"]


# Custom admin actions


def export_selected_to_excel(modeladmin, request, queryset):
    """Custom admin action to export selected records to Excel"""
    # This would implement Excel export functionality


export_selected_to_excel.short_description = "Export selected items to Excel"
# type: ignore[attr-defined]

# Add the action to relevant admin classes       # noqa: E501       # noqa: E501
AccountingInvoiceAdmin.actions = [export_selected_to_excel]  # type: ignore[misc]      # noqa: E501
ExpenseAdmin.actions = [export_selected_to_excel]  # type: ignore[misc]
PayrollEntryAdmin.actions = [export_selected_to_excel]  # type: ignore[misc]


# Admin site customization
admin.site.site_header = "Hospital Accounting Administration"
admin.site.site_title = "HMS Accounting Admin"
admin.site.index_title = "Welcome to Hospital Accounting Administration"
