"""Insurance TPA API URL Configuration with Versioning"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# API Versioning - using URL prefix
API_VERSION = "v1"
app_name = f"insurance_tpa_{API_VERSION}"

urlpatterns = [
    # Health check endpoint
    path(f"{API_VERSION}/health/", views.api_health_check, name="api-health"),
    # PreAuth endpoints
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
    # Claim endpoints
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
    # Reimbursement endpoints
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

# To include in main urls.py:
# from django.urls import path, include
# urlpatterns += [
#     path('api/', include('app.urls')),
# ]

# Note: Mock TPA endpoints are handled separately in mock_tpa.py Flask service
# Example usage in main urls.py:
#
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
#
# router = DefaultRouter()
# # router.register(r'v1/insurance', InsuranceViewSet)  # If using ViewSets
#
# urlpatterns = [
#     path('api/', include(router.urls)),
#     path('api/', include('app.urls')),
# ]
