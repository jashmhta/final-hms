"""
Enterprise-grade accounting models for Hospital Management System.
Supports billing, expenses, payroll, assets, taxation, compliance, and reporting.      # noqa: E501
"""

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from core.models import TenantModel

User = get_user_model()


class AccountType(models.TextChoices):
    """Chart of Accounts - Main account types"""

    ASSETS = "ASSETS", "Assets"
    LIABILITIES = "LIABILITIES", "Liabilities"
    EQUITY = "EQUITY", "Equity"
    INCOME = "INCOME", "Income"
    EXPENSES = "EXPENSES", "Expenses"


class AccountSubType(models.TextChoices):
    """Detailed account sub-types for proper classification"""

    # Assets
    CURRENT_ASSETS = "CURRENT_ASSETS", "Current Assets"
    FIXED_ASSETS = "FIXED_ASSETS", "Fixed Assets"
    INTANGIBLE_ASSETS = "INTANGIBLE_ASSETS", "Intangible Assets"
    INVESTMENTS = "INVESTMENTS", "Investments"

    # Liabilities
    CURRENT_LIABILITIES = "CURRENT_LIABILITIES", "Current Liabilities"
    LONG_TERM_LIABILITIES = "LONG_TERM_LIABILITIES", "Long Term Liabilities"

    # Income
    OPERATING_INCOME = "OPERATING_INCOME", "Operating Income"
    NON_OPERATING_INCOME = "NON_OPERATING_INCOME", "Non-Operating Income"

    # Expenses
    OPERATING_EXPENSES = "OPERATING_EXPENSES", "Operating Expenses"
    ADMINISTRATIVE_EXPENSES = (
        "ADMINISTRATIVE_EXPENSES",
        "Administrative Expenses",
    )
    FINANCIAL_EXPENSES = "FINANCIAL_EXPENSES", "Financial Expenses"


class Currency(TenantModel):
    """Multi-currency support"""

    code = models.CharField(
        max_length=3, help_text="ISO 4217 currency code (e.g., INR, USD)"
    )
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, default="₹")
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=1.0000
    )  # noqa: E501
    is_base_currency = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class TaxType(models.TextChoices):
    """Types of taxes applicable"""

    GST = "GST", "Goods and Services Tax"
    CGST = "CGST", "Central GST"
    SGST = "SGST", "State GST"
    IGST = "IGST", "Integrated GST"
    VAT = "VAT", "Value Added Tax"
    SERVICE_TAX = "SERVICE_TAX", "Service Tax"
    TDS = "TDS", "Tax Deducted at Source"
    TCS = "TCS", "Tax Collected at Source"


class TaxConfiguration(TenantModel):
    """Tax rules configuration"""

    tax_type = models.CharField(max_length=32, choices=TaxType.choices)
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "accounting"
        ordering = ["-effective_from", "tax_type"]

    def __str__(self):
        return f"{self.tax_type} - {self.rate}%"


class ChartOfAccounts(TenantModel):
    """Chart of Accounts for proper accounting classification"""

    account_code = models.CharField(
        max_length=20, help_text="Unique account code (e.g., 1001)"
    )
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=32, choices=AccountType.choices)
    account_subtype = models.CharField(
        max_length=32, choices=AccountSubType.choices
    )  # noqa: E501
    parent_account = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_system_account = models.BooleanField(
        default=False
    )  # Prevents deletion of core accounts

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "account_code")
        ordering = ["account_code"]

    def __str__(self):
        return f"{self.account_code} - {self.account_name}"

    @property
    def balance(self):
        """Calculate current account balance"""
        credit_sum = (
            self.credit_entries.aggregate(total=Sum("amount_cents"))["total"]
            or 0  # noqa: E501
        )
        debit_sum = (
            self.debit_entries.aggregate(total=Sum("amount_cents"))["total"]
            or 0  # noqa: E501
        )

        if self.account_type in [AccountType.ASSETS, AccountType.EXPENSES]:
            return debit_sum - credit_sum  # Normal debit balance
        else:
            return credit_sum - debit_sum  # Normal credit balance


class CostCenter(TenantModel):
    """Cost centers for departmental tracking"""

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )  # noqa: E501
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Vendor(TenantModel):
    """Vendors and service providers"""

    vendor_code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    gstin = models.CharField(
        max_length=15, blank=True, help_text="GST Identification Number"
    )
    pan = models.CharField(max_length=10, blank=True, help_text="PAN Number")
    tds_category = models.CharField(max_length=50, blank=True)
    tds_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )  # noqa: E501
    payment_terms_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "vendor_code")
        ordering = ["name"]

    def __str__(self):
        return f"{self.vendor_code} - {self.name}"


class Customer(TenantModel):
    """Corporate customers and insurance companies"""

    customer_code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    customer_type = models.CharField(
        max_length=32,
        choices=[
            ("CORPORATE", "Corporate"),
            ("INSURANCE", "Insurance Company"),
            ("GOVERNMENT", "Government"),
            ("OTHER", "Other"),
        ],
        default="CORPORATE",
    )
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    gstin = models.CharField(max_length=15, blank=True)
    credit_limit_cents = models.BigIntegerField(default=0)
    credit_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "customer_code")
        ordering = ["name"]

    def __str__(self):
        return f"{self.customer_code} - {self.name}"


