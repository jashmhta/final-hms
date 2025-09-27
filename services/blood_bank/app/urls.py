from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.urls import include, path, re_path

from . import views

router = DefaultRouter()
router.register(r"donors", views.DonorViewSet, basename="donor")
router.register(r"inventory", views.BloodInventoryViewSet, basename="bloodinventory")
router.register(
    r"transfusion", views.TransfusionRecordViewSet, basename="transfusionrecord"
)
router.register(r"crossmatch", views.CrossmatchViewSet, basename="crossmatch")
api_urls = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("donors/", include(router.urls)),
    path("inventory/", include(router.urls)),
    path("transfusion/", include(router.urls)),
    path("crossmatch/", include(router.urls)),
]
urlpatterns = [
    re_path(r"^api/(?P<version>[v1]+)/", include(api_urls)),
    path("api/", include(api_urls)),
]
urlpatterns += [
    path("api/blood-bank/donors/", include(router.urls)),
    path("api/blood-bank/inventory/", include(router.urls)),
    path("api/blood-bank/crossmatch/", include(router.urls)),
]
urlpatterns += [
    path(
        "health/",
        lambda request: {"status": "healthy", "service": "blood-bank-api"},
        name="health_check",
    ),
]
app_name = "blood_bank"
