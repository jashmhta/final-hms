from rest_framework.routers import DefaultRouter

from .views import LabOrderViewSet, LabResultViewSet, LabTestViewSet

router = DefaultRouter()
router.register(r"lab-tests", LabTestViewSet, basename="labtest")
router.register(r"lab-orders", LabOrderViewSet, basename="laborder")
router.register(r"lab-results", LabResultViewSet, basename="labresult")

urlpatterns = router.urls
