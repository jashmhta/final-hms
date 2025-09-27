"""
admin module
"""

from auditlog.models import LogEntry

from django.contrib import admin
from django.utils.html import format_html

from .models import BloodInventory, Crossmatch, Donor, TransfusionRecord


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "name",
        "blood_type",
        "is_active",
        "created_at",
        "get_recent_donation",
    ]
    list_filter = ["blood_type", "is_active", "created_at"]
    search_fields = ["blood_type", "contact"]
    readonly_fields = ["created_at", "updated_at", "history"]
    fieldsets = (
        (
            "Donor Information",
            {
                "fields": ("name", "dob", "ssn", "address", "contact"),
                "description": "Encrypted PII fields - only visible to authorized personnel",
            },
        ),
        (
            "Medical Information",
            {
                "fields": ("blood_type", "donation_history", "is_active"),
            },
        ),
        (
            "Audit Trail",
            {
                "fields": ("created_at", "updated_at", "history"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_recent_donation(self, obj):
        if hasattr(obj, "inventory_items") and obj.inventory_items.exists():
            latest = obj.inventory_items.latest("created_at")
            return latest.created_at.strftime("%Y-%m-%d")
        return "N/A"

    get_recent_donation.short_description = "Last Donation"

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly.extend(["name", "dob", "ssn", "address", "contact"])
        return tuple(readonly)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["audit_count"] = LogEntry.objects.filter(
            content_type__model="donor"
        ).count()
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "unit_id",
        "blood_type",
        "status",
        "expiry_date",
        "get_expiry_status",
        "created_at",
    ]
    list_filter = ["blood_type", "status", "expiry_date", "created_at"]
    search_fields = ["unit_id", "blood_type", "storage_location"]
    readonly_fields = ["created_at", "updated_at", "history"]
    actions = ["mark_as_expired", "mark_as_available"]
    fieldsets = (
        (
            "Inventory Details",
            {
                "fields": (
                    "donor",
                    "blood_type",
                    "unit_id",
                    "quantity",
                    "storage_location",
                ),
            },
        ),
        (
            "Status & Expiry",
            {
                "fields": ("status", "expiry_date"),
            },
        ),
        (
            "Audit Trail",
            {
                "fields": ("created_at", "updated_at", "history"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_expiry_status(self, obj):
        from datetime import date, timedelta

        today = date.today()
        expiry = obj.expiry_date
        if expiry < today:
            return format_html(
                '<span style="color: red; font-weight: bold;">EXPIRED</span>'
            )
        elif expiry <= today + timedelta(days=7):
            return format_html(
                '<span style="color: orange; font-weight: bold;">EXPIRING SOON</span>'
            )
        else:
            return format_html('<span style="color: green;">VALID</span>')

    get_expiry_status.short_description = "Status"
    get_expiry_status.admin_order_field = "expiry_date"

    def mark_as_expired(self, request, queryset):
        updated = queryset.update(status="EXPIRED")
        self.message_user(request, f"Marked {updated} units as expired.")

    mark_as_expired.short_description = "Mark selected as expired"

    def mark_as_available(self, request, queryset):
        updated = queryset.update(status="AVAILABLE")
        self.message_user(request, f"Marked {updated} units as available.")

    mark_as_available.short_description = "Mark selected as available"


@admin.register(TransfusionRecord)
class TransfusionRecordAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "patient",
        "blood_unit",
        "transfusion_date",
        "quantity",
        "performed_by",
        "created_at",
    ]
    list_filter = ["transfusion_date", "performed_by", "created_at"]
    search_fields = ["patient__name", "blood_unit__unit_id"]
    readonly_fields = ["transfusion_date", "created_at", "updated_at", "history"]
    fieldsets = (
        (
            "Transfusion Details",
            {
                "fields": ("patient", "blood_unit", "quantity", "performed_by"),
            },
        ),
        (
            "Clinical Notes",
            {
                "fields": ("notes"),
            },
        ),
        (
            "Audit Trail",
            {
                "fields": ("transfusion_date", "created_at", "updated_at", "history"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Crossmatch)
class CrossmatchAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "patient",
        "blood_unit",
        "compatibility_result",
        "tested_by",
        "created_at",
    ]
    list_filter = ["compatibility_result", "tested_by", "created_at"]
    search_fields = ["patient__name", "blood_unit__unit_id"]
    readonly_fields = ["created_at", "updated_at", "history"]
    fieldsets = (
        (
            "Crossmatch Details",
            {
                "fields": (
                    "patient",
                    "blood_unit",
                    "compatibility_result",
                    "tested_by",
                ),
            },
        ),
        (
            "Test Notes",
            {
                "fields": ("notes"),
            },
        ),
        (
            "Audit Trail",
            {
                "fields": ("created_at", "updated_at", "history"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("patient", "blood_unit", "tested_by")
