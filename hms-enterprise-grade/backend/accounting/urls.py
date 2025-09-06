"""
URL configuration for accounting module.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CurrencyViewSet, TaxConfigurationViewSet, ChartOfAccountsViewSet,
    CostCenterViewSet, VendorViewSet, CustomerViewSet, ServicePackageViewSet,
    PricingTierViewSet, AccountingInvoiceViewSet, AccountingPaymentViewSet,
    ExpenseViewSet, BankAccountViewSet, BankTransactionViewSet,
    FixedAssetViewSet, PayrollEntryViewSet, InsuranceClaimViewSet,
    TDSEntryViewSet, BookLockViewSet, VendorPayoutViewSet,
    RecurringInvoiceViewSet, ComplianceDocumentViewSet, FinancialYearViewSet,
    BudgetViewSet, LedgerEntryViewSet, AccountingAuditLogViewSet,
    ReportsAPIView, DashboardAPIView, ExportAPIView,
    DepreciationProcessingAPIView, TaxLiabilityAPIView
)

# Create router and register viewsets
router = DefaultRouter()

# Configuration
router.register(r'currencies', CurrencyViewSet, basename='currency')
router.register(r'tax-configurations', TaxConfigurationViewSet, basename='tax-configuration')
router.register(r'chart-of-accounts', ChartOfAccountsViewSet, basename='chart-of-accounts')
router.register(r'cost-centers', CostCenterViewSet, basename='cost-center')

# Master Data
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'service-packages', ServicePackageViewSet, basename='service-package')
router.register(r'pricing-tiers', PricingTierViewSet, basename='pricing-tier')

# Transactions
router.register(r'invoices', AccountingInvoiceViewSet, basename='invoice')
router.register(r'payments', AccountingPaymentViewSet, basename='payment')
router.register(r'expenses', ExpenseViewSet, basename='expense')

# Banking
router.register(r'bank-accounts', BankAccountViewSet, basename='bank-account')
router.register(r'bank-transactions', BankTransactionViewSet, basename='bank-transaction')

# Assets and Depreciation
router.register(r'fixed-assets', FixedAssetViewSet, basename='fixed-asset')

# Payroll
router.register(r'payroll-entries', PayrollEntryViewSet, basename='payroll-entry')

# Insurance and Claims
router.register(r'insurance-claims', InsuranceClaimViewSet, basename='insurance-claim')

# Compliance
router.register(r'tds-entries', TDSEntryViewSet, basename='tds-entry')
router.register(r'book-locks', BookLockViewSet, basename='book-lock')
router.register(r'compliance-documents', ComplianceDocumentViewSet, basename='compliance-document')

# Vendor Management
router.register(r'vendor-payouts', VendorPayoutViewSet, basename='vendor-payout')

# Planning and Budgeting
router.register(r'financial-years', FinancialYearViewSet, basename='financial-year')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'recurring-invoices', RecurringInvoiceViewSet, basename='recurring-invoice')

# Audit and Reporting
router.register(r'ledger-entries', LedgerEntryViewSet, basename='ledger-entry')
router.register(r'audit-logs', AccountingAuditLogViewSet, basename='audit-log')

# API endpoints
urlpatterns = [
    path('', include(router.urls)),
    
    # Reports
    path('reports/', ReportsAPIView.as_view(), name='reports'),
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    path('export/', ExportAPIView.as_view(), name='export'),
    
    # Utility endpoints
    path('utilities/process-depreciation/', DepreciationProcessingAPIView.as_view(), name='process-depreciation'),
    path('utilities/calculate-tax-liability/', TaxLiabilityAPIView.as_view(), name='calculate-tax-liability'),
]
