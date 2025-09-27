"""
Optimized Patient Serializers with Performance Enhancements
"""

from datetime import date

from rest_framework import serializers

from django.utils import timezone

from .models import (
    BloodType,
    EmergencyContact,
    EthnicityChoices,
    InsuranceInformation,
    MaritalStatus,
    Patient,
    PatientGender,
    PatientStatus,
    PreferredLanguage,
    RaceChoices,
    ReligionChoices,
)


class PatientListSerializer(serializers.ModelSerializer):
    """Optimized serializer for patient listings (minimal data)"""

    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    is_minor = serializers.BooleanField(read_only=True)
    primary_care_physician_name = serializers.CharField(
        source="primary_care_physician.get_full_name", read_only=True
    )

    class Meta:
        model = Patient
        fields = [
            "id",
            "uuid",
            "medical_record_number",
            "full_name",
            "age",
            "is_minor",
            "gender",
            "status",
            "date_of_birth",
            "phone_primary",
            "email",
            "city",
            "state",
            "primary_care_physician_name",
            "vip_status",
            "confidential",
            "patient_portal_enrolled",
            "created_at",
        ]
        read_only_fields = ["id", "uuid", "created_at"]


class PatientDetailSerializer(serializers.ModelSerializer):
    """Comprehensive patient detail serializer with caching"""

    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    is_minor = serializers.BooleanField(read_only=True)
    primary_care_physician_name = serializers.CharField(
        source="primary_care_physician.get_full_name", read_only=True, allow_null=True
    )
    referring_physician_name = serializers.CharField(
        source="referring_physician.get_full_name", read_only=True, allow_null=True
    )
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, allow_null=True
    )
    updated_by_name = serializers.CharField(
        source="last_updated_by.get_full_name", read_only=True, allow_null=True
    )
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)
    emergency_contacts = serializers.SerializerMethodField()
    insurance_plans = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = "__all__"
        read_only_fields = [
            "id",
            "uuid",
            "medical_record_number",
            "created_at",
            "updated_at",
            "created_by",
            "last_updated_by",
        ]

    def get_emergency_contacts(self, obj):
        """Get emergency contacts efficiently"""
        # This will be prefetched in the view
        if hasattr(obj, "_prefetched_emergency_contacts"):
            return EmergencyContactSerializer(
                obj._prefetched_emergency_contacts, many=True
            ).data
        return []

    def get_insurance_plans(self, obj):
        """Get insurance plans efficiently"""
        # This will be prefetched in the view
        if hasattr(obj, "_prefetched_insurance_plans"):
            return InsuranceInformationSerializer(
                obj._prefetched_insurance_plans, many=True
            ).data
        return []

    def to_representation(self, instance):
        """Optimized serialization with caching"""
        # Use cached representation if available
        cache_key = f"patient_serialized_{instance.id}"
        cached_data = self.context.get("cache", {}).get(cache_key)

        if cached_data:
            return cached_data

        # Serialize data
        data = super().to_representation(instance)

        # Cache in context for multiple calls
        if "cache" in self.context:
            self.context["cache"][cache_key] = data

        return data


class PatientCreateSerializer(serializers.ModelSerializer):
    """Optimized patient creation serializer"""

    class Meta:
        model = Patient
        exclude = [
            "id",
            "uuid",
            "medical_record_number",
            "created_at",
            "updated_at",
            "created_by",
            "last_updated_by",
        ]
        extra_kwargs = {
            "status": {"default": PatientStatus.ACTIVE},
            "country": {"default": "US"},
            "preferred_language": {"default": PreferredLanguage.ENGLISH},
            "marital_status": {"default": MaritalStatus.UNKNOWN},
            "race": {"default": RaceChoices.PREFER_NOT_TO_SAY},
            "ethnicity": {"default": EthnicityChoices.PREFER_NOT_TO_SAY},
            "religion": {"default": ReligionChoices.PREFER_NOT_TO_SAY},
            "blood_type": {"default": BloodType.UNKNOWN},
        }

    def create(self, validated_data):
        """Optimized create with validation"""
        # Generate MRN
        import time

        timestamp = str(int(time.time()))
        validated_data["medical_record_number"] = f"MRN{timestamp[-8:]}"

        # Create patient
        patient = super().create(validated_data)

        # Cache patient data
        patient._cache_patient_data()

        return patient


