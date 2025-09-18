from rest_framework.routers import DefaultRouter
from .views import InventoryTransactionViewSet, MedicationViewSet, PrescriptionViewSet
router = DefaultRouter()
router.register(r"medications", MedicationViewSet, basename="medication")
router.register(r"prescriptions", PrescriptionViewSet, basename="prescription")
router.register(
    r"inventory-transactions",
    InventoryTransactionViewSet,
    basename="inventorytransaction",
)
urlpatterns = router.urls