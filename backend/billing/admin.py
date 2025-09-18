from django.contrib import admin
from .models import Bill, BillLineItem, Payment, ServiceCatalog
@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "hospital",
        "total_cents",
        "paid_cents",
        "status",
        "insurance_claim_status",
    )
    list_filter = ("hospital", "status", "insurance_claim_status")
    search_fields = ("patient__first_name", "patient__last_name")
    autocomplete_fields = ("patient", "appointment", "hospital")
@admin.register(BillLineItem)
class BillLineItemAdmin(admin.ModelAdmin):
    list_display = (
        "bill",
        "description",
        "quantity",
        "unit_price_cents",
        "amount_cents",
    )
    autocomplete_fields = ("bill", "hospital")
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("bill", "amount_cents", "method", "received_at")
    autocomplete_fields = ("bill", "hospital")
@admin.register(ServiceCatalog)
class ServiceCatalogAdmin(admin.ModelAdmin):
    list_display = ("hospital", "code", "name", "price_cents", "active")
    search_fields = ("code", "name")
    list_filter = ("active",)
    autocomplete_fields = ("hospital",)