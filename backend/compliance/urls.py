from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'consents', views.ConsentManagementViewSet, basename='consent')
router.register(r'data-subject-requests', views.DataSubjectRequestViewSet, basename='data-subject-request')

app_name = 'compliance'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),

    # MFA endpoints
    path('api/mfa/', views.MultiFactorAuthenticationView.as_view(), name='mfa'),

    # Compliance dashboard
    path('api/dashboard/', views.ComplianceDashboardView.as_view(), name='compliance-dashboard'),

    # Data retention
    path('api/data-retention/', views.DataRetentionView.as_view(), name='data-retention'),

    # Compliance reports
    path('api/reports/', views.ComplianceReportView.as_view(), name='compliance-reports'),

    # Compliance documentation
    path('docs/', include([
        path('hipaa/', views.HIPAADocumentationView.as_view(), name='hipaa-docs'),
        path('gdpr/', views.GDPRDocumentationView.as_view(), name='gdpr-docs'),
    ])),
]