"""
serializers module
"""

from rest_framework import serializers

from .models import Hospital, HospitalPlan, Plan


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = [
            "id",
            "name",
            "code",
            "address",
            "phone",
            "email",
            "timezone",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "max_users",
            "enable_opd",
            "enable_ipd",
            "enable_diagnostics",
            "enable_pharmacy",
            "enable_accounting",
        ]


class HospitalPlanSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        source="plan", queryset=Plan.objects.all(), write_only=True
    )

    class Meta:
        model = HospitalPlan
        fields = [
            "id",
            "hospital",
            "plan",
            "plan_id",
            "enable_opd",
            "enable_ipd",
            "enable_diagnostics",
            "enable_pharmacy",
            "enable_accounting",
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters")
        return value
