from django.urls import path

from .views import OverviewStatsView

urlpatterns = [
    path("analytics/overview/", OverviewStatsView.as_view(), name="analytics-overview"),
]
