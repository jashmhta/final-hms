<<<<<<< HEAD
from core.models import TenantModel, TimeStampedModel
=======
from core.models import TenantModel
>>>>>>> transform-refactor
from django.db import models


class Bill(TenantModel):
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="bills"
    )
    appointment = models.ForeignKey(
<<<<<<< HEAD
        "appointments.Appointment", on_delete=models.SET_NULL, null=True, blank=True
=======
        "appointments.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
>>>>>>> transform-refactor
    )
    total_cents = models.IntegerField(default=0)
    paid_cents = models.IntegerField(default=0)
    status = models.CharField(
        max_length=16,
        default="DUE",
        choices=[("DUE", "Due"), ("PARTIAL", "Partial"), ("PAID", "Paid")],
    )
    insurance_claim_status = models.CharField(
        max_length=32,
        default="NOT_SUBMITTED",
        choices=[
            ("NOT_SUBMITTED", "Not Submitted"),
            ("SUBMITTED", "Submitted"),
            ("RECEIVED", "Received"),
        ],
    )
    referral_source = models.CharField(max_length=255, blank=True)
    discount_cents = models.IntegerField(default=0)
    net_cents = models.IntegerField(default=0)

    def recalc(self):
        total = sum(item.amount_cents for item in self.items.all())
        self.total_cents = total
        paid = sum(p.amount_cents for p in self.payments.all())
        self.paid_cents = paid
        self.net_cents = max(total - self.discount_cents, 0)
        self.status = (
            "PAID"
            if paid >= self.net_cents and self.net_cents > 0
            else ("PARTIAL" if 0 < paid < self.net_cents else "DUE")
        )
<<<<<<< HEAD
        self.save(update_fields=["total_cents", "paid_cents", "net_cents", "status"])
=======
        self.save(
            update_fields=[
                "total_cents",
                "paid_cents",
                "net_cents",
                "status",
            ]
        )
>>>>>>> transform-refactor


class BillLineItem(TenantModel):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)
    unit_price_cents = models.IntegerField(default=0)
    amount_cents = models.IntegerField(default=0)
    department = models.CharField(max_length=64, default="GENERAL")
    is_outsourced = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.amount_cents = self.quantity * self.unit_price_cents
        super().save(*args, **kwargs)
        self.bill.recalc()


class Payment(TenantModel):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="payments")
    amount_cents = models.IntegerField()
    method = models.CharField(max_length=32, default="CASH")
    reference = models.CharField(max_length=255, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.bill.recalc()


class ServiceCatalog(TenantModel):
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    price_cents = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("hospital", "code"),)
        ordering = ["code"]


class Asset(TenantModel):
    name = models.CharField(max_length=255)
    purchase_date = models.DateField()
    cost_cents = models.IntegerField(default=0)
    depreciation_years = models.IntegerField(default=5)

    def annual_depreciation_cents(self) -> int:
        return self.cost_cents // max(self.depreciation_years, 1)


class DepartmentBudget(TenantModel):
    department = models.CharField(max_length=64)
    period = models.CharField(max_length=16, help_text="YYYY-MM")
    budget_cents = models.IntegerField(default=0)
    alerts_threshold_pct = models.IntegerField(default=80)
