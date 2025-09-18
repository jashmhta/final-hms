from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views
API_VERSION = "v1"
app_name = f"insurance_tpa_{API_VERSION}"
urlpatterns = [
    path(f"{API_VERSION}/health/", views.api_health_check, name="api-health"),
    path(
        f"{API_VERSION}/insurance/pre-auth/",
        views.PreAuthListView.as_view(),
        name="preauth-list",
    ),
    path(
        f"{API_VERSION}/insurance/pre-auth/create/",
        views.PreAuthCreateView.as_view(),
        name="preauth-create",
    ),
    path(
        f"{API_VERSION}/insurance/pre-auth/<int:pk>/",
        views.PreAuthRetrieveUpdateDestroyView.as_view(),
        name="preauth-detail",
    ),
    path(
        f"{API_VERSION}/insurance/claims/",
        views.ClaimListView.as_view(),
        name="claim-list",
    ),
    path(
        f"{API_VERSION}/insurance/claims/create/",
        views.ClaimCreateView.as_view(),
        name="claim-create",
    ),
    path(
        f"{API_VERSION}/insurance/claims/<int:pk>/",
        views.ClaimRetrieveView.as_view(),
        name="claim-detail",
    ),
    path(
        f"{API_VERSION}/insurance/claims/<int:claim_id>/status/",
        views.claim_status,
        name="claim-status",
    ),
    path(
        f"{API_VERSION}/insurance/reimbursement/",
        views.ReimbursementListView.as_view(),
        name="reimbursement-list",
    ),
    path(
        f"{API_VERSION}/insurance/reimbursement/create/",
        views.ReimbursementCreateView.as_view(),
        name="reimbursement-create",
    ),
]