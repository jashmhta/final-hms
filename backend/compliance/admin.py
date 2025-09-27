from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    ConsentAuditLog,
    ConsentManagement,
    ConsentStatus,
    ConsentType,
    DataRetentionPolicy,
    DataSubjectRequest,
    DataSubjectRequestAudit,
)


@admin.register(ConsentManagement)
class ConsentManagementAdmin(admin.ModelAdmin):
    """
    GDPR Article 7 compliant consent management admin interface
    """

    list_display = [
        "id",
        "patient_name",
        "consent_type",
        "status",
        "version",
        "consent_date",
        "expiry_date",
        "is_valid",
        "created_by",
    ]
    list_filter = [
        "consent_type",
        "status",
        "consent_date",
        "expiry_date",
        "hospital",
        "created_by",
    ]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "patient__medical_record_number",
        "title",
        "description",
    ]
    readonly_fields = ["id", "uuid", "created_at", "updated_at", "revoked_date"]
    date_hierarchy = "consent_date"
    ordering = ["-consent_date"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "patient",
                    "consent_type",
                    "status",
                    "version",
                    "title",
                    "description",
                    "purpose",
                )
            },
        ),
        (
            "Consent Details",
            {
                "fields": (
                    "data_categories",
                    "third_parties",
                    "retention_period",
                    "consent_form_url",
                    "digital_signature_data",
                )
            },
        ),
        (
            "Lifecycle",
            {
                "fields": (
                    "consent_date",
                    "expiry_date",
                    "revoked_date",
                    "withdrawal_method",
                    "is_active",
                )
            },
        ),
        (
            "Witness Information",
            {
                "fields": (
                    "witness_name",
                    "interpreter_used",
                    "interpreter_name",
                    "language_preference",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def patient_name(self, obj):
        return obj.patient.get_full_name()

    patient_name.short_description = _("Patient")
    patient_name.admin_order_field = "patient__last_name"

    def is_valid(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html('<span style="color: red;">✗ Invalid</span>')

    is_valid.short_description = _("Valid")
    is_valid.admin_order_field = "status"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("patient", "hospital", "created_by")
        )

    def has_add_permission(self, request):
        return request.user.has_perm("compliance.add_consentmanagement")

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("compliance.change_consentmanagement")

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm("compliance.delete_consentmanagement")

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("compliance.view_consentmanagement")


@admin.register(ConsentAuditLog)
class ConsentAuditLogAdmin(admin.ModelAdmin):
    """
    Consent audit trail admin interface
    """

    list_display = [
        "id",
        "patient_name",
        "consent_title",
        "action",
        "action_by",
        "action_date",
        "ip_address",
    ]
    list_filter = ["action", "action_date", "hospital", "action_by"]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "consent__title",
        "details",
        "ip_address",
    ]
    readonly_fields = [
        "id",
        "uuid",
        "patient",
        "consent",
        "action",
        "action_by",
        "action_date",
        "ip_address",
        "user_agent",
    ]
    date_hierarchy = "action_date"
    ordering = ["-action_date"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "patient",
                    "consent",
                    "action",
                    "action_by",
                    "action_date",
                    "details",
                )
            },
        ),
        (
            "Technical Details",
            {
                "fields": (
                    "ip_address",
                    "user_agent",
                    "location",
                    "session_id",
                    "device_fingerprint",
                )
            },
        ),
        (
            "Change Tracking",
            {"fields": ("previous_values", "new_values"), "classes": ("collapse",)},
        ),
    )

    def patient_name(self, obj):
        return obj.patient.get_full_name()

    patient_name.short_description = _("Patient")
    patient_name.admin_order_field = "patient__last_name"

    def consent_title(self, obj):
        return obj.consent.title if obj.consent else _("N/A")

    consent_title.short_description = _("Consent")
    consent_title.admin_order_field = "consent__title"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("patient", "consent", "action_by")
        )

    def has_add_permission(self, request):
        return False  # Audit logs cannot be manually added

    def has_change_permission(self, request, obj=None):
        return False  # Audit logs cannot be modified

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm("compliance.delete_consentauditlog")

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("compliance.view_consentauditlog")


