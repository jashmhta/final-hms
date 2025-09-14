from rest_framework import serializers

from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "id",
            "uuid",
            "hospital",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "phone",
            "email",
            "address",
            "insurance_provider",
            "insurance_number",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]
