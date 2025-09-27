from django.urls import path

from .monitoring_views import HealthCheckView as EnhancedHealthCheckView
from .monitoring_views import MetricsView, MonitoringViewSet
from .views import HealthCheckView, root_api_view

urlpatterns = [
    path("", root_api_view, name="root"),
    path("health/", HealthCheckView.as_view(), name="health"),
    path("health/detailed/", EnhancedHealthCheckView.as_view(), name="health_detailed"),
    path("metrics/", MetricsView.as_view(), name="metrics"),
    path(
        "monitoring/",
        MonitoringViewSet.as_view({"get": "list"}),
        name="monitoring_list",
    ),
    path(
        "monitoring/system-health/",
        MonitoringViewSet.as_view({"get": "system_health"}),
        name="system_health",
    ),
    path(
        "monitoring/performance/",
        MonitoringViewSet.as_view({"get": "performance_metrics"}),
        name="performance_metrics",
    ),
    path(
        "monitoring/audit-logs/",
        MonitoringViewSet.as_view({"get": "audit_logs"}),
        name="audit_logs",
    ),
    path(
        "monitoring/error-analysis/",
        MonitoringViewSet.as_view({"get": "error_analysis"}),
        name="error_analysis",
    ),
    path(
        "monitoring/run-diagnostics/",
        MonitoringViewSet.as_view({"post": "run_diagnostics"}),
        name="run_diagnostics",
    ),
]
