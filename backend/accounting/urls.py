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
router = DefaultRouter()
router.register(r"currencies", CurrencyViewSet, basename="currency")
router.register(
    r"tax-configurations",
    TaxConfigurationViewSet,
    basename="tax-configuration",
)
router.register(
    r"chart-of-accounts", ChartOfAccountsViewSet, basename="chart-of-accounts"
)
router.register(r"cost-centers", CostCenterViewSet, basename="cost-center")
router.register(r"vendors", VendorViewSet, basename="vendor")
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"service-packages", ServicePackageViewSet, basename="service-package")
router.register(r"pricing-tiers", PricingTierViewSet, basename="pricing-tier")
router.register(r"invoices", AccountingInvoiceViewSet, basename="invoice")
router.register(r"payments", AccountingPaymentViewSet, basename="payment")
router.register(r"expenses", ExpenseViewSet, basename="expense")
router.register(r"bank-accounts", BankAccountViewSet, basename="bank-account")
router.register(
    r"bank-transactions", BankTransactionViewSet, basename="bank-transaction"
)
router.register(r"fixed-assets", FixedAssetViewSet, basename="fixed-asset")
router.register(r"payroll-entries", PayrollEntryViewSet, basename="payroll-entry")
router.register(r"insurance-claims", InsuranceClaimViewSet, basename="insurance-claim")
router.register(r"tds-entries", TDSEntryViewSet, basename="tds-entry")
router.register(r"book-locks", BookLockViewSet, basename="book-lock")
router.register(
    r"compliance-documents",
    ComplianceDocumentViewSet,
    basename="compliance-document",
)
router.register(r"vendor-payouts", VendorPayoutViewSet, basename="vendor-payout")
router.register(r"financial-years", FinancialYearViewSet, basename="financial-year")
router.register(r"budgets", BudgetViewSet, basename="budget")
router.register(
    r"recurring-invoices",
    RecurringInvoiceViewSet,
    basename="recurring-invoice",
)
router.register(r"ledger-entries", LedgerEntryViewSet, basename="ledger-entry")
router.register(r"audit-logs", AccountingAuditLogViewSet, basename="audit-log")
urlpatterns = [
    path("", include(router.urls)),
    path("reports/", ReportsAPIView.as_view(), name="reports"),
    path("dashboard/", DashboardAPIView.as_view(), name="dashboard"),
    path("export/", ExportAPIView.as_view(), name="export"),
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