class ServicePackage(TenantModel):
    """Service packages for bundled billing"""

    package_code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    package_type = models.CharField(
        max_length=32,
        choices=[
            ("SURGERY", "Surgery Package"),
            ("DIAGNOSTIC", "Diagnostic Package"),
            ("CONSULTATION", "Consultation Package"),
            ("WELLNESS", "Wellness Package"),
            ("EMERGENCY", "Emergency Package"),
        ],
    )
    base_price_cents = models.BigIntegerField()
    cost_price_cents = models.BigIntegerField(
        help_text="Internal cost for profitability analysis"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "package_code")
        ordering = ["package_code"]

    def __str__(self):
        return f"{self.package_code} - {self.name}"


class ServicePackageItem(TenantModel):
    """Items included in service packages"""

    package = models.ForeignKey(
        ServicePackage, on_delete=models.CASCADE, related_name="items"
    )
    service = models.ForeignKey(
        "billing.ServiceCatalog", on_delete=models.CASCADE
    )  # noqa: E501
    quantity = models.IntegerField(default=1)
    override_price_cents = models.BigIntegerField(null=True, blank=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("package", "service")


class PricingTier(TenantModel):
    """B2B and B2C pricing tiers"""

    tier_code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    tier_type = models.CharField(
        max_length=10,
        choices=[
            ("B2B", "Business to Business"),
            ("B2C", "Business to Consumer"),
        ],
    )
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    markup_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "tier_code")
        ordering = ["tier_code"]

    def __str__(self):
        return f"{self.tier_code} - {self.name} ({self.tier_type})"


class LedgerEntry(TenantModel):
    """Double-entry bookkeeping ledger entries"""

    entry_id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False
    )  # noqa: E501
    transaction_date = models.DateField()
    reference_number = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    debit_account = models.ForeignKey(
        ChartOfAccounts, on_delete=models.CASCADE, related_name="debit_entries"
    )
    credit_account = models.ForeignKey(
        ChartOfAccounts,
        on_delete=models.CASCADE,
        related_name="credit_entries",
    )
    amount_cents = models.BigIntegerField()
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=1.0000
    )  # noqa: E501

    # References to source transactions
    invoice = models.ForeignKey(
        "AccountingInvoice", on_delete=models.SET_NULL, null=True, blank=True
    )
    payment = models.ForeignKey(
        "AccountingPayment", on_delete=models.SET_NULL, null=True, blank=True
    )
    expense = models.ForeignKey(
        "Expense", on_delete=models.SET_NULL, null=True, blank=True
    )
    payroll = models.ForeignKey(
        "PayrollEntry", on_delete=models.SET_NULL, null=True, blank=True
    )

    # Audit and control
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_reversed = models.BooleanField(default=False)
    reversal_entry = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        app_label = "accounting"
        ordering = ["-transaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["debit_account", "transaction_date"]),
            models.Index(fields=["credit_account", "transaction_date"]),
        ]

    def __str__(self):
        return f"LE-{self.entry_id.hex[:8]} - {self.description}"

    @property
    def amount_currency(self):
        """Amount in the transaction currency"""
        return Decimal(self.amount_cents) / 100


