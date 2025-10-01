from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    
    # Monitoring and metrics
    path("metrics/", include("django_prometheus.urls")),
    
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    
    # Authentication & Authorization
    path("api/auth/", include("authentication.urls")),
    
    # Core Management
    path("api/", include("users.urls")),
    path("api/", include("hospitals.urls")),
    path("api/", include("patients.urls")),
    
    # Clinical Modules
    path("api/", include("appointments.urls")),
    path("api/", include("ehr.urls")),
    path("api/", include("pharmacy.urls")),
    path("api/", include("lab.urls")),
    
    # Financial Modules
    path("api/", include("billing.urls")),
    path("api/", include("accounting.urls")),
    # path("api/", include("accounting_advanced.urls")),  # Enable when ready
    
    # Support Modules
    path("api/", include("feedback.urls")),
    path("api/", include("analytics.urls")),
    path("api/", include("hr.urls")),
    path("api/", include("facilities.urls")),
    
    # Administrative
    path("", include("superadmin.urls")),
    
    # AI/ML (when implemented)
    # path("api/ai/", include("ai_ml.urls")),
    
    # Core utilities (when dependencies resolved)
    # path("", include("core.urls")),
] + (
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if settings.DEBUG
    else []
)
