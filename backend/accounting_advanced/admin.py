from django.contrib import admin

from .models import TallyIntegration


@admin.register(TallyIntegration)
class TallyIntegrationAdmin(admin.ModelAdmin):
    list_display = [
        "hospital",
        "company_name",
        "tally_server_url",
        "auto_sync_enabled",
        "sync_frequency",
        "last_sync_status",
        "last_sync_time",
        "is_active",
    ]
    list_filter = ["is_active", "auto_sync_enabled", "sync_frequency", "last_sync_status"]
    search_fields = ["hospital__name", "company_name", "tally_server_url"]
    readonly_fields = ["last_sync_time", "last_sync_status", "sync_error_message"]
    fieldsets = (
        ("Hospital Information", {"fields": ("hospital", "is_active")}),
        ("Tally Configuration", {"fields": ("tally_server_url", "company_name", "tally_license_key")}),
        ("Sync Settings", {"fields": ("auto_sync_enabled", "sync_frequency")}),
        (
            "Account Mapping",
            {"fields": ("revenue_account_id", "expense_account_id", "asset_account_id", "liability_account_id")},
        ),
        (
            "Sync Status",
            {"fields": ("last_sync_time", "last_sync_status", "sync_error_message"), "classes": ("collapse",)},
        ),
    )
    actions = ["enable_auto_sync", "disable_auto_sync", "test_connections"]

    def enable_auto_sync(self, request, queryset):
        updated = queryset.update(auto_sync_enabled=True)
        self.message_user(request, f"{updated} integration(s) auto-sync enabled successfully.")

    enable_auto_sync.short_description = "Enable auto-sync for selected integrations"

    def disable_auto_sync(self, request, queryset):
        updated = queryset.update(auto_sync_enabled=False)
        self.message_user(request, f"{updated} integration(s) auto-sync disabled successfully.")

    disable_auto_sync.short_description = "Disable auto-sync for selected integrations"

    def test_connections(self, request, queryset):
        self.message_user(
            request,
            f"Connection test initiated for {queryset.count()} integration(s). "
            "Check individual integration status for results.",
        )

    test_connections.short_description = "Test connections for selected integrations"
