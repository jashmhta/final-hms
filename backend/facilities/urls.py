from rest_framework.routers import DefaultRouter

from .views import BedViewSet, WardViewSet

router = DefaultRouter()
router.register(r"wards", WardViewSet, basename="ward")
router.register(r"beds", BedViewSet, basename="bed")
urlpatterns = router.urls
