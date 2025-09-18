from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
urlpatterns = [
    path("admin/", admin.site.urls),
    path("metrics/", include("django_prometheus.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/", include("patients.urls")),
    path("api/", include("hospitals.urls")),
    path("api/", include("users.urls")),
    path("api/", include("appointments.urls")),
    path("api/", include("ehr.urls")),
    path("api/", include("pharmacy.urls")),
    path("api/", include("lab.urls")),
    path("api/", include("billing.urls")),
    path("api/", include("accounting.urls")),
    path("api/", include("accounting_advanced.urls")),
    path("api/", include("feedback.urls")),
    path("api/", include("analytics.urls")),
    path("api/", include("hr.urls")),
    path("api/", include("facilities.urls")),
    path("api/", include("superadmin.urls")),
    path("api/", include("authentication.urls")),
    path("api/", include("ai_ml.urls")),
    path("", include("core.urls")),
] + (
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if settings.DEBUG
    else []
)