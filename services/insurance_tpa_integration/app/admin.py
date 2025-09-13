from django.contrib import admin
from django_auditlog.admin import AuditlogAdminMixin

from .models import Claim, PreAuth, Reimbursement


@admin.register(PreAuth)
class PreAuthAdmin(AuditlogAdminMixin, admin.ModelAdmin):
    list_display = ["id", "patient", "claim_amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["patient__name"]
    readonly_fields = ["created_at", "auditlog"]


@admin.register(Claim)
class ClaimAdmin(AuditlogAdminMixin, admin.ModelAdmin):
    list_display = ["id", "preauth", "billed_amount", "paid_amount", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["preauth__patient__name"]
    readonly_fields = ["created_at", "auditlog"]


@admin.register(Reimbursement)
class ReimbursementAdmin(AuditlogAdminMixin, admin.ModelAdmin):
    list_display = ["id", "claim", "amount", "payment_date", "tpa_transaction_id"]
    list_filter = ["payment_date"]
    search_fields = ["tpa_transaction_id"]
    readonly_fields = ["created_at", "auditlog"]
