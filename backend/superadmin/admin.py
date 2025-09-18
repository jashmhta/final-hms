from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    GlobalSettings,
    HospitalSubscription,
    ModulePermission,
    SubscriptionTier,
    SuperadminUser,
    SystemAlert,
    TierModuleAccess,
    UsageMetrics,
)
@admin.register(SubscriptionTier)
class SubscriptionTierAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "tier_type",
        "price_monthly",
        "price_yearly",
        "max_users",
        "max_beds",
        "is_active",
    ]
    list_filter = ["tier_type", "is_active"]
    search_fields = ["name", "description"]
    ordering = ["price_monthly"]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "tier_type", "description", "is_active")},
        ),
        ("Pricing", {"fields": ("price_monthly", "price_yearly")}),
        (
            "Limits",
            {"fields": ("max_users", "max_beds", "storage_gb", "api_calls_per_month")},
        ),
        ("Support", {"fields": ("support_level",)}),
    )
class TierModuleAccessInline(admin.TabularInline):
    model = TierModuleAccess
    extra = 0
    fields = ["module", "is_enabled", "feature_limits"]
@admin.register(ModulePermission)
class ModulePermissionAdmin(admin.ModelAdmin):
    list_display = [
        "display_name",
        "module_name",
        "is_core_module",
        "min_tier_required",
    ]
    list_filter = ["is_core_module", "min_tier_required"]
    search_fields = ["display_name", "module_name", "description"]
    inlines = [TierModuleAccessInline]
@admin.register(HospitalSubscription)
class HospitalSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "hospital",
        "tier",
        "status",
        "billing_cycle",
        "days_remaining_display",
        "monthly_amount",
    ]
    list_filter = ["status", "billing_cycle", "tier", "auto_renewal"]
    search_fields = ["hospital__name", "billing_contact_name", "billing_contact_email"]
    readonly_fields = ["days_remaining_display", "usage_summary"]
    fieldsets = (
        (
            "Subscription Details",
            {"fields": ("hospital", "tier", "status", "billing_cycle")},
        ),
        (
            "Dates",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "trial_end_date",
                    "next_billing_date",
                    "last_payment_date",
                )
            },
        ),
        (
            "Usage & Limits",
            {
                "fields": (
                    "current_users",
                    "current_beds",
                    "storage_used_gb",
                    "api_calls_this_month",
                    "usage_summary",
                )
            },
        ),
        (
            "Billing Information",
            {
                "fields": (
                    "monthly_amount",
                    "discount_percent",
                    "billing_contact_name",
                    "billing_contact_email",
                    "billing_contact_phone",
                    "billing_address",
                )
            },
        ),
        ("Payment Settings", {"fields": ("auto_renewal", "payment_method")}),
    )
    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days > 30:
            color = "green"
        elif days > 7:
            color = "orange"
        else:
            color = "red"
        return format_html('<span style="color: {};">{} days</span>', color, days)
    days_remaining_display.short_description = "Days Remaining"
    def usage_summary(self, obj):
        tier_limits = obj.tier
        usage_html = f
        from django.utils.html import format_html
        return format_html(usage_html)
    usage_summary.short_description = "Usage Summary"
@admin.register(SuperadminUser)
class SuperadminUserAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "is_active", "last_login_ip", "permissions_summary"]
    list_filter = ["role", "is_active", "can_manage_subscriptions", "can_manage_users"]
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    ]
    fieldsets = (
        ("User Information", {"fields": ("user", "role", "is_active")}),
        (
            "Permissions",
            {
                "fields": (
                    "can_manage_subscriptions",
                    "can_manage_users",
                    "can_view_analytics",
                    "can_access_support",
                    "can_manage_billing",
                )
            },
        ),
        ("Access Control", {"fields": ("accessible_hospitals", "ip_whitelist")}),
        ("Activity", {"fields": ("last_login_ip",)}),
    )
    def permissions_summary(self, obj):
        perms = []
        if obj.can_manage_subscriptions:
            perms.append("Subscriptions")
        if obj.can_manage_users:
            perms.append("Users")
        if obj.can_view_analytics:
            perms.append("Analytics")
        if obj.can_manage_billing:
            perms.append("Billing")
        return ", ".join(perms) if perms else "Basic"
    permissions_summary.short_description = "Permissions"
@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "key",
        "category",
        "value_preview",
        "is_encrypted",
        "last_modified_by",
        "modified_at",
    ]
    list_filter = ["category", "is_encrypted"]
    search_fields = ["key", "description"]
    readonly_fields = ["last_modified_by", "modified_at"]
    def value_preview(self, obj):
        return obj.value[:100] + "..." if len(obj.value) > 100 else obj.value
    value_preview.short_description = "Value"
    def save_model(self, request, obj, form, change):
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)
@admin.register(SystemAlert)
class SystemAlertAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "alert_type",
        "severity",
        "is_active",
        "show_from",
        "show_until",
        "created_by",
    ]
    list_filter = ["alert_type", "severity", "is_active", "target_all_hospitals"]
    search_fields = ["title", "message"]
    filter_horizontal = ["target_hospitals", "target_tiers"]
    fieldsets = (
        ("Alert Content", {"fields": ("title", "message", "alert_type", "severity")}),
        (
            "Targeting",
            {"fields": ("target_all_hospitals", "target_hospitals", "target_tiers")},
        ),
        ("Scheduling", {"fields": ("is_active", "show_from", "show_until")}),
        (
            "Display Options",
            {"fields": ("show_on_dashboard", "send_email", "send_sms")},
        ),
    )
@admin.register(UsageMetrics)
class UsageMetricsAdmin(admin.ModelAdmin):
    list_display = [
        "hospital",
        "date",
        "active_users",
        "api_calls",
        "patients_created",
        "storage_used_mb",
    ]
    list_filter = ["date", "hospital"]
    search_fields = ["hospital__name"]
    date_hierarchy = "date"
    ordering = ["-date"]
    readonly_fields = ["hospital", "date"]  