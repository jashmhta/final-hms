from core.models import TenantModel, TimeStampedModel
from django.db import models


class Medication(TenantModel):
    name = models.CharField(max_length=255)
    strength = models.CharField(max_length=100, blank=True)
    form = models.CharField(max_length=100, blank=True)
    stock_quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True)
    supplier = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (("hospital", "name", "strength", "form"),)
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} {self.strength} {self.form}".strip()


class Prescription(TenantModel):
    encounter = models.ForeignKey(
        "ehr.Encounter", on_delete=models.CASCADE, related_name="prescriptions"
    )
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="prescriptions"
    )
    doctor = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, related_name="prescriptions"
    )
    medication = models.ForeignKey(
        Medication, on_delete=models.PROTECT, related_name="prescriptions"
    )
    dosage_instructions = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)
    is_dispensed = models.BooleanField(default=False)
    dispensed_at = models.DateTimeField(null=True, blank=True)


class InventoryTransaction(TenantModel):
    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name="transactions"
    )
    change = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True)
    performed_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
