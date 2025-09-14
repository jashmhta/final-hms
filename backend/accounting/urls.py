"""
URL configuration for accounting module.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountingAuditLogViewSet,
    AccountingInvoiceViewSet,
    AccountingPaymentViewSet,
    BankAccountViewSet,
    BankTransactionViewSet,
    BookLockViewSet,
    BudgetViewSet,
    ChartOfAccountsViewSet,
    ComplianceDocumentViewSet,
    CostCenterViewSet,
    CurrencyViewSet,
    CustomerViewSet,
    DashboardAPIView,
    DepreciationProcessingAPIView,
    ExpenseViewSet,
    ExportAPIView,
    FinancialYearViewSet,
    FixedAssetViewSet,
    InsuranceClaimViewSet,
    LedgerEntryViewSet,
    PayrollEntryViewSet,
    PricingTierViewSet,
    RecurringInvoiceViewSet,
    ReportsAPIView,
    ServicePackageViewSet,
    TaxConfigurationViewSet,
    TaxLiabilityAPIView,
    TDSEntryViewSet,
    VendorPayoutViewSet,
    VendorViewSet,
)

# Create router and register viewsets
router = DefaultRouter()

# Configuration
router.register(r"currencies", CurrencyViewSet, basename="currency")
router.register(
<<<<<<< HEAD
    r"tax-configurations", TaxConfigurationViewSet, basename="tax-configuration"
=======
    r"tax-configurations",
    TaxConfigurationViewSet,
    basename="tax-configuration",
>>>>>>> transform-refactor
)
router.register(
    r"chart-of-accounts", ChartOfAccountsViewSet, basename="chart-of-accounts"
)
router.register(r"cost-centers", CostCenterViewSet, basename="cost-center")

# Master Data
router.register(r"vendors", VendorViewSet, basename="vendor")
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"service-packages", ServicePackageViewSet, basename="service-package")
<<<<<<< HEAD
=======
# noqa: E501
# noqa: E501
>>>>>>> transform-refactor
router.register(r"pricing-tiers", PricingTierViewSet, basename="pricing-tier")

# Transactions
router.register(r"invoices", AccountingInvoiceViewSet, basename="invoice")
router.register(r"payments", AccountingPaymentViewSet, basename="payment")
router.register(r"expenses", ExpenseViewSet, basename="expense")

# Banking
router.register(r"bank-accounts", BankAccountViewSet, basename="bank-account")
router.register(
    r"bank-transactions", BankTransactionViewSet, basename="bank-transaction"
)

# Assets and Depreciation
router.register(r"fixed-assets", FixedAssetViewSet, basename="fixed-asset")

# Payroll
router.register(r"payroll-entries", PayrollEntryViewSet, basename="payroll-entry")
<<<<<<< HEAD

# Insurance and Claims
router.register(r"insurance-claims", InsuranceClaimViewSet, basename="insurance-claim")
=======
# noqa: E501
# noqa: E501

# Insurance and Claims
router.register(r"insurance-claims", InsuranceClaimViewSet, basename="insurance-claim")
# noqa: E501
# noqa: E501
>>>>>>> transform-refactor

# Compliance
router.register(r"tds-entries", TDSEntryViewSet, basename="tds-entry")
router.register(r"book-locks", BookLockViewSet, basename="book-lock")
router.register(
<<<<<<< HEAD
    r"compliance-documents", ComplianceDocumentViewSet, basename="compliance-document"
=======
    r"compliance-documents",
    ComplianceDocumentViewSet,
    basename="compliance-document",
>>>>>>> transform-refactor
)

# Vendor Management
router.register(r"vendor-payouts", VendorPayoutViewSet, basename="vendor-payout")
<<<<<<< HEAD

# Planning and Budgeting
router.register(r"financial-years", FinancialYearViewSet, basename="financial-year")
router.register(r"budgets", BudgetViewSet, basename="budget")
router.register(
    r"recurring-invoices", RecurringInvoiceViewSet, basename="recurring-invoice"
=======
# noqa: E501
# noqa: E501

# Planning and Budgeting
router.register(r"financial-years", FinancialYearViewSet, basename="financial-year")
# noqa: E501
# noqa: E501
router.register(r"budgets", BudgetViewSet, basename="budget")
router.register(
    r"recurring-invoices",
    RecurringInvoiceViewSet,
    basename="recurring-invoice",
>>>>>>> transform-refactor
)

# Audit and Reporting
router.register(r"ledger-entries", LedgerEntryViewSet, basename="ledger-entry")
router.register(r"audit-logs", AccountingAuditLogViewSet, basename="audit-log")

# API endpoints
urlpatterns = [
    path("", include(router.urls)),
    # Reports
    path("reports/", ReportsAPIView.as_view(), name="reports"),
    path("dashboard/", DashboardAPIView.as_view(), name="dashboard"),
    path("export/", ExportAPIView.as_view(), name="export"),
    # Utility endpoints
    path(
        "utilities/process-depreciation/",
        DepreciationProcessingAPIView.as_view(),
        name="process-depreciation",
    ),
    path(
        "utilities/calculate-tax-liability/",
        TaxLiabilityAPIView.as_view(),
        name="calculate-tax-liability",
    ),
]
