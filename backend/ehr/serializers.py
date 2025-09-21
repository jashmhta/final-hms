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


class OptimizedEncounterNoteSerializer(serializers.ModelSerializer):
    """Optimized serializer to prevent N+1 queries."""

    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = EncounterNote
        fields = [
            "id",
            "encounter",
            "author",
            "author_name",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OptimizedEncounterAttachmentSerializer(serializers.ModelSerializer):
    """Optimized serializer to prevent N+1 queries."""

    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_size = serializers.IntegerField(source='file.size', read_only=True)

    class Meta:
        model = EncounterAttachment
        fields = [
            "id",
            "encounter",
            "uploaded_by",
            "uploaded_by_name",
            "file",
            "file_size",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EncounterSerializer(serializers.ModelSerializer):
    """Optimized encounter serializer with N+1 query prevention."""

    notes = OptimizedEncounterNoteSerializer(many=True, read_only=True)
    attachments = OptimizedEncounterAttachmentSerializer(many=True, read_only=True)

    # Optimized related field lookups
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    physician_name = serializers.CharField(source='primary_physician.get_full_name', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)

    class Meta:
        model = Encounter
        fields = [
            "id",
            "hospital",
            "hospital_name",
            "patient",
            "patient_name",
            "primary_physician",
            "physician_name",
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


# Legacy serializer for backward compatibility
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


class NotificationSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    message = serializers.CharField()
    type = serializers.CharField()
    severity = serializers.CharField(default="info")
    created_at = serializers.DateTimeField(read_only=True)
    read = serializers.BooleanField(default=False)


class QualityMetricSerializer(serializers.Serializer):
    metric_name = serializers.CharField()
    value = serializers.FloatField()
    target_value = serializers.FloatField(required=False)
    unit = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField()
    hospital_id = serializers.IntegerField(required=False)
