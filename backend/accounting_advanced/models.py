import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from core.models import TimeStampedModel
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class TallyIntegration(TimeStampedModel):
    """Tally Prime integration configuration"""

    hospital = models.OneToOneField(
        "hospitals.Hospital", on_delete=models.CASCADE, related_name="tally_config"
    )

    # Tally connection details
    tally_server_url = models.URLField(help_text="Tally Prime server URL")
    company_name = models.CharField(max_length=200)
    tally_license_key = models.CharField(max_length=100, blank=True)

    # Integration settings
    auto_sync_enabled = models.BooleanField(default=True)
    sync_frequency = models.CharField(
        max_length=20,
        choices=[
            ("REALTIME", "Real-time"),
            ("HOURLY", "Hourly"),
            ("DAILY", "Daily"),
            ("WEEKLY", "Weekly"),
        ],
        default="DAILY",
    )

    # Last sync info
    last_sync_time = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=20, default="PENDING")
    sync_error_message = models.TextField(blank=True)

    # Chart of accounts mapping
    revenue_account_id = models.CharField(max_length=50, blank=True)
    expense_account_id = models.CharField(max_length=50, blank=True)
    asset_account_id = models.CharField(max_length=50, blank=True)
    liability_account_id = models.CharField(max_length=50, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Tally Integration - {self.hospital.name}"


class DepartmentBudget(TimeStampedModel):
    """Department-wise budget management"""

    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.CASCADE)
    department_name = models.CharField(max_length=100)

    # Budget period
    financial_year = models.CharField(max_length=10)  # e.g., "2024-25"
    quarter = models.CharField(
        max_length=10,
        choices=[
            ("Q1", "Quarter 1 (Apr-Jun)"),
            ("Q2", "Quarter 2 (Jul-Sep)"),
            ("Q3", "Quarter 3 (Oct-Dec)"),
            ("Q4", "Quarter 4 (Jan-Mar)"),
        ],
        blank=True,
    )

    # Budget amounts
    allocated_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    revised_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    committed_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Budget categories
    salary_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    equipment_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    consumables_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    utilities_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    maintenance_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ("DRAFT", "Draft"),
            ("APPROVED", "Approved"),
            ("ACTIVE", "Active"),
            ("CLOSED", "Closed"),
        ],
        default="DRAFT",
    )

    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["hospital", "department_name", "financial_year", "quarter"]
        indexes = [
            models.Index(fields=["hospital", "financial_year"]),
            models.Index(fields=["department_name", "status"]),
        ]

    def __str__(self):
        return f"{self.department_name} Budget - {self.financial_year} {self.quarter}"

    @property
    def remaining_budget(self):
        effective_budget = (
            self.revised_budget if self.revised_budget > 0 else self.allocated_budget
        )
        return effective_budget - self.spent_amount - self.committed_amount

    @property
    def utilization_percentage(self):
        effective_budget = (
            self.revised_budget if self.revised_budget > 0 else self.allocated_budget
        )
        if effective_budget == 0:
            return 0
        return (self.spent_amount / effective_budget) * 100

    @property
    def is_over_budget(self):
        return self.remaining_budget < 0


class ReferralTracking(TimeStampedModel):
    """Track referral income and commissions"""

    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.CASCADE)

    # Referral details
    referral_type = models.CharField(
        max_length=20,
        choices=[
            ("DOCTOR", "Doctor Referral"),
            ("HOSPITAL", "Hospital Referral"),
            ("AGENT", "Agent Referral"),
            ("CORPORATE", "Corporate Referral"),
            ("INSURANCE", "Insurance Referral"),
        ],
    )

    referrer_name = models.CharField(max_length=200)
    referrer_code = models.CharField(max_length=50, unique=True)
    referrer_contact = models.CharField(max_length=100, blank=True)

    # Patient and transaction details
    patient_id = models.IntegerField()
    patient_name = models.CharField(max_length=200)

    # Financial details
    total_bill_amount = models.DecimalField(max_digits=12, decimal_places=2)
    referral_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    referral_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Payment tracking
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("PARTIAL", "Partially Paid"),
            ("PAID", "Paid"),
            ("CANCELLED", "Cancelled"),
        ],
        default="PENDING",
    )

    payment_date = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    # Additional details
    service_date = models.DateTimeField()
    service_type = models.CharField(max_length=100)
    notes = models.TextField(blank=True)

    # Accounting integration
    tally_voucher_id = models.CharField(max_length=100, blank=True)
    synced_to_tally = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["hospital", "referrer_code"]),
            models.Index(fields=["payment_status", "service_date"]),
        ]

    def __str__(self):
        return f"Referral: {self.referrer_name} - {self.patient_name} (₹{self.referral_amount})"


