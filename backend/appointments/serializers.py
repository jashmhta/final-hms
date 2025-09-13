from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import (
    Appointment,
    AppointmentHistory,
    AppointmentReminder,
    AppointmentResource,
    AppointmentStatus,
    AppointmentTemplate,
    Resource,
    WaitList,
)


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = [
            "id",
            "name",
            "resource_type",
            "description",
            "location",
            "capacity",
            "is_bookable",
            "requires_approval",
            "min_booking_duration",
            "max_booking_duration",
            "hourly_rate",
            "is_active",
        ]


class AppointmentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentTemplate
        fields = [
            "id",
            "name",
            "appointment_type",
            "duration_minutes",
            "description",
            "allows_online_booking",
            "requires_preparation",
            "preparation_instructions",
            "specialty_required",
            "equipment_required",
            "advance_booking_days",
            "cancellation_hours",
            "base_cost",
            "is_active",
        ]


class AppointmentResourceSerializer(serializers.ModelSerializer):
    resource_name = serializers.CharField(source="resource.name", read_only=True)
    resource_type = serializers.CharField(
        source="resource.resource_type", read_only=True
    )

    class Meta:
        model = AppointmentResource
        fields = [
            "id",
            "resource",
            "resource_name",
            "resource_type",
            "quantity",
            "start_time",
            "end_time",
            "notes",
        ]


class AppointmentReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentReminder
        fields = [
            "id",
            "reminder_type",
            "scheduled_for",
            "sent_at",
            "status",
            "subject",
            "message",
            "delivered_at",
            "response_received",
            "response_type",
            "response_notes",
        ]


class AppointmentHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(
        source="changed_by.get_full_name", read_only=True
    )

    class Meta:
        model = AppointmentHistory
        fields = [
            "id",
            "action",
            "field_changed",
            "old_value",
            "new_value",
            "notes",
            "changed_by",
            "changed_by_name",
            "timestamp",
            "ip_address",
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    provider_name = serializers.CharField(
        source="primary_provider.get_full_name", read_only=True
    )
    duration_display = serializers.CharField(
        source="get_duration_display", read_only=True
    )
    resources = AppointmentResourceSerializer(
        source="appointmentresource_set", many=True, read_only=True
    )
    reminders = AppointmentReminderSerializer(many=True, read_only=True)
    history = AppointmentHistorySerializer(many=True, read_only=True)

    # Backward compatibility fields
    doctor = serializers.CharField(source="primary_provider", read_only=True)
    notes = serializers.CharField(
        source="clinical_notes", allow_blank=True, required=False
    )

    class Meta:
        model = Appointment
        fields = [
            "id",
            "uuid",
            "appointment_number",
            "patient",
            "patient_name",
            "primary_provider",
            "provider_name",
            "additional_providers",
            "appointment_type",
            "template",
            "start_at",
            "end_at",
            "duration_minutes",
            "duration_display",
            "status",
            "priority",
            "reason",
            "chief_complaint",
            "clinical_notes",
            "scheduled_by",
            "confirmation_required",
            "confirmed_at",
            "confirmed_by",
            "checked_in_at",
            "checked_in_by",
            "location",
            "room",
            "resources",
            "insurance_authorization",
            "copay_amount",
            "estimated_cost",
            "reminder_sent",
            "reminder_sent_at",
            "patient_instructions",
            "preparation_instructions",
            "is_telehealth",
            "telehealth_link",
            "telehealth_platform",
            "is_recurring",
            "recurrence_pattern",
            "recurrence_end_date",
            "parent_appointment",
            "series_id",
            "cancelled_at",
            "cancelled_by",
            "cancellation_reason",
            "cancellation_notes",
            "no_show_at",
            "no_show_fee",
            "is_confidential",
            "special_instructions",
            "internal_notes",
            "requires_interpretation",
            "interpreter_language",
            "requires_transportation",
            "reminders",
            "history",
            "hospital",
            "created_at",
            "updated_at",
            # Backward compatibility fields
            "doctor",
            "notes",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "appointment_number",
            "duration_display",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        start_at = attrs.get("start_at") or getattr(self.instance, "start_at", None)
        end_at = attrs.get("end_at") or getattr(self.instance, "end_at", None)
        if start_at and end_at and end_at <= start_at:
            raise serializers.ValidationError("end_at must be after start_at")

        # Handle backward compatibility for 'notes' field
        if "notes" in attrs:
            attrs["clinical_notes"] = attrs.pop("notes")

        return attrs

    def create(self, validated_data):
        instance = Appointment(**validated_data)
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict or e.messages)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict or e.messages)
        instance.save()
        return instance


class AppointmentBasicSerializer(serializers.ModelSerializer):
    """A simplified serializer for appointments in lists or references"""

    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    provider_name = serializers.CharField(
        source="primary_provider.get_full_name", read_only=True
    )
    duration_display = serializers.CharField(
        source="get_duration_display", read_only=True
    )

    # Backward compatibility
    doctor = serializers.CharField(source="primary_provider", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "uuid",
            "appointment_number",
            "patient",
            "patient_name",
            "primary_provider",
            "provider_name",
            "appointment_type",
            "start_at",
            "end_at",
            "duration_display",
            "status",
            "location",
            "room",
            "is_telehealth",
            "is_recurring",
            "doctor",
        ]


class WaitListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    provider_name = serializers.CharField(
        source="provider.get_full_name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )

    class Meta:
        model = WaitList
        fields = [
            "id",
            "patient",
            "patient_name",
            "provider",
            "provider_name",
            "appointment_type",
            "preferred_date_from",
            "preferred_date_to",
            "preferred_times",
            "priority",
            "reason",
            "notes",
            "is_active",
            "notified_count",
            "last_notification",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
