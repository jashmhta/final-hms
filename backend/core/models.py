from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(TimeStampedModel):
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)ss",
    )

    class Meta:
        abstract = True


class AuditLog(TimeStampedModel):
    ACTION_CHOICES = (
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("ACTION", "Action"),
    )
    # hospital = models.ForeignKey(
    #     "hospitals.Hospital", on_delete=models.SET_NULL, null=True, blank=True
    # )  # App not implemented
    user = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    model = models.CharField(max_length=128)
    object_id = models.CharField(max_length=64)
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
