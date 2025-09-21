from rest_framework.routers import DefaultRouter

from .views import DutyRosterViewSet, LeaveRequestViewSet, ShiftViewSet

router = DefaultRouter()
router.register(r"hr/shifts", ShiftViewSet, basename="hr-shift")
router.register(r"hr/roster", DutyRosterViewSet, basename="hr-roster")
router.register(r"hr/leaves", LeaveRequestViewSet, basename="hr-leave")
urlpatterns = router.urls
