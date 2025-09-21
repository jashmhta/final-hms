from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from hospitals.models import Hospital
from users.models import UserRole

from .models import (
    AccountingInvoice,
    AccountingPayment,
    AccountType,
    ChartOfAccounts,
    CostCenter,
    Currency,
    Customer,
    Expense,
    FixedAsset,
    InvoiceLineItem,
    LedgerEntry,
    PayrollEntry,
    Vendor,
)
from .utils import DepreciationCalculator, DoubleEntryBookkeeping, ReportGenerator

User = get_user_model()


class AccountingModuleTestCase(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name="Test Hospital",
            address="Test Address",
            phone="1234567890",
            email="test@hospital.com",
        )
        self.user = User.objects.create_user(
            username="testadmin",
            email="admin@test.com",
            password="secure_test_password",
            role=UserRole.HOSPITAL_ADMIN,
            hospital=self.hospital,
        )
        self.currency = Currency.objects.create(
            hospital=self.hospital,
            code="INR",
            name="Indian Rupee",
            symbol="₹",
            is_base_currency=True,
        )
        self.cash_account = ChartOfAccounts.objects.create(
            hospital=self.hospital,
            account_code="1100",
            account_name="Cash in Hand",
            account_type=AccountType.ASSETS,
            account_subtype="CURRENT_ASSETS",
        )
        self.revenue_account = ChartOfAccounts.objects.create(
            hospital=self.hospital,
            account_code="4100",
            account_name="Patient Services Revenue",
            account_type=AccountType.INCOME,
            account_subtype="OPERATING_INCOME",
        )
        self.receivables_account = ChartOfAccounts.objects.create(
            hospital=self.hospital,
            account_code="1200",
            account_name="Accounts Receivable",
            account_type=AccountType.ASSETS,
            account_subtype="CURRENT_ASSETS",
        )
        self.cost_center = CostCenter.objects.create(
            hospital=self.hospital,
            code="OPD",
            name="Out Patient Department",
            manager=self.user,
        )


class CurrencyModelTest(AccountingModuleTestCase):
    def test_currency_creation(self):
        currency = Currency.objects.create(
            hospital=self.hospital,
            code="USD",
            name="US Dollar",
            symbol="$",
            exchange_rate=Decimal("83.50"),
        )
        self.assertEqual(currency.code, "USD")
        self.assertEqual(currency.exchange_rate, Decimal("83.50"))
        self.assertFalse(currency.is_base_currency)


class ChartOfAccountsTest(AccountingModuleTestCase):
    def test_account_balance_calculation(self):
        LedgerEntry.objects.create(
            hospital=self.hospital,
            transaction_date=timezone.now().date(),
            reference_number="TEST001",
            description="Test entry",
            debit_account=self.cash_account,
            credit_account=self.revenue_account,
            amount_cents=10000,
            currency=self.currency,
            created_by=self.user,
        )
        self.assertEqual(self.cash_account.balance, 10000)
        self.assertEqual(self.revenue_account.balance, 10000)


class InvoiceTest(AccountingModuleTestCase):
    def setUp(self):
        super().setUp()
        self.customer = Customer.objects.create(
            hospital=self.hospital,
            customer_code="CUST001",
            name="Test Customer",
            customer_type="CORPORATE",
        )

    def test_invoice_number_generation(self):
        invoice = AccountingInvoice.objects.create(
            hospital=self.hospital,
            invoice_type="CORPORATE",
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date(),
            customer=self.customer,
            currency=self.currency,
            created_by=self.user,
        )
        current_year = timezone.now().year
        expected_prefix = f"INV-{current_year}-"
        self.assertTrue(invoice.invoice_number.startswith(expected_prefix))

    def test_invoice_calculation(self):
        invoice = AccountingInvoice.objects.create(
            hospital=self.hospital,
            invoice_type="CORPORATE",
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date(),
            customer=self.customer,
            currency=self.currency,
            created_by=self.user,
        )
        item1 = InvoiceLineItem.objects.create(
            hospital=self.hospital,
            invoice=invoice,
            description="Consultation",
            quantity=1,
            unit_price_cents=50000,
            cgst_rate=Decimal("9.00"),
            sgst_rate=Decimal("9.00"),
        )
        item2 = InvoiceLineItem.objects.create(
            hospital=self.hospital,
            invoice=invoice,
            description="Lab Test",
            quantity=2,
            unit_price_cents=100000,
            cgst_rate=Decimal("9.00"),
            sgst_rate=Decimal("9.00"),
        )
        invoice.calculate_totals()
        expected_subtotal = 50000 + (2 * 100000)
        expected_tax = int(expected_subtotal * 0.18)
        expected_total = expected_subtotal + expected_tax
        self.assertEqual(invoice.subtotal_cents, expected_subtotal)
        self.assertEqual(invoice.tax_cents, expected_tax)
        self.assertEqual(invoice.total_cents, expected_total)


class PaymentTest(AccountingModuleTestCase):
    def setUp(self):
        super().setUp()
        self.customer = Customer.objects.create(
            hospital=self.hospital,
            customer_code="CUST001",
            name="Test Customer",
        )
        self.invoice = AccountingInvoice.objects.create(
            hospital=self.hospital,
            invoice_type="CORPORATE",
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date(),
            customer=self.customer,
            currency=self.currency,
            total_cents=100000,
            created_by=self.user,
        )

    def test_payment_updates_invoice(self):
        payment = AccountingPayment.objects.create(
            hospital=self.hospital,
            payment_date=timezone.now().date(),
            invoice=self.invoice,
            amount_cents=100000,
            currency=self.currency,
            payment_method="CASH",
            received_by=self.user,
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.paid_cents, 100000)
        self.assertEqual(self.invoice.status, "PAID")


