from rest_framework import serializers

from .models import LabOrder, LabResult, LabTest


class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        fields = [
            "id",
            "hospital",
            "name",
            "description",
            "normal_range",
            "price_cents",
        ]
        read_only_fields = ["id"]


class LabOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabOrder
        fields = ["id", "hospital", "patient", "doctor", "test", "ordered_at", "status"]
        read_only_fields = ["id", "ordered_at"]


class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = [
            "id",
            "hospital",
            "order",
            "value",
            "unit",
            "observations",
            "reported_at",
        ]
        read_only_fields = ["id", "reported_at"]
