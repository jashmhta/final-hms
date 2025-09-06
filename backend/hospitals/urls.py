from rest_framework.routers import DefaultRouter
from .views import HospitalViewSet, PlanViewSet, HospitalPlanViewSet

router = DefaultRouter()
router.register(r'hospitals', HospitalViewSet, basename='hospital')
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'hospital-plans', HospitalPlanViewSet, basename='hospitalplan')

urlpatterns = router.urls