from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("hospital", "patient", "rating", "submitted_at")
    list_filter = ("hospital", "rating")
    autocomplete_fields = ("hospital", "patient")
