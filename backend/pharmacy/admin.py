from django.contrib import admin

from .models import InventoryTransaction, Medication, Prescription


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "strength",
        "form",
        "hospital",
        "total_stock_quantity",
        "min_stock_level",
    )
    list_filter = ("hospital",)
    search_fields = ("name", "strength", "form")
    autocomplete_fields = ("hospital",)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "medication", "quantity", "is_dispensed")
    search_fields = ("patient__first_name", "patient__last_name")
    autocomplete_fields = ("patient", "doctor", "medication", "hospital", "encounter")


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ("medication", "change", "performed_by", "performed_at")
    autocomplete_fields = ("medication", "performed_by", "hospital")
