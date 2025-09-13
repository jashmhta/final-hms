from core.models import TenantModel
from django.db import models


class Ward(TenantModel):
    name = models.CharField(max_length=128)
    floor = models.CharField(max_length=32, blank=True)

    class Meta:
        unique_together = (("hospital", "name"),)
        ordering = ["name"]


class Bed(TenantModel):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="beds")
    number = models.CharField(max_length=32)
    is_occupied = models.BooleanField(default=False)
    occupant = models.ForeignKey(
        "patients.Patient",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="beds",
    )

    class Meta:
        unique_together = (("hospital", "ward", "number"),)
        ordering = ["ward__name", "number"]
