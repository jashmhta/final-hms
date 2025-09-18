from django.contrib import admin
from .models import AuditLog
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "hospital", "model", "object_id", "action")
    search_fields = ("model", "object_id", "user__username")
    list_filter = ("action", "hospital")