from django.contrib import admin

from .models import LabOrder, LabResult, LabTest


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("name", "hospital", "price_cents")
    search_fields = ("name",)
    autocomplete_fields = ("hospital",)


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "test", "ordered_at", "status")
    list_filter = ("status",)
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "doctor__username",
        "test__name",
    )
    autocomplete_fields = ("patient", "doctor", "test", "hospital")


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("order", "value", "unit", "reported_at")
    autocomplete_fields = ("order", "hospital")
