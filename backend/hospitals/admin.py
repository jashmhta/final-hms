from django.contrib import admin
from .models import Hospital
@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "timezone")
    search_fields = ("name", "code")
    list_filter = ("is_active", "timezone")