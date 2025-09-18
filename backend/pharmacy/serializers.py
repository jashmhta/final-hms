from rest_framework import serializers
from .models import InventoryTransaction, Medication, Prescription
class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = [
            "id",
            "hospital",
            "name",
            "strength",
            "form",
            "total_stock_quantity",
            "min_stock_level",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = [
            "id",
            "hospital",
            "encounter",
            "patient",
            "doctor",
            "medication",
            "dosage_instructions",
            "quantity",
            "is_dispensed",
            "dispensed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_dispensed",
            "dispensed_at",
            "created_at",
            "updated_at",
        ]
class InventoryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransaction
        fields = [
            "id",
            "hospital",
            "medication",
            "change",
            "reason",
            "performed_by",
            "performed_at",
        ]
        read_only_fields = ["id", "performed_at"]