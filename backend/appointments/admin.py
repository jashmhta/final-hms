from django.contrib import admin
from .models import (
    Appointment,
    AppointmentHistory,
    AppointmentReminder,
    AppointmentTemplate,
    Resource,
    WaitList,
)
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "primary_provider",
        "hospital",
        "start_at",
        "end_at",
        "status",
        "appointment_type",
    )
    list_filter = (
        "hospital",
        "primary_provider",
        "status",
        "appointment_type",
        "priority",
    )
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "primary_provider__username",
        "reason",
        "appointment_number",
    )
    autocomplete_fields = ("patient", "primary_provider", "hospital", "template")
    readonly_fields = ("uuid", "appointment_number", "created_at", "updated_at")
    filter_horizontal = ("additional_providers",)
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "uuid",
                    "appointment_number",
                    "patient",
                    "primary_provider",
                    "additional_providers",
                )
            },
        ),
        (
            "Appointment Details",
            {
                "fields": (
                    "appointment_type",
                    "template",
                    "start_at",
                    "end_at",
                    "status",
                    "priority",
                )
            },
        ),
        (
            "Clinical Information",
            {"fields": ("reason", "chief_complaint", "clinical_notes")},
        ),
        (
            "Location & Resources",
            {"fields": ("location", "room", "is_telehealth", "telehealth_link")},
        ),
        (
            "Administrative",
            {
                "fields": (
                    "hospital",
                    "scheduled_by",
                    "confirmation_required",
                    "is_confidential",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
@admin.register(AppointmentTemplate)
class AppointmentTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "appointment_type",
        "duration_minutes",
        "hospital",
        "is_active",
    )
    list_filter = ("hospital", "appointment_type", "is_active", "allows_online_booking")
    search_fields = ("name", "description", "specialty_required")
    autocomplete_fields = ("hospital",)
@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "resource_type",
        "hospital",
        "capacity",
        "is_active",
        "is_bookable",
    )
    list_filter = ("hospital", "resource_type", "is_active", "is_bookable")
    search_fields = ("name", "description", "location")
    autocomplete_fields = ("hospital",)
@admin.register(WaitList)
class WaitListAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "provider",
        "appointment_type",
        "priority",
        "is_active",
        "created_at",
    )
    list_filter = ("hospital", "provider", "appointment_type", "priority", "is_active")
    search_fields = ("patient__first_name", "patient__last_name", "reason")
    autocomplete_fields = ("patient", "provider", "hospital", "created_by")
    readonly_fields = (
        "notified_count",
        "last_notification",
        "created_at",
        "updated_at",
    )
@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = (
        "appointment",
        "reminder_type",
        "scheduled_for",
        "status",
        "sent_at",
    )
    list_filter = ("reminder_type", "status", "scheduled_for")
    search_fields = (
        "appointment__patient__first_name",
        "appointment__patient__last_name",
        "subject",
    )
    autocomplete_fields = ("appointment",)
    readonly_fields = ("sent_at", "delivered_at", "created_at", "updated_at")
@admin.register(AppointmentHistory)
class AppointmentHistoryAdmin(admin.ModelAdmin):
    list_display = ("appointment", "action", "changed_by", "timestamp")
    list_filter = ("action", "timestamp", "changed_by")
    search_fields = (
        "appointment__patient__first_name",
        "appointment__patient__last_name",
        "notes",
    )
    autocomplete_fields = ("appointment", "changed_by")
    readonly_fields = ("timestamp",)
    def has_add_permission(self, request):
        return False  
    def has_change_permission(self, request, obj=None):
        return False  