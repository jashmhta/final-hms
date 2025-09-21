from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "last_name",
        "first_name",
        "hospital",
        "date_of_birth",
        "status",
        "medical_record_number",
    )
    search_fields = (
        "last_name",
        "first_name",
        "phone_primary",
        "email",
        "medical_record_number",
        "external_id",
    )
    list_filter = (
        "hospital",
        "status",
        "gender",
        "preferred_language",
        "marital_status",
    )
    autocomplete_fields = (
        "hospital",
        "primary_care_physician",
        "referring_physician",
        "created_by",
    )
    readonly_fields = ("uuid", "medical_record_number", "created_at", "updated_at")
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "uuid",
                    "medical_record_number",
                    "external_id",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "suffix",
                    "preferred_name",
                )
            },
        ),
        (
            "Demographics",
            {
                "fields": (
                    "date_of_birth",
                    "gender",
                    "marital_status",
                    "race",
                    "ethnicity",
                    "religion",
                    "preferred_language",
                    "interpreter_needed",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "phone_primary",
                    "phone_secondary",
                    "email",
                    "preferred_contact_method",
                    "allow_sms",
                    "allow_email",
                )
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "zip_code",
                    "country",
                )
            },
        ),
        (
            "Medical Information",
            {
                "fields": (
                    "blood_type",
                    "weight_kg",
                    "height_cm",
                    "primary_care_physician",
                    "referring_physician",
                )
            },
        ),
        (
            "Status & Administrative",
            {
                "fields": (
                    "hospital",
                    "status",
                    "date_of_death",
                    "cause_of_death",
                    "vip_status",
                    "confidential",
                )
            },
        ),
        (
            "Preferences & Directives",
            {
                "fields": (
                    "organ_donor",
                    "advance_directive_on_file",
                    "do_not_resuscitate",
                    "healthcare_proxy",
                )
            },
        ),
        (
            "System Fields",
            {
                "fields": (
                    "created_by",
                    "last_updated_by",
                    "notes",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )
