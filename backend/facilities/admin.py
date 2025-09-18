from django.contrib import admin
from .models import Bed, Ward
@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ("hospital", "name", "floor")
    search_fields = ("name",)
    autocomplete_fields = ("hospital",)
@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ("hospital", "ward", "number", "is_occupied", "occupant")
    list_filter = ("is_occupied",)
    autocomplete_fields = ("hospital", "ward", "occupant")