from rest_framework.routers import DefaultRouter
from .views import EncounterAttachmentViewSet, EncounterNoteViewSet, EncounterViewSet
router = DefaultRouter()
router.register(r"encounters", EncounterViewSet, basename="encounter")
router.register(r"encounter-notes", EncounterNoteViewSet, basename="encounternote")
router.register(
    r"encounter-attachments",
    EncounterAttachmentViewSet,
    basename="encounterattachment",
)
urlpatterns = router.urls