class AssetRegister(TimeStampedModel):
    """Fixed assets register with depreciation"""

    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.CASCADE)

    # Asset identification
    asset_code = models.CharField(max_length=50, unique=True)
    asset_name = models.CharField(max_length=200)
    asset_category = models.CharField(
        max_length=50,
        choices=[
            ("MEDICAL_EQUIPMENT", "Medical Equipment"),
            ("IT_EQUIPMENT", "IT Equipment"),
            ("FURNITURE", "Furniture & Fixtures"),
            ("BUILDING", "Building & Infrastructure"),
            ("VEHICLE", "Vehicles"),
            ("OTHER", "Other Assets"),
        ],
    )

    # Purchase details
    purchase_date = models.DateField()
    supplier_name = models.CharField(max_length=200)
    purchase_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Installation and commissioning
    installation_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commissioning_date = models.DateField(null=True, blank=True)

    # Depreciation settings
    depreciation_method = models.CharField(
        max_length=20,
        choices=[
            ("STRAIGHT_LINE", "Straight Line"),
            ("WRITTEN_DOWN", "Written Down Value"),
            ("DOUBLE_DECLINING", "Double Declining Balance"),
        ],
        default="STRAIGHT_LINE",
    )

    useful_life_years = models.IntegerField(default=5)
    salvage_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depreciation_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=20.00
    )

    # Current status
    current_status = models.CharField(
        max_length=20,
        choices=[
            ("ACTIVE", "Active"),
            ("UNDER_MAINTENANCE", "Under Maintenance"),
            ("DISPOSED", "Disposed"),
            ("WRITTEN_OFF", "Written Off"),
        ],
        default="ACTIVE",
    )

    # Location
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=200)

    # Warranty and AMC
    warranty_end_date = models.DateField(null=True, blank=True)
    amc_provider = models.CharField(max_length=200, blank=True)
    amc_cost_annual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amc_end_date = models.DateField(null=True, blank=True)

    # Accounting integration
    tally_asset_id = models.CharField(max_length=100, blank=True)
    synced_to_tally = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["hospital", "asset_category"]),
            models.Index(fields=["current_status", "purchase_date"]),
        ]

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"

    @property
    def total_cost(self):
        return self.purchase_amount + self.installation_cost

    @property
    def current_book_value(self):
        """Calculate current book value after depreciation"""
        if self.commissioning_date:
            start_date = self.commissioning_date
        else:
            start_date = self.purchase_date

        years_elapsed = (timezone.now().date() - start_date).days / 365.25

        if self.depreciation_method == "STRAIGHT_LINE":
            annual_depreciation = (
                self.total_cost - self.salvage_value
            ) / self.useful_life_years
            total_depreciation = min(
                annual_depreciation * years_elapsed,
                self.total_cost - self.salvage_value,
            )
        elif self.depreciation_method == "WRITTEN_DOWN":
            rate = self.depreciation_rate / 100
            total_depreciation = self.total_cost * (1 - (1 - rate) ** years_elapsed)
        else:
            # Double declining balance
            rate = 2 / self.useful_life_years
            total_depreciation = self.total_cost * (1 - (1 - rate) ** years_elapsed)

        return max(self.total_cost - total_depreciation, self.salvage_value)

    @property
    def accumulated_depreciation(self):
        return self.total_cost - self.current_book_value


class ProfitLossStatement(TimeStampedModel):
    """Department-wise P&L statements"""

    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.CASCADE)
    department = models.CharField(max_length=100)

    # Period
    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(
        max_length=20,
        choices=[
            ("MONTHLY", "Monthly"),
            ("QUARTERLY", "Quarterly"),
            ("YEARLY", "Yearly"),
        ],
    )

    # Revenue
    patient_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    insurance_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    referral_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Direct costs
    staff_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    medical_supplies = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    equipment_depreciation = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    # Indirect costs
    utilities = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    maintenance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    administrative_costs = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    # Other expenses
    marketing_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    finance_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Calculated fields
    gross_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    operating_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Status
    is_finalized = models.BooleanField(default=False)
    finalized_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["hospital", "department", "period_start", "period_end"]
        indexes = [
            models.Index(fields=["hospital", "period_start"]),
            models.Index(fields=["department", "period_type"]),
        ]

    def __str__(self):
        return f"{self.department} P&L - {self.period_start} to {self.period_end}"

    @property
    def total_revenue(self):
        return (
            self.patient_revenue
            + self.insurance_revenue
            + self.referral_revenue
            + self.other_revenue
        )

    @property
    def total_direct_costs(self):
        return self.staff_costs + self.medical_supplies + self.equipment_depreciation

    @property
    def total_indirect_costs(self):
        return self.utilities + self.maintenance + self.administrative_costs

    @property
    def total_other_expenses(self):
        return self.marketing_costs + self.finance_costs + self.other_expenses

    def calculate_profits(self):
        """Calculate and update profit figures"""
        self.gross_profit = self.total_revenue - self.total_direct_costs
        self.operating_profit = self.gross_profit - self.total_indirect_costs
        self.net_profit = self.operating_profit - self.total_other_expenses
        self.save()


