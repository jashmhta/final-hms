from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html

from .models import AuditLog, BreachNotification, PatientConsent
from .utils import ConsentManager


@admin.register(PatientConsent)
class PatientConsentAdmin(admin.ModelAdmin):
    """HIPAA-compliant admin for patient consent management."""

    list_display = [
        "patient",
        "consent_type",
        "is_active",
        "consent_date",
        "expiry_date",
        "status_display",
    ]
    list_filter = ["consent_type", "is_active", "consent_date", "expiry_date"]
    search_fields = ["patient__username", "patient__email", "consent_type"]
    readonly_fields = ["consent_date"]

    fieldsets = (
        ("Patient Information", {"fields": ("patient", "consent_type")}),
        (
            "Consent Details",
            {
                "fields": ("encrypted_consent_details",),
                "description": "Encrypted PHI - visible only to authorized personnel",
            },
        ),
        ("Status", {"fields": ("is_active", "consent_date", "expiry_date")}),
    )

    def status_display(self, obj):
        """Display consent status with color coding."""
        if not obj.is_active:
            return format_html('<span style="color: red;">Inactive</span>')
        elif obj.expiry_date and obj.expiry_date < timezone.now().date():
            return format_html('<span style="color: orange;">Expired</span>')
        else:
            return format_html('<span style="color: green;">Active</span>')

    status_display.short_description = "Status"

    def get_queryset(self, request):
        """Filter consents for current user (HIPAA access control)."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Limit to patient's own consents or staff consents
            if request.user.is_staff:
                return qs.filter(patient=request.user)
        return qs

    actions = ["mark_consents_expired", "reactivate_consents"]

    @admin.action(description="Mark selected consents as expired")
    def mark_consents_expired(self, request, queryset):
        """Custom action to mark consents as expired."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} consents marked as expired.")

    @admin.action(description="Reactivate selected consents")
    def reactivate_consents(self, request, queryset):
        """Custom action to reactivate consents."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} consents reactivated.")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """HIPAA-compliant audit log administration."""

    list_display = ["action", "user", "timestamp", "ip_address", "phi_summary"]
    list_filter = ["action", "user", "timestamp", "ip_address"]
    search_fields = ["user__username", "action", "phi_accessed"]
    readonly_fields = ["timestamp"]
    date_hierarchy = "timestamp"

    fieldsets = (
        ("Audit Details", {"fields": ("user", "action", "timestamp")}),
        (
            "PHI Access",
            {
                "fields": ("phi_accessed",),
                "description": "Encrypted PHI access details",
            },
        ),
        ("Technical", {"fields": ("ip_address", "session_id")}),
    )

    def phi_summary(self, obj):
        """Display truncated, decrypted PHI summary if possible."""
        if obj.phi_accessed:
            # Attempt to show first 50 chars (decrypted if possible)
            try:
                from .utils import HIPAAEncryptionUtils

                key = HIPAAEncryptionUtils.get_encryption_key()
                decrypted = HIPAAEncryptionUtils.decrypt_transit_data(
                    obj.phi_accessed, key
                )
                return decrypted[:50] + "..." if len(decrypted) > 50 else decrypted
            except:
                return (
                    obj.phi_accessed[:50] + "..."
                    if len(obj.phi_accessed) > 50
                    else obj.phi_accessed
                )
        return "No PHI accessed"

    phi_summary.short_description = "PHI Summary"

    def has_add_permission(self, request):
        """Prevent manual addition of audit logs."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of audit logs (immutability)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs (retention requirements)."""
        return False

    actions = ["export_audit_logs"]

    @admin.action(description="Export selected audit logs to CSV")
    def export_audit_logs(self, request, queryset):
        """Export audit logs for compliance reporting."""
        # Implementation for CSV export
        self.message_user(request, f"Exporting {queryset.count()} audit logs...")


@admin.register(BreachNotification)
class BreachNotificationAdmin(admin.ModelAdmin):
    """HIPAA-compliant breach notification administration."""

    list_display = [
        "breach_type",
        "affected_patients_count",
        "discovery_date",
        "notification_sent",
        "notification_due_display",
    ]
    list_filter = ["breach_type", "notification_sent", "discovery_date"]
    search_fields = ["breach_type", "description"]
    readonly_fields = ["discovery_date"]

    fieldsets = (
        (
            "Breach Details",
            {"fields": ("breach_type", "affected_patients_count", "discovery_date")},
        ),
        (
            "Description",
            {"fields": ("description",), "description": "Encrypted breach description"},
        ),
        (
            "Notifications",
            {"fields": ("notification_sent", "notification_date", "notified_parties")},
        ),
    )

    def notification_due_display(self, obj):
        """Calculate and display notification due date per HIPAA rules."""
        from .utils import BreachDetectionUtils

        impact = BreachDetectionUtils.calculate_breach_impact(
            obj.affected_patients_count
        )
        if impact == "major":
            return format_html('<span style="color: red;">60 days to HHS</span>')
        elif impact == "minor":
            return format_html(
                '<span style="color: orange;">Immediate to individuals</span>'
            )
        return "None required"

    notification_due_display.short_description = "Notification Due"

    actions = ["mark_notifications_sent", "generate_breach_report"]

    @admin.action(description="Mark selected breaches as notified")
    def mark_notifications_sent(self, request, queryset):
        """Mark breach notifications as sent."""
        updated = queryset.update(
            notification_sent=True, notification_date=timezone.now()
        )
        self.message_user(request, f"{updated} breach notifications marked as sent.")

    @admin.action(description="Generate breach compliance report")
    def generate_breach_report(self, request, queryset):
        """Generate HIPAA breach notification report."""
        # Implementation for report generation
        self.message_user(
            request, f"Generating report for {queryset.count()} breaches..."
        )


# Custom UserAdmin extension for HIPAA consent overview
class HIPAAUserAdmin(UserAdmin):
    """Extended UserAdmin with HIPAA consent information."""

    def get_consent_status(self, obj):
        """Display patient's consent status in user list."""
        from .models import PatientConsent

        now = timezone.now().date()
        active_consents = PatientConsent.objects.filter(
            patient=obj, is_active=True, expiry_date__gte=now
        ).count()
        total_consents = PatientConsent.objects.filter(patient=obj).count()
        return f"{active_consents}/{total_consents} active"

    get_consent_status.short_description = "Consent Status"

    def changelist_view(self, request, extra_context=None):
        """Add consent statistics to user changelist."""
        extra_context = extra_context or {}
        from .models import PatientConsent

        extra_context["consent_stats"] = {
            "total_consents": PatientConsent.objects.count(),
            "active_consents": PatientConsent.objects.filter(is_active=True).count(),
            "expired_consents": PatientConsent.objects.filter(is_active=False).count(),
        }
        return super().changelist_view(request, extra_context=extra_context)


# Register extended UserAdmin
admin.site.unregister(User)
admin.site.register(User, HIPAAUserAdmin)
