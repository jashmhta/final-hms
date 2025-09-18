from core.models import TenantModel
from django.db import models
class LabTest(TenantModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    normal_range = models.CharField(max_length=255, blank=True)
    price_cents = models.IntegerField(default=0)
    class Meta:
        unique_together = (("hospital", "name"),)
        ordering = ["name"]
    def __str__(self) -> str:
        return self.name
class LabOrder(TenantModel):
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="lab_orders"
    )
    doctor = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)
    test = models.ForeignKey(LabTest, on_delete=models.PROTECT)
    ordered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=32,
        default="PENDING",
        choices=[
            ("PENDING", "Pending"),
            ("IN_PROGRESS", "In Progress"),
            ("COMPLETED", "Completed"),
        ],
    )
class LabResult(TenantModel):
    order = models.OneToOneField(
        LabOrder, on_delete=models.CASCADE, related_name="result"
    )
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=64, blank=True)
    observations = models.TextField(blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)