class PatientUpdateSerializer(serializers.ModelSerializer):
    """Optimized patient update serializer with partial updates"""

    class Meta:
        model = Patient
        exclude = [
            "id",
            "uuid",
            "medical_record_number",
            "created_at",
            "updated_at",
            "created_by",
            "last_updated_by",
        ]

    def update(self, instance, validated_data):
        """Optimized update with selective field updates"""
        # Only update fields that are provided
        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()

        # Cache patient data
        instance._cache_patient_data()

        return instance


class EmergencyContactSerializer(serializers.ModelSerializer):
    """Optimized emergency contact serializer"""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = EmergencyContact
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_full_name(self, obj):
        """Get full name efficiently"""
        return f"{obj.first_name} {obj.last_name}"


class InsuranceInformationSerializer(serializers.ModelSerializer):
    """Optimized insurance information serializer"""

    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = InsuranceInformation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate insurance dates"""
        effective_date = data.get("effective_date")
        termination_date = data.get("termination_date")

        if effective_date and termination_date:
            if termination_date < effective_date:
                raise serializers.ValidationError(
                    "Termination date must be after effective date"
                )

        return data

    def to_representation(self, instance):
        """Optimized representation with status calculation"""
        data = super().to_representation(instance)
        today = date.today()

        # Calculate active status
        effective_date = instance.effective_date
        termination_date = instance.termination_date

        data["is_active"] = effective_date <= today and (
            termination_date is None or termination_date >= today
        )

        return data


class PatientSearchSerializer(serializers.ModelSerializer):
    """Ultra-lightweight serializer for search results"""

    class Meta:
        model = Patient
        fields = [
            "id",
            "medical_record_number",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "status",
            "phone_primary",
            "email",
        ]


class PatientStatisticsSerializer(serializers.Serializer):
    """Serializer for patient statistics"""

    total_patients = serializers.IntegerField()
    active_patients = serializers.IntegerField()
    inactive_patients = serializers.IntegerField()
    vip_count = serializers.IntegerField()
    portal_enrolled = serializers.IntegerField()
    confidential_count = serializers.IntegerField()
    new_patients_last_30d = serializers.IntegerField()
    age_distribution = serializers.DictField()
    calculated_at = serializers.DateTimeField()


class PatientExportSerializer(serializers.ModelSerializer):
    """Optimized serializer for data export"""

    class Meta:
        model = Patient
        fields = [
            "id",
            "medical_record_number",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "marital_status",
            "status",
            "phone_primary",
            "phone_secondary",
            "email",
            "address_line1",
            "city",
            "state",
            "zip_code",
            "country",
            "blood_type",
            "vip_status",
            "confidential",
            "patient_portal_enrolled",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        """Optimized export serialization"""
        data = super().to_representation(instance)

        # Format dates for export
        if data["date_of_birth"]:
            data["date_of_birth"] = instance.date_of_birth.strftime("%Y-%m-%d")

        if data["created_at"]:
            data["created_at"] = instance.created_at.strftime("%Y-%m-%d %H:%M:%S")

        if data["updated_at"]:
            data["updated_at"] = instance.updated_at.strftime("%Y-%m-%d %H:%M:%S")

        return data


class BulkPatientSerializer(serializers.ListSerializer):
    """Optimized bulk operations serializer"""

    def create(self, validated_data):
        """Bulk create patients efficiently"""
        patients = [Patient(**item) for item in validated_data]
        return Patient.objects.bulk_create(patients, batch_size=1000)

    def update(self, instances, validated_data):
        """Bulk update patients efficiently"""
        instance_map = {instance.id: instance for instance in instances}

        updates = []
        for item in validated_data:
            instance = instance_map[item["id"]]
            for field, value in item.items():
                if field != "id":
                    setattr(instance, field, value)
            updates.append(instance)

        Patient.objects.bulk_update(updates, batch_size=1000)
        return updates
