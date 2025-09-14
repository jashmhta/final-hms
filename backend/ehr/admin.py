from django.contrib import admin

from .models import (
    Allergy,
    Assessment,
    ClinicalNote,
    Encounter,
    EncounterAttachment,
    PlanOfCare,
    VitalSigns,
)


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "primary_physician",
        "hospital",
        "appointment",
        "encounter_type",
        "encounter_status",
    )
    list_filter = (
        "hospital",
        "primary_physician",
        "encounter_type",
        "encounter_status",
        "priority_level",
    )
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "primary_physician__username",
        "encounter_number",
    )
<<<<<<< HEAD
    autocomplete_fields = ("patient", "primary_physician", "hospital", "appointment")
=======
    autocomplete_fields = (
        "patient",
        "primary_physician",
        "hospital",
        "appointment",
    )
>>>>>>> transform-refactor
    readonly_fields = ("encounter_number", "created_at", "updated_at")
    filter_horizontal = ("consulting_physicians",)


@admin.register(VitalSigns)
class VitalSignsAdmin(admin.ModelAdmin):
    list_display = (
        "encounter",
        "recorded_by",
        "temperature_celsius",
        "systolic_bp",
        "diastolic_bp",
        "heart_rate",
        "recorded_at",
    )
    list_filter = ("encounter__hospital", "recorded_by", "recorded_at")
<<<<<<< HEAD
    search_fields = ("encounter__patient__first_name", "encounter__patient__last_name")
=======
    search_fields = (
        "encounter__patient__first_name",
        "encounter__patient__last_name",
    )
>>>>>>> transform-refactor
    autocomplete_fields = ("encounter", "recorded_by")


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "encounter",
        "diagnosis_type",
        "diagnosis_code",
        "diagnosis_description",
        "status",
    )
<<<<<<< HEAD
    list_filter = ("encounter__hospital", "diagnosis_type", "status", "severity")
=======
    list_filter = (
        "encounter__hospital",
        "diagnosis_type",
        "status",
        "severity",
    )
>>>>>>> transform-refactor
    search_fields = (
        "encounter__patient__first_name",
        "encounter__patient__last_name",
        "diagnosis_code",
        "diagnosis_description",
    )
    autocomplete_fields = ("encounter", "diagnosed_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PlanOfCare)
class PlanOfCareAdmin(admin.ModelAdmin):
    list_display = ("encounter", "plan_type", "title", "status", "ordered_by")
    list_filter = ("encounter__hospital", "plan_type", "status", "priority")
    search_fields = (
        "encounter__patient__first_name",
        "encounter__patient__last_name",
        "title",
        "description",
    )
    autocomplete_fields = ("encounter", "ordered_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display = ("encounter", "note_type", "author", "is_signed", "created_at")
    list_filter = ("encounter__hospital", "note_type", "is_signed", "is_amended")
=======
    list_display = (
        "encounter",
        "note_type",
        "author",
        "is_signed",
        "created_at",
    )
    list_filter = (
        "encounter__hospital",
        "note_type",
        "is_signed",
        "is_amended",
    )
>>>>>>> transform-refactor
    search_fields = (
        "encounter__patient__first_name",
        "encounter__patient__last_name",
        "content",
    )
<<<<<<< HEAD
    autocomplete_fields = ("encounter", "author", "co_signed_by", "original_note")
=======
    autocomplete_fields = (
        "encounter",
        "author",
        "co_signed_by",
        "original_note",
    )
>>>>>>> transform-refactor
    readonly_fields = ("created_at", "updated_at", "signed_at")


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display = ("patient", "allergen", "allergen_type", "severity", "status")
=======
    list_display = (
        "patient",
        "allergen",
        "allergen_type",
        "severity",
        "status",
    )
>>>>>>> transform-refactor
    list_filter = ("patient__hospital", "allergen_type", "severity", "status")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "allergen",
        "reaction",
    )
    autocomplete_fields = ("patient", "reported_by", "verified_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(EncounterAttachment)
class EncounterAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "encounter",
        "file_type",
        "description",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("encounter__hospital", "file_type", "created_at")
    search_fields = (
        "encounter__patient__first_name",
        "encounter__patient__last_name",
        "description",
    )
    autocomplete_fields = ("encounter", "uploaded_by")
    readonly_fields = ("created_at", "updated_at")
