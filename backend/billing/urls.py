from rest_framework.routers import DefaultRouter

from .views import (
    AccountingViewSet,
    BillLineItemViewSet,
    BillViewSet,
    DepartmentBudgetViewSet,
    PaymentViewSet,
    ServiceCatalogViewSet,
)

router = DefaultRouter()
router.register(r"bills", BillViewSet, basename="bill")
router.register(r"bill-items", BillLineItemViewSet, basename="billitem")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"services", ServiceCatalogViewSet, basename="service")
router.register(r"accounting", AccountingViewSet, basename="accounting")
router.register(r"budgets", DepartmentBudgetViewSet, basename="budget")
urlpatterns = router.urls