class AccountingInvoice(TenantModel):
    """Enhanced invoicing system"""

    INVOICE_TYPES = [
        ("PATIENT", "Patient Invoice"),
        ("CORPORATE", "Corporate Invoice"),
        ("INSURANCE", "Insurance Invoice"),
        ("VENDOR", "Vendor Invoice"),
    ]

    INVOICE_STATUS = [
        ("DRAFT", "Draft"),
        ("SENT", "Sent"),
        ("OVERDUE", "Overdue"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
        ("PARTIAL", "Partially Paid"),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES)
    invoice_date = models.DateField()
    due_date = models.DateField()

    # Billing entities
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, null=True, blank=True
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, null=True, blank=True
    )
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, null=True, blank=True
    )  # noqa: E501

    # Financial details
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    subtotal_cents = models.BigIntegerField(default=0)
    tax_cents = models.BigIntegerField(default=0)
    discount_cents = models.BigIntegerField(default=0)
    total_cents = models.BigIntegerField(default=0)
    paid_cents = models.BigIntegerField(default=0)
    balance_cents = models.BigIntegerField(default=0)

    # References
    bill = models.ForeignKey(
        "billing.Bill", on_delete=models.SET_NULL, null=True, blank=True
    )
    cost_center = models.ForeignKey(
        CostCenter, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Status and control
    status = models.CharField(
        max_length=20, choices=INVOICE_STATUS, default="DRAFT"
    )  # noqa: E501
    terms_and_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    # Split billing for insurance
    insurance_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    employer_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    patient_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=100.00
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        app_label = "accounting"
        ordering = ["-invoice_date"]
        indexes = [
            models.Index(fields=["invoice_date"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["customer"]),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.get_invoice_type_display()}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.generate_invoice_number()
        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        """Generate unique invoice number"""
        current_year = timezone.now().year
        prefix = f"INV-{current_year}-"
        last_invoice = (
            AccountingInvoice.objects.filter(
                hospital=self.hospital, invoice_number__startswith=prefix
            )
            .order_by("-invoice_number")
            .first()
        )

        if last_invoice:
            try:
                last_number = int(last_invoice.invoice_number.split("-")[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        self.invoice_number = f"{prefix}{new_number:06d}"

    def calculate_totals(self):
        """Recalculate invoice totals"""
        items = self.items.all()
        if items.exists():
            # Subtotal is the sum of line item subtotals (pre-tax)
            self.subtotal_cents = sum(item.subtotal_cents for item in items)
            self.tax_cents = sum(item.tax_cents for item in items)
            self.total_cents = (
                self.subtotal_cents + self.tax_cents - self.discount_cents
            )
        # Always recompute balance based on current total and paid amounts
        self.balance_cents = self.total_cents - self.paid_cents

        # Update status based on payment
        if self.total_cents > 0 and self.paid_cents >= self.total_cents:
            self.status = "PAID"
        elif self.paid_cents > 0:
            self.status = "PARTIAL"
        elif timezone.now().date() > self.due_date:
            self.status = "OVERDUE"

        # Persist fields (subtotal/tax/total only if items exist)
        update_fields = ["balance_cents", "status"]
        if items.exists():
            update_fields.extend(
                ["subtotal_cents", "tax_cents", "total_cents"]
            )  # noqa: E501
        self.save(update_fields=update_fields)


class InvoiceLineItem(TenantModel):
    """Invoice line items with detailed tracking"""

    invoice = models.ForeignKey(
        AccountingInvoice, on_delete=models.CASCADE, related_name="items"
    )
    service = models.ForeignKey(
        "billing.ServiceCatalog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    package = models.ForeignKey(
        ServicePackage, on_delete=models.SET_NULL, null=True, blank=True
    )

    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price_cents = models.BigIntegerField()
    cost_price_cents = models.BigIntegerField(
        default=0
    )  # For profitability analysis      # noqa: E501

    subtotal_cents = models.BigIntegerField()  # quantity * unit_price
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    discount_cents = models.BigIntegerField(default=0)
    taxable_cents = models.BigIntegerField()  # subtotal - discount

    # Tax breakdown
    tax_cents = models.BigIntegerField(default=0)
    cgst_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )  # noqa: E501
    cgst_cents = models.BigIntegerField(default=0)
    sgst_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )  # noqa: E501
    sgst_cents = models.BigIntegerField(default=0)
    igst_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )  # noqa: E501
    igst_cents = models.BigIntegerField(default=0)

    total_cents = models.BigIntegerField()  # taxable + tax

    # Outsourcing
    is_outsourced = models.BooleanField(default=False)
    outsource_vendor = models.ForeignKey(
        Vendor, on_delete=models.SET_NULL, null=True, blank=True
    )
    vendor_payout_cents = models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):
        self.calculate_amounts()
        super().save(*args, **kwargs)
        self.invoice.calculate_totals()

    def calculate_amounts(self):
        """Calculate all amounts for this line item"""
        self.subtotal_cents = int(self.quantity * self.unit_price_cents)
        self.discount_cents = int(
            self.subtotal_cents * self.discount_percentage / 100
        )  # noqa: E501
        self.taxable_cents = self.subtotal_cents - self.discount_cents

        # Calculate taxes
        self.cgst_cents = int(self.taxable_cents * self.cgst_rate / 100)
        self.sgst_cents = int(self.taxable_cents * self.sgst_rate / 100)
        self.igst_cents = int(self.taxable_cents * self.igst_rate / 100)
        self.tax_cents = self.cgst_cents + self.sgst_cents + self.igst_cents

        self.total_cents = self.taxable_cents + self.tax_cents


