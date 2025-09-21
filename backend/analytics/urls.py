from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    AnomalyViewSet,
    EquipmentPredictionViewSet,
    OverviewStatsView,
    PredictionViewSet,
    ReadmissionPredictionView,
)

router = DefaultRouter()
router.register(r"predictions", PredictionViewSet)
router.register(r"anomalies", AnomalyViewSet)
router.register(r"equipment-predictions", EquipmentPredictionViewSet)
urlpatterns = [
    path("analytics/overview/", OverviewStatsView.as_view(), name="analytics-overview"),
    path(
        "analytics/readmission/",
        ReadmissionPredictionView.as_view(),
        name="readmission-prediction",
    ),
    path("analytics/", include(router.urls)),
]