class BreakEvenAnalysis(TimeStampedModel):
    """Break-even analysis for departments/services"""

    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.CASCADE)
    analysis_name = models.CharField(max_length=200)

    # Analysis parameters
    department = models.CharField(max_length=100, blank=True)
    service_type = models.CharField(max_length=100, blank=True)

    # Financial inputs
    fixed_costs_monthly = models.DecimalField(max_digits=12, decimal_places=2)
    variable_cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    # Analysis period
    analysis_date = models.DateField(default=timezone.now)
    period_months = models.IntegerField(default=12)

    # Results
    breakeven_units = models.IntegerField(default=0)
    breakeven_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    margin_of_safety_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )

    # Current performance
    current_monthly_units = models.IntegerField(default=0)
    current_monthly_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    class Meta:
        indexes = [
            models.Index(fields=["hospital", "analysis_date"]),
            models.Index(fields=["department", "service_type"]),
        ]

    def __str__(self):
        return f"Break-even Analysis: {self.analysis_name}"

    def calculate_breakeven(self):
        """Calculate break-even point"""
        contribution_per_unit = (
            self.selling_price_per_unit - self.variable_cost_per_unit
        )

        if contribution_per_unit > 0:
            self.breakeven_units = int(self.fixed_costs_monthly / contribution_per_unit)
            self.breakeven_revenue = self.breakeven_units * self.selling_price_per_unit

            if self.current_monthly_units > 0:
                safety_units = self.current_monthly_units - self.breakeven_units
                self.margin_of_safety_percentage = (
                    safety_units / self.current_monthly_units
                ) * 100

        self.save()


class TallyVoucherMapping(TimeStampedModel):
    """Mapping HMS transactions to Tally vouchers"""

    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.CASCADE)

    # HMS transaction details
    hms_transaction_type = models.CharField(max_length=50)
    hms_transaction_id = models.CharField(max_length=100)
    hms_transaction_date = models.DateTimeField()
    hms_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Tally voucher details
    tally_voucher_type = models.CharField(max_length=50)
    tally_voucher_number = models.CharField(max_length=100)
    tally_voucher_date = models.DateField()
    tally_master_id = models.CharField(max_length=100)

    # Sync status
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("SYNCED", "Synced"),
            ("FAILED", "Failed"),
            ("REVERSED", "Reversed"),
        ],
        default="PENDING",
    )

    sync_attempts = models.IntegerField(default=0)
    last_sync_attempt = models.DateTimeField(null=True, blank=True)
    sync_error_message = models.TextField(blank=True)

    # Additional details
    ledger_entries = models.JSONField(default=list, blank=True)
    reference_details = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ["hospital", "hms_transaction_type", "hms_transaction_id"]
        indexes = [
            models.Index(fields=["sync_status", "last_sync_attempt"]),
            models.Index(fields=["hospital", "tally_voucher_type"]),
        ]

    def __str__(self):
        return f"{self.hms_transaction_type} - {self.hms_transaction_id} -> Tally {self.tally_voucher_number}"


class AccountingReport(TimeStampedModel):
    """Generated accounting reports"""

    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.CASCADE)

    report_type = models.CharField(
        max_length=50,
        choices=[
            ("BALANCE_SHEET", "Balance Sheet"),
            ("PROFIT_LOSS", "Profit & Loss"),
            ("CASH_FLOW", "Cash Flow Statement"),
            ("TRIAL_BALANCE", "Trial Balance"),
            ("BUDGET_VARIANCE", "Budget Variance"),
            ("DEPARTMENT_WISE_PL", "Department-wise P&L"),
            ("ASSET_REGISTER", "Asset Register"),
            ("REFERRAL_REPORT", "Referral Income Report"),
        ],
    )

    report_title = models.CharField(max_length=200)

    # Report parameters
    period_from = models.DateField()
    period_to = models.DateField()
    department_filter = models.CharField(max_length=100, blank=True)
    additional_filters = models.JSONField(default=dict, blank=True)

    # Report data
    report_data = models.JSONField(default=dict)
    report_summary = models.JSONField(default=dict, blank=True)

    # Generation details
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    generation_time = models.DateTimeField(auto_now_add=True)

    # File storage
    pdf_file_path = models.CharField(max_length=500, blank=True)
    excel_file_path = models.CharField(max_length=500, blank=True)

    # Status
    is_exported_to_tally = models.BooleanField(default=False)
    export_timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["hospital", "report_type", "-generation_time"]),
            models.Index(fields=["period_from", "period_to"]),
        ]

    def __str__(self):
        return f"{self.report_title} - {self.period_from} to {self.period_to}"