class AccountingPayment(TenantModel):
    """Enhanced payment tracking system"""

    PAYMENT_METHODS = [
        ("CASH", "Cash"),
        ("CARD", "Credit/Debit Card"),
        ("UPI", "UPI"),
        ("NET_BANKING", "Net Banking"),
        ("BANK_TRANSFER", "Bank Transfer"),
        ("CHEQUE", "Cheque"),
        ("DD", "Demand Draft"),
        ("INSURANCE_DIRECT", "Insurance Direct Settlement"),
        ("CORPORATE_CREDIT", "Corporate Credit"),
        ("ADJUSTMENT", "Adjustment"),
    ]

    PAYMENT_STATUS = [
        ("PENDING", "Pending"),
        ("CLEARED", "Cleared"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
        ("RECONCILED", "Bank Reconciled"),
    ]

    payment_number = models.CharField(max_length=50, unique=True)
    payment_date = models.DateField()
    invoice = models.ForeignKey(
        AccountingInvoice, on_delete=models.CASCADE, related_name="payments"
    )

    amount_cents = models.BigIntegerField()
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=1.0000
    )  # noqa: E501

    payment_method = models.CharField(max_length=32, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True)
    bank_account = models.ForeignKey(
        "BankAccount", on_delete=models.SET_NULL, null=True, blank=True
    )

    # TDS if applicable
    tds_cents = models.BigIntegerField(default=0)
    tds_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )  # noqa: E501

    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, default="PENDING"
    )  # noqa: E501
    notes = models.TextField(blank=True)

    received_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        app_label = "accounting"
        ordering = ["-payment_date"]

    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.generate_payment_number()
        super().save(*args, **kwargs)
        # Recompute paid amount from all payments
        self.invoice.paid_cents = (
            self.invoice.payments.aggregate(total=Sum("amount_cents"))["total"]
            or 0  # noqa: E501
        )
        # Persist the paid amount, then recalc totals/balance/status
        self.invoice.save(update_fields=["paid_cents"])
        self.invoice.calculate_totals()

    def generate_payment_number(self):
        """Generate unique payment number"""
        current_year = timezone.now().year
        prefix = f"PMT-{current_year}-"
        last_payment = (
            AccountingPayment.objects.filter(
                hospital=self.hospital, payment_number__startswith=prefix
            )
            .order_by("-payment_number")
            .first()
        )

        if last_payment:
            try:
                last_number = int(last_payment.payment_number.split("-")[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        self.payment_number = f"{prefix}{new_number:06d}"


class Expense(TenantModel):
    """Expense tracking with cost center allocation"""

    EXPENSE_CATEGORIES = [
        ("MEDICAL_SUPPLIES", "Medical Supplies"),
        ("PHARMACEUTICALS", "Pharmaceuticals"),
        ("EQUIPMENT", "Equipment"),
        ("UTILITIES", "Utilities"),
        ("RENT", "Rent"),
        ("SALARIES", "Salaries"),
        ("PROFESSIONAL_FEES", "Professional Fees"),
        ("MAINTENANCE", "Maintenance"),
        ("INSURANCE", "Insurance"),
        ("MARKETING", "Marketing"),
        ("ADMINISTRATIVE", "Administrative"),
        ("OTHER", "Other"),
    ]

    expense_number = models.CharField(max_length=50, unique=True)
    expense_date = models.DateField()
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE)

    category = models.CharField(max_length=32, choices=EXPENSE_CATEGORIES)
    description = models.CharField(max_length=255)

    # Financial details
    amount_cents = models.BigIntegerField()
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    tax_cents = models.BigIntegerField(default=0)
    tds_cents = models.BigIntegerField(default=0)
    net_amount_cents = models.BigIntegerField()  # amount + tax - tds

    # Reference documents
    invoice_number = models.CharField(max_length=100, blank=True)
    purchase_order_number = models.CharField(max_length=100, blank=True)

    # Status
    is_approved = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_expenses",
    )

    class Meta:
        app_label = "accounting"
        ordering = ["-expense_date"]

    def save(self, *args, **kwargs):
        if not self.expense_number:
            self.generate_expense_number()
        self.net_amount_cents = (
            self.amount_cents + self.tax_cents - self.tds_cents
        )  # noqa: E501
        super().save(*args, **kwargs)

    def generate_expense_number(self):
        """Generate unique expense number"""
        current_year = timezone.now().year
        prefix = f"EXP-{current_year}-"
        last_expense = (
            Expense.objects.filter(
                hospital=self.hospital, expense_number__startswith=prefix
            )
            .order_by("-expense_number")
            .first()
        )

        if last_expense:
            try:
                last_number = int(last_expense.expense_number.split("-")[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        self.expense_number = f"{prefix}{new_number:06d}"


class BankAccount(TenantModel):
    """Bank account management"""

    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=255)
    branch = models.CharField(max_length=255, blank=True)
    ifsc_code = models.CharField(max_length=11, blank=True)
    account_type = models.CharField(
        max_length=20,
        choices=[
            ("SAVINGS", "Savings Account"),
            ("CURRENT", "Current Account"),
            ("CC", "Cash Credit"),
            ("OD", "Overdraft"),
        ],
        default="CURRENT",
    )
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    opening_balance_cents = models.BigIntegerField(default=0)
    current_balance_cents = models.BigIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "account_number", "ifsc_code")

    def __str__(self):
        return f"{self.account_name} - {self.account_number}"

    def update_balance(self):
        """Update current balance based on transactions"""
        total_credits = (
            self.credit_transactions.aggregate(total=Sum("amount_cents"))[
                "total"
            ]  # noqa: E501
            or 0  # noqa: E501
        )
        total_debits = (
            self.debit_transactions.aggregate(total=Sum("amount_cents"))[
                "total"
            ]  # noqa: E501
            or 0  # noqa: E501
        )

        self.current_balance_cents = (
            self.opening_balance_cents + total_credits - total_debits
        )
        self.save(update_fields=["current_balance_cents"])


