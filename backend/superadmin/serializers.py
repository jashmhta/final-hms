from django.contrib.auth import get_user_model
from hospitals.models import Hospital
from rest_framework import serializers

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

User = get_user_model()


class SubscriptionTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionTier
        fields = "__all__"


class ModulePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModulePermission
        fields = "__all__"


class TierModuleAccessSerializer(serializers.ModelSerializer):
    module_details = ModulePermissionSerializer(source="module", read_only=True)

    class Meta:
        model = TierModuleAccess
        fields = ["id", "module", "module_details", "is_enabled", "feature_limits"]


class HospitalSubscriptionSerializer(serializers.ModelSerializer):
    tier_details = SubscriptionTierSerializer(source="tier", read_only=True)
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)
    days_remaining = serializers.ReadOnlyField()
    is_trial = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = HospitalSubscription
        fields = "__all__"


class HospitalSummarySerializer(serializers.ModelSerializer):
    subscription = HospitalSubscriptionSerializer(read_only=True)
    total_users = serializers.SerializerMethodField()
    total_patients = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = [
            "id",
            "name",
            "address",
            "phone",
            "email",
            "license_number",
            "subscription",
            "total_users",
            "total_patients",
            "created_at",
        ]

    def get_total_users(self, obj):
        return obj.users.count()

    def get_total_patients(self, obj):
        return obj.patients.count()


class SuperadminUserSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    accessible_hospitals_details = serializers.SerializerMethodField()

    class Meta:
        model = SuperadminUser
        fields = "__all__"

    def get_user_details(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "full_name": obj.user.get_full_name(),
            "is_active": obj.user.is_active,
            "last_login": obj.user.last_login,
        }

    def get_accessible_hospitals_details(self, obj):
        hospitals = obj.accessible_hospitals.all()
        return [{"id": h.id, "name": h.name} for h in hospitals]


class GlobalSettingsSerializer(serializers.ModelSerializer):
    last_modified_by_name = serializers.CharField(
        source="last_modified_by.get_full_name", read_only=True
    )

    class Meta:
        model = GlobalSettings
        fields = "__all__"
        extra_kwargs = {"last_modified_by": {"read_only": True}}


class SystemAlertSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    target_hospitals_details = serializers.SerializerMethodField()
    target_tiers_details = serializers.SerializerMethodField()

    class Meta:
        model = SystemAlert
        fields = "__all__"
        extra_kwargs = {"created_by": {"read_only": True}}

    def get_target_hospitals_details(self, obj):
        if obj.target_all_hospitals:
            return "All Hospitals"
        hospitals = obj.target_hospitals.all()
        return [{"id": h.id, "name": h.name} for h in hospitals]

    def get_target_tiers_details(self, obj):
        tiers = obj.target_tiers.all()
        return [{"id": t.id, "name": t.name} for t in tiers]


class UsageMetricsSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)

    class Meta:
        model = UsageMetrics
        fields = "__all__"


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""

    total_hospitals = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    trial_subscriptions = serializers.IntegerField()
    expired_subscriptions = serializers.IntegerField()
    total_revenue_monthly = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_users = serializers.IntegerField()
    total_patients = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    system_health = serializers.CharField()


class PriceEstimatorRequestSerializer(serializers.Serializer):
    """Serializer for price estimation requests"""

    services = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )
    patient_type = serializers.ChoiceField(choices=["OPD", "IPD", "EMERGENCY"])
    insurance_type = serializers.ChoiceField(
        choices=["NONE", "BASIC", "PREMIUM"], required=False
    )
    room_type = serializers.ChoiceField(
        choices=["GENERAL", "PRIVATE", "DELUXE", "SUITE"], required=False
    )
    duration_days = serializers.IntegerField(min_value=1, required=False)


class PriceEstimatorResponseSerializer(serializers.Serializer):
    """Serializer for price estimation responses"""

    total_estimate = serializers.DecimalField(max_digits=10, decimal_places=2)
    breakdown = serializers.ListField(child=serializers.DictField())
    insurance_coverage = serializers.DecimalField(max_digits=10, decimal_places=2)
    patient_responsibility = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_available = serializers.DecimalField(max_digits=10, decimal_places=2)
    estimated_savings = serializers.DecimalField(max_digits=10, decimal_places=2)
