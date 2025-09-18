from rest_framework import serializers
from .models import Encounter, EncounterAttachment, EncounterNote
class EncounterNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncounterNote
        fields = [
            "id",
            "encounter",
            "author",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
class EncounterAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EncounterAttachment
        fields = [
            "id",
            "encounter",
            "uploaded_by",
            "file",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
class EncounterSerializer(serializers.ModelSerializer):
    notes = EncounterNoteSerializer(many=True, read_only=True)
    attachments = EncounterAttachmentSerializer(many=True, read_only=True)
    class Meta:
        model = Encounter
        fields = [
            "id",
            "hospital",
            "patient",
            "primary_physician",
            "appointment",
            "diagnosis",
            "treatment",
            "prescription_text",
            "is_finalized",
            "notes",
            "attachments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "notes",
            "attachments",
        ]
class NotificationSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    message = serializers.CharField()
    type = serializers.CharField()
    severity = serializers.CharField(default='info')
    created_at = serializers.DateTimeField(read_only=True)
    read = serializers.BooleanField(default=False)
class QualityMetricSerializer(serializers.Serializer):
    metric_name = serializers.CharField()
    value = serializers.FloatField()
    target_value = serializers.FloatField(required=False)
    unit = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField()
    hospital_id = serializers.IntegerField(required=False)