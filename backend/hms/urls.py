from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # path("admin/", admin.site.urls),  # Admin has issues with missing models
    path("metrics/", include("django_prometheus.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # path("api/", include("patients.urls")),  # App not implemented
    # path("api/", include("hospitals.urls")),  # App not implemented
    path("api/", include("users.urls")),
    # path("api/", include("appointments.urls")),  # Depends on patients
    # path("api/", include("ehr.urls")),  # Depends on patients
    # path("api/", include("pharmacy.urls")),  # App not implemented
    # path("api/", include("lab.urls")),  # App not implemented
    # path("api/", include("billing.urls")),  # App not implemented
    # path("api/", include("accounting.urls")),  # App not implemented
    # path("api/", include("accounting_advanced.urls")),  # May have dependencies
    # path("api/", include("feedback.urls")),  # App not implemented
    # path("api/", include("analytics.urls")),  # App not implemented
    # path("api/", include("hr.urls")),  # May have dependencies
    # path("api/", include("facilities.urls")),  # App not implemented
    # path("api/", include("superadmin.urls")),  # May have dependencies
    # path("api/", include("authentication.urls")),  # May have dependencies
    # path("api/", include("ai_ml.urls")),  # May have dependencies
    # path("", include("core.urls")),  # Missing dependencies
] + (
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if settings.DEBUG
    else []
)