class DepreciationTest(AccountingModuleTestCase):
    def setUp(self):
        super().setUp()
        self.vendor = Vendor.objects.create(
            hospital=self.hospital,
            vendor_code="VEN001",
            name="Equipment Vendor",
        )

    def test_straight_line_depreciation(self):
        asset = FixedAsset.objects.create(
            hospital=self.hospital,
            asset_code="MED001",
            name="MRI Machine",
            category="MEDICAL_EQUIPMENT",
            cost_center=self.cost_center,
            purchase_date=timezone.now().date(),
            purchase_cost_cents=500000000,
            vendor=self.vendor,
            depreciation_method="STRAIGHT_LINE",
            useful_life_years=10,
            salvage_value_cents=5000000,
            current_book_value_cents=500000000,
        )
        annual_depreciation = asset.calculate_annual_depreciation()
        expected_annual = (500000000 - 5000000) // 10
        self.assertEqual(annual_depreciation, expected_annual)
        monthly_depreciation = DepreciationCalculator.calculate_monthly_depreciation(asset)
        expected_monthly = expected_annual // 12
        self.assertEqual(monthly_depreciation, expected_monthly)


class DoubleEntryBookkeepingTest(AccountingModuleTestCase):
    def test_journal_entry_creation(self):
        entry = DoubleEntryBookkeeping.create_journal_entry(
            hospital=self.hospital,
            debit_account_code="1100",
            credit_account_code="4100",
            amount_cents=100000,
            description="Test transaction",
            reference_number="TEST001",
            created_by=self.user,
        )
        self.assertEqual(entry.debit_account, self.cash_account)
        self.assertEqual(entry.credit_account, self.revenue_account)
        self.assertEqual(entry.amount_cents, 100000)


class ReportGenerationTest(AccountingModuleTestCase):
    def setUp(self):
        super().setUp()
        LedgerEntry.objects.create(
            hospital=self.hospital,
            transaction_date=timezone.now().date(),
            reference_number="TEST001",
            description="Test revenue",
            debit_account=self.receivables_account,
            credit_account=self.revenue_account,
            amount_cents=100000,
            currency=self.currency,
            created_by=self.user,
        )

    def test_trial_balance_generation(self):
        trial_balance = ReportGenerator.generate_trial_balance(self.hospital, timezone.now().date())
        self.assertIn("accounts", trial_balance)
        self.assertIn("total_debits", trial_balance)
        self.assertIn("total_credits", trial_balance)
        self.assertTrue(trial_balance["is_balanced"])


class ExpenseTest(AccountingModuleTestCase):
    def setUp(self):
        super().setUp()
        self.vendor = Vendor.objects.create(
            hospital=self.hospital,
            vendor_code="VEN001",
            name="Test Vendor",
            tds_rate=Decimal("10.00"),
        )

    def test_expense_creation(self):
        expense = Expense.objects.create(
            hospital=self.hospital,
            expense_date=timezone.now().date(),
            vendor=self.vendor,
            cost_center=self.cost_center,
            category="UTILITIES",
            description="Electricity Bill",
            amount_cents=50000,
            currency=self.currency,
            tax_cents=9000,
            tds_cents=5000,
            created_by=self.user,
        )
        expected_net = 50000 + 9000 - 5000
        self.assertEqual(expense.net_amount_cents, expected_net)
        current_year = timezone.now().year
        expected_prefix = f"EXP-{current_year}-"
        self.assertTrue(expense.expense_number.startswith(expected_prefix))


class PayrollTest(AccountingModuleTestCase):
    def setUp(self):
        super().setUp()
        self.employee = User.objects.create_user(
            username="testdoc",
            email="doc@test.com",
            password="secure_test_password",
            role=UserRole.ATTENDING_PHYSICIAN,
            hospital=self.hospital,
        )

    def test_payroll_calculations(self):
        payroll = PayrollEntry.objects.create(
            hospital=self.hospital,
            employee=self.employee,
            pay_period_start=timezone.now().date().replace(day=1),
            pay_period_end=timezone.now().date(),
            pay_date=timezone.now().date(),
            basic_salary_cents=5000000,
            hra_cents=2000000,
            medical_allowance_cents=125000,
            pf_employee_cents=600000,
            pf_employer_cents=600000,
            esi_employee_cents=52500,
            esi_employer_cents=315000,
            status="DRAFT",
            cost_center=self.cost_center,
            created_by=self.user,
        )
        expected_gross = 5000000 + 2000000 + 125000
        expected_deductions = 600000 + 52500
        expected_net = expected_gross - expected_deductions
        expected_employer_cost = expected_gross + 600000 + 315000
        self.assertEqual(payroll.gross_salary_cents, expected_gross)
        self.assertEqual(payroll.total_deductions_cents, expected_deductions)
        self.assertEqual(payroll.net_salary_cents, expected_net)
        self.assertEqual(payroll.employer_cost_cents, expected_employer_cost)
