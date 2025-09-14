import uuid
from typing import Optional

from django.core.validators import MinValueValidator
from django.db import models


class BaseModel(models.Model):
    """Abstract base model with common fields for all accounting entities."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {self.id}"

    def soft_delete(self) -> None:
        """Mark as inactive instead of hard delete."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])


class Account(BaseModel):
    """
    Patient or provider account model for healthcare accounting system.

    Follows SRP: Handles only account data persistence and basic validation.
    Business logic delegated to AccountService.

    Fields:
        account_type: Type of account (patient/provider)
        balance: Current account balance with validation
        patient_id: Optional foreign key to patient (for patient accounts)
        provider_id: Optional foreign key to provider (for provider accounts)
    """

    account_type = models.CharField(
        max_length=50,
        choices=[("patient", "Patient"), ("provider", "Provider")],
        help_text="Type of healthcare account",
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        help_text="Current account balance",
    )
    patient_id = models.IntegerField(
        null=True, blank=True, help_text="Patient ID for patient accounts"
    )
    provider_id = models.IntegerField(
        null=True, blank=True, help_text="Provider ID for provider accounts"
    )

    class Meta:
        db_table = "accounts"
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        indexes = [
            models.Index(fields=["account_type", "is_active"]),
            models.Index(fields=["patient_id"]),
            models.Index(fields=["provider_id"]),
        ]

    def validate_balance(self, amount: float) -> None:
        """
        Validate balance after transaction (business logic should be in service).
        This is a simple data validation example.
        """
        if self.balance + amount < 0:
            raise ValueError("Insufficient funds")
