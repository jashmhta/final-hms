"""
serializers module
"""

from rest_framework import serializers

from .models import TallyIntegration


class TallyIntegrationSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)
    days_since_last_sync = serializers.SerializerMethodField()
    sync_status_display = serializers.SerializerMethodField()

    class Meta:
        model = TallyIntegration
        fields = [
            "id",
            "hospital",
            "hospital_name",
            "tally_server_url",
            "company_name",
            "tally_license_key",
            "auto_sync_enabled",
            "sync_frequency",
            "last_sync_time",
            "last_sync_status",
            "sync_error_message",
            "revenue_account_id",
            "expense_account_id",
            "asset_account_id",
            "liability_account_id",
            "is_active",
            "created_at",
            "updated_at",
            "days_since_last_sync",
            "sync_status_display",
        ]
        read_only_fields = ["last_sync_time", "last_sync_status", "sync_error_message"]

    def get_days_since_last_sync(self, obj):
        if obj.last_sync_time:
            from django.utils import timezone

            return (timezone.now() - obj.last_sync_time).days
        return None

    def get_sync_status_display(self, obj):
        status_map = {
            "PENDING": "Pending",
            "SUCCESS": "Success",
            "FAILED": "Failed",
            "IN_PROGRESS": "In Progress",
        }
        return status_map.get(obj.last_sync_status, obj.last_sync_status)

    def validate_tally_server_url(self, value):
        if not value.startswith(("http://", "https://")):
            raise serializers.ValidationError(
                "Tally server URL must start with http:// or https://"
            )
        return value

    def validate_company_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Company name must be at least 2 characters long"
            )
        return value.strip()
