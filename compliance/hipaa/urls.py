from django.urls import path

from . import views

app_name = "hipaa_compliance"

urlpatterns = [
    # Patient Consent Management
    path("consent/", views.patient_consent_list, name="patient_consent_list"),
    path(
        "consent/create/", views.create_patient_consent, name="create_patient_consent"
    ),
    path(
        "consent/<int:consent_id>/revoke/", views.revoke_consent, name="revoke_consent"
    ),
    # Audit Log Viewing (Admin/Staff only)
    path("audit-logs/", views.audit_log_view, name="audit_log_view"),
    # Breach Notification Endpoints
    path("breach/report/", views.report_breach, name="report_breach"),
    path(
        "breach/<int:breach_id>/notify/",
        views.send_breach_notification,
        name="send_breach_notification",
    ),
    # HIPAA Compliance APIs
    path(
        "api/consent/validate/", views.validate_consent_api, name="validate_consent_api"
    ),
    path("api/encryption/test/", views.test_encryption_api, name="test_encryption_api"),
    path(
        "api/audit/search/", views.search_audit_logs_api, name="search_audit_logs_api"
    ),
    # Compliance Dashboard
    path("dashboard/", views.compliance_dashboard, name="compliance_dashboard"),
    # Legacy Integration Endpoints
    path(
        "legacy/patient-consent/",
        views.legacy_patient_consent,
        name="legacy_patient_consent",
    ),
    path(
        "legacy/phi-access/", views.legacy_phi_access_log, name="legacy_phi_access_log"
    ),
]

# Legacy compatibility endpoints for existing backend integration
legacy_patterns = [
    path("hipaa/consent/", views.patient_consent_list, name="legacy_consent_list"),
    path("hipaa/audit/", views.audit_log_view, name="legacy_audit_view"),
    path("hipaa/breach/", views.report_breach, name="legacy_report_breach"),
]