class BankTransaction(TenantModel):
    """Bank transactions for reconciliation"""

    TRANSACTION_TYPES = [
        ("CREDIT", "Credit"),
        ("DEBIT", "Debit"),
    ]

    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_date = models.DateField()
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPES
    )  # noqa: E501
    amount_cents = models.BigIntegerField()
    description = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=100, blank=True)

    # Reconciliation
    is_reconciled = models.BooleanField(default=False)
    reconciled_payment = models.ForeignKey(
        AccountingPayment, on_delete=models.SET_NULL, null=True, blank=True
    )
    reconciled_expense = models.ForeignKey(
        Expense, on_delete=models.SET_NULL, null=True, blank=True
    )
    reconciled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    reconciled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "accounting"
        ordering = ["-transaction_date"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update bank account balance when transaction is saved
        if self.transaction_type == "CREDIT":
            self.bank_account.current_balance_cents += self.amount_cents
        else:
            self.bank_account.current_balance_cents -= self.amount_cents
        self.bank_account.save(update_fields=["current_balance_cents"])


class FixedAsset(TenantModel):
    """Fixed assets register with depreciation"""

    ASSET_CATEGORIES = [
        ("MEDICAL_EQUIPMENT", "Medical Equipment"),
        ("IT_EQUIPMENT", "IT Equipment"),
        ("FURNITURE", "Furniture & Fixtures"),
        ("VEHICLES", "Vehicles"),
        ("BUILDING", "Building"),
        ("LAND", "Land"),
        ("OFFICE_EQUIPMENT", "Office Equipment"),
        ("OTHER", "Other"),
    ]

    DEPRECIATION_METHODS = [
        ("STRAIGHT_LINE", "Straight Line"),
        ("REDUCING_BALANCE", "Written Down Value"),
        ("DOUBLE_DECLINING", "Double Declining Balance"),
    ]

    asset_code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=ASSET_CATEGORIES)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE)

    # Purchase details
    purchase_date = models.DateField()
    purchase_cost_cents = models.BigIntegerField()
    vendor = models.ForeignKey(
        Vendor, on_delete=models.SET_NULL, null=True, blank=True
    )  # noqa: E501
    invoice_reference = models.CharField(max_length=100, blank=True)

    # Depreciation
    depreciation_method = models.CharField(
        max_length=32, choices=DEPRECIATION_METHODS, default="STRAIGHT_LINE"
    )
    useful_life_years = models.IntegerField()
    salvage_value_cents = models.BigIntegerField(default=0)
    depreciation_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    # Current status
    current_book_value_cents = models.BigIntegerField()
    accumulated_depreciation_cents = models.BigIntegerField(default=0)

    # Disposal
    disposal_date = models.DateField(null=True, blank=True)
    disposal_amount_cents = models.BigIntegerField(null=True, blank=True)
    disposal_method = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "asset_code")
        ordering = ["asset_code"]

    def __str__(self):
        return f"{self.asset_code} - {self.name}"

    def calculate_annual_depreciation(self):
        """Calculate annual depreciation amount"""
        if self.depreciation_method == "STRAIGHT_LINE":
            return (
                self.purchase_cost_cents - self.salvage_value_cents
            ) // self.useful_life_years
        elif self.depreciation_method == "REDUCING_BALANCE":
            rate = (
                self.depreciation_rate / 100
                if self.depreciation_rate
                else (1 / self.useful_life_years)
            )
            return int(self.current_book_value_cents * rate)
        elif self.depreciation_method == "DOUBLE_DECLINING":
            rate = 2 / self.useful_life_years
            return int(self.current_book_value_cents * rate)
        return 0


class DepreciationSchedule(TenantModel):
    """Depreciation schedule entries"""

    asset = models.ForeignKey(
        FixedAsset,
        on_delete=models.CASCADE,
        related_name="depreciation_entries",
    )
    depreciation_date = models.DateField()
    depreciation_amount_cents = models.BigIntegerField()
    accumulated_depreciation_cents = models.BigIntegerField()
    book_value_cents = models.BigIntegerField()
    is_processed = models.BooleanField(default=False)
    processed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("asset", "depreciation_date")
        ordering = ["depreciation_date"]


