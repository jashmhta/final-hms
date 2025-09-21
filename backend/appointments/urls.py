from rest_framework.routers import DefaultRouter

from .views import (
    AppointmentHistoryViewSet,
    AppointmentReminderViewSet,
    AppointmentTemplateViewSet,
    AppointmentViewSet,
    ResourceViewSet,
    WaitListViewSet,
)

router = DefaultRouter()
router.register(r"appointments", AppointmentViewSet, basename="appointment")
router.register(r"appointment-templates", AppointmentTemplateViewSet, basename="appointmenttemplate")
router.register(r"resources", ResourceViewSet, basename="resource")
router.register(r"waitlist", WaitListViewSet, basename="waitlist")
router.register(r"appointment-reminders", AppointmentReminderViewSet, basename="appointmentreminder")
router.register(r"appointment-history", AppointmentHistoryViewSet, basename="appointmenthistory")
urlpatterns = router.urls
