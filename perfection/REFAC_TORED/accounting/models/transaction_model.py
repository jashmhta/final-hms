import uuid
from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .account_model import BaseModel
from .ledger_model import Ledger


class Transaction(BaseModel):
    """
    Financial transaction model for healthcare accounting system.

    Follows SRP: Manages transaction data persistence and basic validation only.
    Complex business logic (payment processing, insurance claims) delegated to TransactionService.

    Fields:
        ledger: Foreign key to Ledger entry
        transaction_type: Type of transaction (payment, claim, copay, etc.)
        status: Transaction status (pending, completed, failed, refunded)
        amount: Transaction amount with validation
        insurance_claim_id: Reference to insurance claim (if applicable)
        copay_amount: Patient copay portion
        description: Transaction description
        metadata: JSON field for additional transaction data
    """

    TRANSACTION_TYPES = [
        ("payment", "Patient Payment"),
        ("insurance_claim", "Insurance Claim"),
        ("copay", "Copay Collection"),
        ("refund", "Patient Refund"),
        ("adjustment", "Billing Adjustment"),
        ("write_off", "Write-off"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
        ("disputed", "Disputed"),
    ]

    ledger = models.ForeignKey(
        Ledger,
        on_delete=models.CASCADE,
        related_name="transactions",
        help_text="Associated ledger entry for this transaction",
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES,
        help_text="Type of financial transaction",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current status of transaction",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(99999999.99)],
        help_text="Transaction amount",
    )
    insurance_claim_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Insurance claim reference number",
    )
    copay_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        help_text="Patient copay amount",
    )
    description = models.TextField(
        blank=True, help_text="Detailed transaction description"
    )
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional transaction metadata"
    )
    transaction_date = models.DateTimeField(
        auto_now_add=True, help_text="Date and time of transaction"
    )

    class Meta:
        db_table = "transactions"
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        indexes = [
            models.Index(fields=["ledger", "status", "is_active"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["insurance_claim_id"]),
            models.Index(fields=["status", "transaction_date"]),
        ]

    def clean(self) -> None:
        """
        Validate transaction data integrity.
        Complex business validation should be in TransactionService.
        """
        super().clean()
        if self.amount < self.copay_amount:
            raise ValidationError("Transaction amount cannot be less than copay amount")

        # Ensure ledger account type matches transaction type
        if self.ledger and self.ledger.account:
            if (
                self.transaction_type == "copay"
                and self.ledger.account.account_type != "patient"
            ):
                raise ValidationError(
                    "Copay transactions must be associated with patient accounts"
                )

    def update_status(
        self, new_status: str, metadata_update: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update transaction status with optional metadata.
        Audit trail should be handled by AuditService.
        """
        if new_status not in dict(self.STATUS_CHOICES).keys():
            raise ValueError(f"Invalid status: {new_status}")
        self.status = new_status
        if metadata_update:
            self.metadata.update(metadata_update)
        self.save(update_fields=["status", "metadata", "updated_at"])
