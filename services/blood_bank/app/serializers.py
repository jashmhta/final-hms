from datetime import date, timedelta
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import BloodInventory, Crossmatch, Donor, TransfusionRecord
BLOOD_TYPES = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
class DonorSerializer(serializers.ModelSerializer):
    ssn = serializers.CharField(
        validators=[
            RegexValidator(r"^\d{3}-\d{2}-\d{4}$", "SSN must be in format XXX-XX-XXXX")
        ]
    )
    contact = serializers.CharField(
        validators=[RegexValidator(r"^\+?1?\d{10}$", "Phone number must be 10 digits")]
    )
    blood_type = serializers.ChoiceField(choices=BLOOD_TYPES)
    class Meta:
        model = Donor
        fields = [
            "id",
            "name",
            "dob",
            "ssn",
            "address",
            "contact",
            "blood_type",
            "donation_history",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    def validate_blood_type(self, value):
        if value not in BLOOD_TYPES:
            raise serializers.ValidationError(f"Invalid blood type: {value}")
        return value
    def validate_ssn(self, value):
        digits = value.replace("-", "")
        if len(digits) != 9 or not digits.isdigit():
            raise serializers.ValidationError("SSN must be 9 digits")
        return value
class BloodInventorySerializer(serializers.ModelSerializer):
    unit_id = serializers.CharField(
        validators=[UniqueValidator(queryset=BloodInventory.objects.all())]
    )
    blood_type = serializers.ChoiceField(choices=BLOOD_TYPES)
    status = serializers.ChoiceField(
        choices=["AVAILABLE", "RESERVED", "TRANSFUSED", "EXPIRED", "QUARANTINED"]
    )
    expiry_date = serializers.DateField()
    class Meta:
        model = BloodInventory
        fields = [
            "id",
            "donor",
            "blood_type",
            "unit_id",
            "expiry_date",
            "status",
            "quantity",
            "storage_location",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    def validate_blood_type(self, value):
        if value not in BLOOD_TYPES:
            raise serializers.ValidationError(f"Invalid blood type: {value}")
        return value
    def validate_expiry_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Expiry date cannot be in the past")
        if value < date.today() + timedelta(days=30):
            raise serializers.ValidationError(
                "Blood must have at least 30 days shelf life"
            )
        return value
    def validate_status(self, value):
        valid_statuses = [
            "AVAILABLE",
            "RESERVED",
            "TRANSFUSED",
            "EXPIRED",
            "QUARANTINED",
        ]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status: {value}")
        return value
class TransfusionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransfusionRecord
        fields = [
            "id",
            "patient",
            "blood_unit",
            "transfusion_date",
            "quantity",
            "notes",
            "performed_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "transfusion_date", "created_at", "updated_at"]
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value
    def validate_blood_unit(self, value):
        if value.status not in ["AVAILABLE", "RESERVED"]:
            raise serializers.ValidationError(
                "Blood unit must be available or reserved for transfusion"
            )
        return value
class CrossmatchSerializer(serializers.ModelSerializer):
    compatibility_result = serializers.ChoiceField(
        choices=["COMPATIBLE", "INCOMPATIBLE", "PENDING", "ERROR"]
    )
    class Meta:
        model = Crossmatch
        fields = [
            "id",
            "patient",
            "blood_unit",
            "compatibility_result",
            "tested_by",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    def validate_compatibility_result(self, value):
        valid_results = ["COMPATIBLE", "INCOMPATIBLE", "PENDING", "ERROR"]
        if value not in valid_results:
            raise serializers.ValidationError(f"Invalid compatibility result: {value}")
        return value
__all__ = [
    "DonorSerializer",
    "BloodInventorySerializer",
    "TransfusionRecordSerializer",
    "CrossmatchSerializer",
]