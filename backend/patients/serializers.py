from rest_framework import serializers

from .models import (
    Patient,
    EmergencyContact,
    InsuranceInformation,
    PatientStatus,
    EmergencyContact,
    InsuranceInformation,
    PatientStatus,
)


class PatientSerializer(serializers.ModelSerializer):
    phone_primary = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    insurance_provider = serializers.CharField(
        source="insurance_information.insurance_company_name", required=False
    )
    insurance_number = serializers.CharField(
        source="insurance_information.policy_number", required=False
    )
    status = serializers.ChoiceField(choices=PatientStatus.choices, default="ACTIVE")

    class Meta:
        model = Patient
        fields = [
            "id",
            "uuid",
            "hospital",
            "first_name",
            "middle_name",
            "last_name",
            "suffix",
            "date_of_birth",
            "gender",
            "marital_status",
            "phone_primary",
            "phone_secondary",
            "email",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "zip_code",
            "country",
            "blood_type",
            "weight_kg",
            "height_cm",
            "status",
            "organ_donor",
            "primary_care_physician",
            "insurance_provider",
            "insurance_number",
            "created_at",
            "updated_at",
            "emergency_contacts",
            "insurance_plans",
        ]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]
        extra_kwargs = {
            "phone_primary": {"write_only": True},
            "email": {"write_only": True},
            "address_line1": {"write_only": True},
        }

    def create(self, validated_data):
        # Handle nested emergency contacts and insurance if provided
        emergency_data = validated_data.pop("emergency_contacts", [])
        insurance_data = validated_data.pop("insurance_plans", [])
        patient = super().create(validated_data)

        # Create emergency contacts
        for contact_data in emergency_data:
            EmergencyContact.objects.create(patient=patient, **contact_data)

        # Create insurance plans
        for ins_data in insurance_data:
            InsuranceInformation.objects.create(patient=patient, **ins_data)

        return patient