class PayrollEntry(TenantModel):
    """Payroll processing"""

    PAYROLL_STATUS = [
        ("DRAFT", "Draft"),
        ("APPROVED", "Approved"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    ]

    employee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="payroll_entries"
    )
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    pay_date = models.DateField()

    # Basic pay components
    basic_salary_cents = models.BigIntegerField()
    hra_cents = models.BigIntegerField(default=0)
    medical_allowance_cents = models.BigIntegerField(default=0)
    transport_allowance_cents = models.BigIntegerField(default=0)
    other_allowances_cents = models.BigIntegerField(default=0)

    # Overtime and bonuses
    overtime_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0
    )  # noqa: E501
    overtime_rate_cents = models.BigIntegerField(default=0)
    bonus_cents = models.BigIntegerField(default=0)
    incentive_cents = models.BigIntegerField(default=0)

    # Deductions
    pf_employee_cents = models.BigIntegerField(default=0)
    pf_employer_cents = models.BigIntegerField(
        default=0
    )  # This goes to expenses      # noqa: E501
    esi_employee_cents = models.BigIntegerField(default=0)
    esi_employer_cents = models.BigIntegerField(
        default=0
    )  # This goes to expenses      # noqa: E501
    professional_tax_cents = models.BigIntegerField(default=0)
    tds_cents = models.BigIntegerField(default=0)
    advance_deduction_cents = models.BigIntegerField(default=0)
    other_deductions_cents = models.BigIntegerField(default=0)

    # Calculated totals
    gross_salary_cents = models.BigIntegerField()
    total_deductions_cents = models.BigIntegerField()
    net_salary_cents = models.BigIntegerField()
    employer_cost_cents = (
        models.BigIntegerField()
    )  # Includes employer contributions      # noqa: E501

    status = models.CharField(
        max_length=20, choices=PAYROLL_STATUS, default="DRAFT"
    )  # noqa: E501
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE)

    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_payrolls"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payrolls",
    )

    class Meta:
        app_label = "accounting"
        unique_together = ("employee", "pay_period_start", "pay_period_end")
        ordering = ["-pay_date"]

    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate all payroll totals"""
        # Calculate gross salary
        self.gross_salary_cents = (
            self.basic_salary_cents
            + self.hra_cents
            + self.medical_allowance_cents
            + self.transport_allowance_cents
            + self.other_allowances_cents
            + (self.overtime_hours * self.overtime_rate_cents)
            + self.bonus_cents
            + self.incentive_cents
        )

        # Calculate total deductions
        self.total_deductions_cents = (
            self.pf_employee_cents
            + self.esi_employee_cents
            + self.professional_tax_cents
            + self.tds_cents
            + self.advance_deduction_cents
            + self.other_deductions_cents
        )

        # Calculate net salary
        self.net_salary_cents = (
            self.gross_salary_cents - self.total_deductions_cents
        )  # noqa: E501

        # Calculate employer cost (includes employer contributions)
        self.employer_cost_cents = (
            self.gross_salary_cents
            + self.pf_employer_cents
            + self.esi_employer_cents  # noqa: E501
        )


class InsuranceClaim(TenantModel):
    """Insurance claim tracking"""

    CLAIM_STATUS = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("PARTIALLY_APPROVED", "Partially Approved"),
        ("PAID", "Paid"),
        ("SETTLED", "Settled"),
    ]

    claim_number = models.CharField(max_length=50, unique=True)
    invoice = models.ForeignKey(AccountingInvoice, on_delete=models.CASCADE)
    insurance_company = models.ForeignKey(Customer, on_delete=models.CASCADE)

    claim_amount_cents = models.BigIntegerField()
    approved_amount_cents = models.BigIntegerField(default=0)
    received_amount_cents = models.BigIntegerField(default=0)

    submission_date = models.DateField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=32, choices=CLAIM_STATUS, default="DRAFT"
    )  # noqa: E501
    rejection_reason = models.TextField(blank=True)

    # Reference numbers
    insurance_ref_number = models.CharField(max_length=100, blank=True)
    policy_number = models.CharField(max_length=100, blank=True)
    authorization_number = models.CharField(max_length=100, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        app_label = "accounting"
        ordering = ["-submission_date"]

    def save(self, *args, **kwargs):
        if not self.claim_number:
            self.generate_claim_number()
        super().save(*args, **kwargs)

    def generate_claim_number(self):
        """Generate unique claim number"""
        current_year = timezone.now().year
        prefix = f"CLM-{current_year}-"
        last_claim = (
            InsuranceClaim.objects.filter(
                hospital=self.hospital, claim_number__startswith=prefix
            )
            .order_by("-claim_number")
            .first()
        )

        if last_claim:
            try:
                last_number = int(last_claim.claim_number.split("-")[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        self.claim_number = f"{prefix}{new_number:06d}"


class TDSEntry(TenantModel):
    """TDS (Tax Deducted at Source) tracking"""

    TDS_SECTIONS = [
        ("194A", "Interest other than on Securities - 194A"),
        ("194C", "Payments to Contractors - 194C"),
        ("194H", "Commission or Brokerage - 194H"),
        ("194I", "Rent - 194I"),
        ("194J", "Professional Fees - 194J"),
        ("194O", "E-commerce - 194O"),
        ("192", "Salary - 192"),
    ]

    tds_entry_number = models.CharField(max_length=50, unique=True)
    deduction_date = models.DateField()
    section = models.CharField(max_length=10, choices=TDS_SECTIONS)

    # Deductee details
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, null=True, blank=True
    )  # noqa: E501
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tds_entries_employee",
    )

    gross_amount_cents = models.BigIntegerField()
    tds_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tds_amount_cents = models.BigIntegerField()

    # References
    expense = models.ForeignKey(
        Expense, on_delete=models.SET_NULL, null=True, blank=True
    )
    payroll = models.ForeignKey(
        PayrollEntry, on_delete=models.SET_NULL, null=True, blank=True
    )

    # TDS Certificate details
    certificate_number = models.CharField(max_length=100, blank=True)
    certificate_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_tds_entries"
    )

    class Meta:
        app_label = "accounting"
        ordering = ["-deduction_date"]

    def save(self, *args, **kwargs):
        if not self.tds_entry_number:
            self.generate_tds_number()
        super().save(*args, **kwargs)

    def generate_tds_number(self):
        """Generate unique TDS entry number"""
        current_year = timezone.now().year
        prefix = f"TDS-{current_year}-"
        last_tds = (
            TDSEntry.objects.filter(
                hospital=self.hospital, tds_entry_number__startswith=prefix
            )
            .order_by("-tds_entry_number")
            .first()
        )

        if last_tds:
            try:
                last_number = int(last_tds.tds_entry_number.split("-")[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        self.tds_entry_number = f"{prefix}{new_number:06d}"


class BookLock(TenantModel):
    """Book locking for preventing backdated entries"""

    lock_date = models.DateField()
    lock_type = models.CharField(
        max_length=20,
        choices=[
            ("MONTHLY", "Monthly Lock"),
            ("QUARTERLY", "Quarterly Lock"),
            ("YEARLY", "Yearly Lock"),
        ],
    )
    locked_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "lock_date", "lock_type")
        ordering = ["-lock_date"]

    def __str__(self):
        return f"{self.lock_type} lock for {self.lock_date}"


class AccountingPeriod(TenantModel):
    """Accounting periods for financial reporting"""

    period_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    closed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "start_date", "end_date")
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.period_name} ({self.start_date} to {self.end_date})"


class VendorPayout(TenantModel):
    """Track payouts to outsourced service providers"""

    PAYOUT_STATUS = [
        ("PENDING", "Pending"),
        ("PROCESSED", "Processed"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    ]

    payout_number = models.CharField(max_length=50, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    payout_date = models.DateField()

    # Services provided
    total_services_cents = models.BigIntegerField()
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )  # noqa: E501
    commission_cents = models.BigIntegerField(default=0)

    # Amounts
    gross_payout_cents = models.BigIntegerField()
    tds_cents = models.BigIntegerField(default=0)
    other_deductions_cents = models.BigIntegerField(default=0)
    net_payout_cents = models.BigIntegerField()

    status = models.CharField(
        max_length=20, choices=PAYOUT_STATUS, default="PENDING"
    )  # noqa: E501
    payment_reference = models.CharField(max_length=100, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        app_label = "accounting"
        ordering = ["-payout_date"]

    def save(self, *args, **kwargs):
        if not self.payout_number:
            self.generate_payout_number()

        self.commission_cents = int(
            self.total_services_cents * self.commission_rate / 100
        )
        self.gross_payout_cents = (
            self.total_services_cents - self.commission_cents
        )  # noqa: E501
        self.net_payout_cents = (
            self.gross_payout_cents
            - self.tds_cents
            - self.other_deductions_cents  # noqa: E501
        )

        super().save(*args, **kwargs)

    def generate_payout_number(self):
        """Generate unique payout number"""
        current_year = timezone.now().year
        prefix = f"PAY-{current_year}-"
        last_payout = (
            VendorPayout.objects.filter(
                hospital=self.hospital, payout_number__startswith=prefix
            )
            .order_by("-payout_number")
            .first()
        )

        if last_payout:
            try:
                last_number = int(last_payout.payout_number.split("-")[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        self.payout_number = f"{prefix}{new_number:06d}"


class VendorPayoutItem(TenantModel):
    """Individual services included in vendor payout"""

    payout = models.ForeignKey(
        VendorPayout, on_delete=models.CASCADE, related_name="items"
    )
    invoice_line_item = models.ForeignKey(
        InvoiceLineItem, on_delete=models.CASCADE
    )  # noqa: E501
    service_date = models.DateField()
    amount_cents = models.BigIntegerField()
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)


class RecurringInvoice(TenantModel):
    """Recurring billing setup"""

    FREQUENCY_CHOICES = [
        ("MONTHLY", "Monthly"),
        ("QUARTERLY", "Quarterly"),
        ("HALF_YEARLY", "Half Yearly"),
        ("YEARLY", "Yearly"),
    ]

    template_invoice = models.ForeignKey(
        AccountingInvoice, on_delete=models.CASCADE
    )  # noqa: E501
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_billing_date = models.DateField()
    last_generated_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        app_label = "accounting"
        ordering = ["next_billing_date"]


class TaxLiability(TenantModel):
    """Tax liability tracking"""

    period_start = models.DateField()
    period_end = models.DateField()
    tax_type = models.CharField(max_length=32, choices=TaxType.choices)

    # Tax calculations
    total_sales_cents = models.BigIntegerField(default=0)
    taxable_sales_cents = models.BigIntegerField(default=0)
    tax_collected_cents = models.BigIntegerField(default=0)
    tax_paid_cents = models.BigIntegerField(default=0)
    input_tax_credit_cents = models.BigIntegerField(default=0)
    net_tax_liability_cents = models.BigIntegerField(default=0)

    # Filing details
    return_filed = models.BooleanField(default=False)
    filing_date = models.DateField(null=True, blank=True)
    acknowledgment_number = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = "accounting"
        unique_together = (
            "hospital",
            "period_start",
            "period_end",
            "tax_type",
        )
        ordering = ["-period_start"]


class ComplianceDocument(TenantModel):
    """Store compliance documents and certificates"""

    DOCUMENT_TYPES = [
        ("GST_CERTIFICATE", "GST Certificate"),
        ("TRADE_LICENSE", "Trade License"),
        ("DRUG_LICENSE", "Drug License"),
        ("FIRE_SAFETY", "Fire Safety Certificate"),
        ("POLLUTION_CLEARANCE", "Pollution Clearance"),
        ("LABOR_LICENSE", "Labor License"),
        ("PF_REGISTRATION", "PF Registration"),
        ("ESI_REGISTRATION", "ESI Registration"),
        ("TAN_CERTIFICATE", "TAN Certificate"),
        ("OTHER", "Other"),
    ]

    document_type = models.CharField(max_length=32, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=100)
    issuing_authority = models.CharField(max_length=255)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    renewal_date = models.DateField(null=True, blank=True)
    document_file = models.FileField(
        upload_to="compliance_documents/", null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "document_type", "document_number")
        ordering = ["expiry_date"]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.document_number}"

    @property
    def is_expiring_soon(self):
        """Check if document expires within 30 days"""
        if self.expiry_date:
            return (self.expiry_date - timezone.now().date()).days <= 30
        return False


# Financial Year and Reporting Models


class FinancialYear(TenantModel):
    """Financial year configuration"""

    name = models.CharField(max_length=20, help_text="e.g., 2024-25")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta:
        app_label = "accounting"
        unique_together = ("hospital", "name")
        ordering = ["-start_date"]

    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one current financial year
            FinancialYear.objects.filter(
                hospital=self.hospital, is_current=True
            ).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"FY {self.name}"


# Budget and Planning Models


class Budget(TenantModel):
    """Annual budgets by cost center and account"""

    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE)
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.CASCADE)

    budgeted_amount_cents = models.BigIntegerField()
    actual_amount_cents = models.BigIntegerField(default=0)
    variance_cents = models.BigIntegerField(default=0)
    variance_percentage = models.DecimalField(
        max_digits=6, decimal_places=2, default=0.00
    )

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        app_label = "accounting"
        unique_together = ("financial_year", "cost_center", "account")
        ordering = ["cost_center", "account"]

    def calculate_variance(self):
        """Calculate budget variance"""
        self.variance_cents = (
            self.actual_amount_cents - self.budgeted_amount_cents
        )  # noqa: E501
        if self.budgeted_amount_cents != 0:
            self.variance_percentage = (
                self.variance_cents / self.budgeted_amount_cents
            ) * 100
        else:
            self.variance_percentage = 0
        self.save(update_fields=["variance_cents", "variance_percentage"])


# Advanced Features


class ProviderCommissionStructure(TenantModel):
    """Commission structure for outsourced providers"""

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    service = models.ForeignKey(
        "billing.ServiceCatalog", on_delete=models.CASCADE
    )  # noqa: E501
    commission_type = models.CharField(
        max_length=20,
        choices=[
            ("PERCENTAGE", "Percentage"),
            ("FIXED", "Fixed Amount"),
            ("TIER", "Tier Based"),
        ],
    )
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )  # noqa: E501
    fixed_amount_cents = models.BigIntegerField(default=0)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "accounting"
        unique_together = ("vendor", "service", "effective_from")
        ordering = ["-effective_from"]


class ReportSchedule(TenantModel):
    """Scheduled report generation"""

    REPORT_TYPES = [
        ("PROFIT_LOSS", "Profit & Loss Statement"),
        ("BALANCE_SHEET", "Balance Sheet"),
        ("CASH_FLOW", "Cash Flow Statement"),
        ("TRIAL_BALANCE", "Trial Balance"),
        ("AGING_REPORT", "Aging Report"),
        ("GST_RETURN", "GST Return"),
        ("TDS_RETURN", "TDS Return"),
        ("PAYROLL_SUMMARY", "Payroll Summary"),
        ("ASSET_DEPRECIATION", "Asset Depreciation Report"),
    ]

    FREQUENCY_CHOICES = [
        ("DAILY", "Daily"),
        ("WEEKLY", "Weekly"),
        ("MONTHLY", "Monthly"),
        ("QUARTERLY", "Quarterly"),
    ]

    report_name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=32, choices=REPORT_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    recipients = models.TextField(
        help_text="Email addresses separated by commas"
    )  # noqa: E501
    last_generated = models.DateTimeField(null=True, blank=True)
    next_generation = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        app_label = "accounting"
        ordering = ["next_generation"]


# Audit and Control Models


class AccountingAuditLog(TenantModel):
    """Detailed audit log for all accounting transactions"""

    ACTION_TYPES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("APPROVE", "Approve"),
        ("REJECT", "Reject"),
        ("REVERSE", "Reverse"),
        ("RECONCILE", "Reconcile"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )  # noqa: E501
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    table_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "accounting"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["table_name", "record_id"]),
            models.Index(fields=["user", "timestamp"]),
        ]


# Import/Export Models


class ImportBatch(TenantModel):
    """Track bulk imports"""

    IMPORT_TYPES = [
        ("BANK_STATEMENT", "Bank Statement"),
        ("EXPENSES", "Expenses"),
        ("ASSETS", "Assets"),
        ("VENDORS", "Vendors"),
        ("CUSTOMERS", "Customers"),
    ]

    import_type = models.CharField(max_length=32, choices=IMPORT_TYPES)
    file_name = models.CharField(max_length=255)
    total_records = models.IntegerField(default=0)
    successful_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    import_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("PROCESSING", "Processing"),
            ("COMPLETED", "Completed"),
            ("FAILED", "Failed"),
        ],
        default="PENDING",
    )
    error_log = models.TextField(blank=True)

    imported_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        app_label = "accounting"
        ordering = ["-created_at"]


class ExportLog(TenantModel):
    """Track data exports"""

    EXPORT_TYPES = [
        ("EXCEL", "Excel Export"),
        ("CSV", "CSV Export"),
        ("TALLY_XML", "Tally XML"),
        ("GST_JSON", "GST JSON"),
        ("ITR_EXCEL", "ITR Excel"),
    ]

    export_type = models.CharField(max_length=32, choices=EXPORT_TYPES)
    report_name = models.CharField(max_length=255)
    filters_applied = models.JSONField(default=dict)
    file_path = models.CharField(max_length=500)
    file_size_bytes = models.BigIntegerField(default=0)

    exported_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        app_label = "accounting"
        ordering = ["-created_at"]
