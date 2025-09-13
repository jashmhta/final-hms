from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model that adds created_at and updated_at timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(TimeStampedModel):
    """Abstract base model with a required hospital FK for multi-tenancy."""

    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)ss",
    )

    class Meta:
        abstract = True


class AuditLog(TimeStampedModel):
    """Simple audit log for model-level actions with optional user and hospital."""

    ACTION_CHOICES = (
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("ACTION", "Action"),
    )
    hospital = models.ForeignKey(
        "hospitals.Hospital", on_delete=models.SET_NULL, null=True, blank=True
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    model = models.CharField(max_length=128)
    object_id = models.CharField(max_length=64)
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
