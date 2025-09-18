from core.models import TenantModel
from django.db import models
class Feedback(TenantModel):
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.SET_NULL,
        null=True,
        related_name="feedback",
    )
    rating = models.IntegerField(default=5)
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-submitted_at"]