@admin.register(DataSubjectRequest)
class DataSubjectRequestAdmin(admin.ModelAdmin):
    """
    GDPR data subject request admin interface
    """

    list_display = [
        "id",
        "patient_name",
        "request_type",
        "status",
        "received_date",
        "due_date",
        "assigned_to",
        "priority",
    ]
    list_filter = [
        "request_type",
        "status",
        "priority",
        "received_date",
        "due_date",
        "assigned_to",
        "hospital",
    ]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "description",
        "response_message",
        "rejection_reason",
    ]
    readonly_fields = ["id", "uuid", "received_date", "due_date", "completed_date"]
    date_hierarchy = "received_date"
    ordering = ["-received_date"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "patient",
                    "request_type",
                    "status",
                    "priority",
                    "description",
                    "scope",
                    "timeframe",
                )
            },
        ),
        (
            "Processing",
            {
                "fields": (
                    "assigned_to",
                    "completed_by",
                    "received_date",
                    "due_date",
                    "completed_date",
                )
            },
        ),
        (
            "Response",
            {"fields": ("response_data", "response_message", "rejection_reason")},
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def patient_name(self, obj):
        return obj.patient.get_full_name()

    patient_name.short_description = _("Patient")
    patient_name.admin_order_field = "patient__last_name"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("patient", "assigned_to", "completed_by", "hospital")
        )

    actions = ["assign_to_compliance_officer", "mark_as_completed"]

    def assign_to_compliance_officer(self, request, queryset):
        """
        Assign selected requests to compliance officers
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()

        compliance_officers = User.objects.filter(
            groups__name="Compliance Officers", is_active=True
        )

        if not compliance_officers.exists():
            self.message_user(
                request,
                _("No compliance officers available for assignment"),
                level="error",
            )
            return

        # Assign to first available compliance officer
        assigned_officer = compliance_officers.first()
        updated_count = queryset.update(
            assigned_to=assigned_officer, status="IN_PROGRESS"
        )

        self.message_user(
            request,
            _(
                f"Assigned {updated_count} requests to {assigned_officer.get_full_name()}"
            ),
            level="success",
        )

    assign_to_compliance_officer.short_description = _("Assign to compliance officer")

    def mark_as_completed(self, request, queryset):
        """
        Mark selected requests as completed
        """
        updated_count = queryset.filter(status__in=["PENDING", "IN_PROGRESS"]).update(
            status="COMPLETED", completed_date=timezone.now(), completed_by=request.user
        )

        self.message_user(
            request, _(f"Marked {updated_count} requests as completed"), level="success"
        )

    mark_as_completed.short_description = _("Mark as completed")

    def has_add_permission(self, request):
        return request.user.has_perm("compliance.add_datasubjectrequest")

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("compliance.change_datasubjectrequest")

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm("compliance.delete_datasubjectrequest")

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("compliance.view_datasubjectrequest")


@admin.register(DataSubjectRequestAudit)
class DataSubjectRequestAuditAdmin(admin.ModelAdmin):
    """
    Data subject request audit admin interface
    """

    list_display = [
        "id",
        "request_type",
        "patient_name",
        "action",
        "action_by",
        "action_date",
    ]
    list_filter = ["action", "action_date", "hospital", "action_by"]
    search_fields = [
        "request__patient__first_name",
        "request__patient__last_name",
        "details",
    ]
    readonly_fields = [
        "id",
        "uuid",
        "request",
        "action",
        "action_by",
        "action_date",
        "details",
    ]
    date_hierarchy = "action_date"
    ordering = ["-action_date"]

    def patient_name(self, obj):
        return obj.request.patient.get_full_name()

    patient_name.short_description = _("Patient")
    patient_name.admin_order_field = "request__patient__last_name"

    def request_type(self, obj):
        return obj.request.get_request_type_display()

    request_type.short_description = _("Request Type")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("request", "request__patient", "action_by")
        )

    def has_add_permission(self, request):
        return False  # Audit logs cannot be manually added

    def has_change_permission(self, request, obj=None):
        return False  # Audit logs cannot be modified

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm("compliance.delete_datasubjectrequestaudit")

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("compliance.view_datasubjectrequestaudit")


class ComplianceAdminSite(admin.AdminSite):
    """
    Dedicated admin site for compliance management
    """

    site_header = _("HIPAA/GDPR Compliance Management")
    site_title = _("Compliance Portal")
    index_title = _("Welcome to Compliance Management Portal")
    site_url = "/compliance/"


# Create compliance admin site instance
compliance_admin_site = ComplianceAdminSite(name="compliance_admin")

# Register models with compliance admin site
compliance_admin_site.register(ConsentManagement, ConsentManagementAdmin)
compliance_admin_site.register(ConsentAuditLog, ConsentAuditLogAdmin)
compliance_admin_site.register(DataSubjectRequest, DataSubjectRequestAdmin)
compliance_admin_site.register(DataSubjectRequestAudit, DataSubjectRequestAuditAdmin)


# Admin dashboard customization
def get_compliance_dashboard_data():
    """
    Get data for compliance admin dashboard
    """
    from django.db.models import Count, Q
    from django.utils import timezone

    today = timezone.now()
    last_30_days = today - timezone.timedelta(days=30)

    # Consent metrics
    consent_metrics = ConsentManagement.objects.aggregate(
        total_consents=Count("id"),
        active_consents=Count("id", filter=Q(status=ConsentStatus.ACTIVE)),
        expired_consents=Count("id", filter=Q(status=ConsentStatus.EXPIRED)),
        revoked_consents=Count("id", filter=Q(status=ConsentStatus.REVOKED)),
    )

    # Data subject request metrics
    request_metrics = DataSubjectRequest.objects.aggregate(
        total_requests=Count("id"),
        pending_requests=Count("id", filter=Q(status="PENDING")),
        in_progress_requests=Count("id", filter=Q(status="IN_PROGRESS")),
        completed_requests=Count("id", filter=Q(status="COMPLETED")),
        overdue_requests=Count(
            "id", filter=Q(due_date__lt=today, status__in=["PENDING", "IN_PROGRESS"])
        ),
    )

    # Recent activity
    recent_consents = ConsentManagement.objects.filter(
        created_at__gte=last_30_days
    ).count()

    recent_requests = DataSubjectRequest.objects.filter(
        received_date__gte=last_30_days
    ).count()

    return {
        "consent_metrics": consent_metrics,
        "request_metrics": request_metrics,
        "recent_activity": {
            "new_consents": recent_consents,
            "new_requests": recent_requests,
        },
        "last_updated": today.isoformat(),
    }


# Custom admin template tags and filters can be added here
def customize_admin_site():
    """
    Customize the admin site with compliance-specific features
    """
    # Add custom CSS for compliance admin
    from django.templatetags.static import static

    # Add custom JavaScript for compliance features
    pass


# Call customization function
customize_admin_site()
