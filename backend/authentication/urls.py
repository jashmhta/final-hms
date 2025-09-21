from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from django.urls import include, path

from .views import (
    CustomTokenObtainPairView,
    LogoutView,
    MFAAuthenticationView,
    MFASetupViewSet,
    PasswordChangeView,
    SecurityEventViewSet,
    SessionManagementView,
    TrustedDeviceViewSet,
)

router = DefaultRouter()
router.register(r"mfa-setup", MFASetupViewSet, basename="mfa-setup")
router.register(r"trusted-devices", TrustedDeviceViewSet, basename="trusted-devices")
router.register(r"security-events", SecurityEventViewSet, basename="security-events")
urlpatterns = [
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("login/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("mfa/verify/", MFAAuthenticationView.as_view(), name="mfa_verify"),
    path("password/change/", PasswordChangeView.as_view(), name="password_change"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("sessions/", SessionManagementView.as_view(), name="session_management"),
    path("", include(router.urls)),
]
