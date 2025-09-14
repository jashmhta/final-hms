from core.models import TenantModel, TimeStampedModel
from django.db import models
<<<<<<< HEAD
=======
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
>>>>>>> transform-refactor


class Medication(TenantModel):
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True)
    brand_name = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(
        "DrugCategory", on_delete=models.SET_NULL, null=True, blank=True
    )
    manufacturer = models.ForeignKey(
        "Manufacturer", on_delete=models.SET_NULL, null=True, blank=True
    )
    strength = models.CharField(max_length=100, blank=True)
    form = models.CharField(max_length=100, blank=True)
    route = models.CharField(max_length=50, blank=True)  # Oral, IV, etc.
    total_stock_quantity = models.IntegerField(default=0)  # Sum across batches
    min_stock_level = models.IntegerField(default=0)
    max_stock_level = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preferred_supplier = models.ForeignKey(
        "Supplier", on_delete=models.SET_NULL, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    is_discontinued = models.BooleanField(default=False)
    ndc_code = models.CharField(
        max_length=20, blank=True, unique=True
    )  # National Drug Code
    storage_instructions = models.TextField(blank=True)
    warnings = models.TextField(blank=True)
    interactions = models.TextField(blank=True)

    class Meta:
        unique_together = (("hospital", "name", "strength", "form"),)
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} {self.strength} {self.form}".strip()

    @property
    def is_low_stock(self):
        return self.total_stock_quantity <= self.reorder_level

    @property
    def expiry_alert(self):
        """Check for batches expiring soon"""
        soon_expiry = self.batches.filter(
            expiry_date__lte=timezone.now().date() + timedelta(days=30),
            quantity_remaining__gt=0,
        ).exists()
        return soon_expiry

    def update_total_stock(self):
        self.total_stock_quantity = sum(
            batch.quantity_remaining for batch in self.batches.all()
        )
        self.save(update_fields=["total_stock_quantity"])


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


class DrugCategory(TenantModel):
    """Medication categories for organization and reporting"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_controlled_substance = models.BooleanField(default=False)
    schedule = models.CharField(
        max_length=20,
        blank=True,  # e.g., Schedule II, Narcotic
        help_text="DEA Schedule for controlled substances",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Manufacturer(TenantModel):
    """Pharmaceutical manufacturers/suppliers"""

    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(TenantModel):
    """External suppliers for inventory"""

    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    lead_time_days = models.PositiveIntegerField(default=7)
    is_preferred = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({'Preferred' if self.is_preferred else 'Standard'})"


class MedicationBatch(TenantModel):
    """Batch/lot tracking for medications"""

    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name="batches"
    )
    batch_number = models.CharField(max_length=100, unique=True)
    expiry_date = models.DateField()
    quantity_received = models.PositiveIntegerField()
    quantity_remaining = models.PositiveIntegerField()
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    received_date = models.DateField()
    received_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="received_batches",
    )
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-received_date"]
        indexes = [
            models.Index(fields=["medication", "batch_number"]),
            models.Index(fields=["expiry_date"]),
        ]

    def __str__(self):
        return (
            f"{self.medication} - Batch {self.batch_number} (Exp: {self.expiry_date})"
        )

    def is_expired(self):
        return self.expiry_date < timezone.now().date()

    def update_quantity(self, dispensed_quantity):
        self.quantity_remaining = max(0, self.quantity_remaining - dispensed_quantity)
        self.save()


class PharmacyOrder(TenantModel):
    """Purchase orders to suppliers"""

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("ORDERED", "Ordered"),
            ("SHIPPED", "Shipped"),
            ("RECEIVED", "Received"),
            ("PARTIAL", "Partial Delivery"),
            ("CANCELLED", "Cancelled"),
        ],
        default="PENDING",
    )
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tracking_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    ordered_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="pharmacy_orders",
    )

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"Order #{self.id} - {self.supplier.name} ({self.status})"


class OrderItem(TenantModel):
    """Items in a pharmacy purchase order"""

    order = models.ForeignKey(
        PharmacyOrder, on_delete=models.CASCADE, related_name="items"
    )
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    batch_number = models.CharField(max_length=100, blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["medication"]

    def __str__(self):
        return f"{self.medication} x{self.quantity_ordered} @ ${self.unit_price}"

    @property
    def total_cost(self):
        return self.quantity_ordered * self.unit_price

    @property
    def is_fully_received(self):
        return self.quantity_received >= self.quantity_ordered


class Dispensation(TenantModel):
    """Medication dispensation records"""

    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="dispensations"
    )
    medication_batch = models.ForeignKey(
        MedicationBatch, on_delete=models.PROTECT, related_name="dispensations"
    )
    quantity_dispensed = models.PositiveIntegerField()
    dispensed_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, related_name="dispensations"
    )
    dispensed_at = models.DateTimeField(auto_now_add=True)
    instructions_given = models.TextField(blank=True)
    patient_education_provided = models.BooleanField(default=False)
    verification_performed = models.BooleanField(default=False)
    cost_to_patient = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["-dispensed_at"]

    def __str__(self):
        return f"Dispensed {self.quantity_dispensed} {self.medication_batch.medication} for {self.prescription.patient}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update batch quantity
        self.medication_batch.update_quantity(self.quantity_dispensed)
        # Mark prescription as dispensed if full quantity
        if self.prescription.quantity <= self.quantity_dispensed:
            self.prescription.is_dispensed = True
            self.prescription.dispensed_at = self.dispensed_at
            self.prescription.save()


class StockAdjustment(TenantModel):
    """Inventory adjustments (theft, damage, expiry)"""

    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    medication_batch = models.ForeignKey(
        MedicationBatch, on_delete=models.SET_NULL, null=True, blank=True
    )
    quantity_adjusted = models.IntegerField()  # Negative for loss
    reason = models.CharField(max_length=255)
    adjustment_type = models.CharField(
        max_length=20,
        choices=[
            ("EXPIRY", "Expiry"),
            ("DAMAGE", "Damage"),
            ("THEFT", "Theft/Loss"),
            ("TRANSFER", "Transfer"),
            ("CORRECTION", "Correction"),
        ],
    )
    adjusted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="stock_adjustments",
    )
    adjusted_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    witnessed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="witnessed_adjustments",
        blank=True,
    )

    class Meta:
        ordering = ["-adjusted_at"]

    def __str__(self):
        return f"{self.adjustment_type}: {self.quantity_adjusted} {self.medication} by {self.adjusted_by}"

    def clean(self):
        if self.quantity_adjusted == 0:
            raise ValidationError("Quantity adjusted cannot be zero.")
        if (
            self.medication_batch
            and self.medication_batch.medication != self.medication
        ):
            raise ValidationError("Batch must belong to the selected medication.")
