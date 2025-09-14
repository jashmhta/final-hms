from django.contrib import admin

from .models import DutyRoster, LeaveRequest, Shift


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("hospital", "name", "start_time", "end_time")
    search_fields = ("name",)
    autocomplete_fields = ("hospital",)


@admin.register(DutyRoster)
class DutyRosterAdmin(admin.ModelAdmin):
    list_display = ("hospital", "user", "date", "shift")
    list_filter = ("date", "shift")
    autocomplete_fields = ("hospital", "user", "shift")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("hospital", "user", "start_date", "end_date", "status")
    list_filter = ("status",)
    autocomplete_fields = ("hospital", "user")
