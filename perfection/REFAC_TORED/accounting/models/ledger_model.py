import uuid
from typing import Optional

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .account_model import Account, BaseModel


class Ledger(BaseModel):
    """
    Accounting ledger entries model for healthcare financial tracking.

    Follows SRP: Manages ledger entry data and basic relationships only.
    Complex business logic (balancing, reconciliation) delegated to LedgerService.

    Fields:
        account: Foreign key to Account model
        entry_type: Type of ledger entry (debit/credit/adjustment)
        amount: Transaction amount with validation
        reference_number: External reference for reconciliation
        description: Detailed entry description
    """

    ENTRY_TYPES = [
        ("debit", "Debit"),
        ("credit", "Credit"),
        ("adjustment", "Adjustment"),
        ("refund", "Refund"),
        ("payment", "Payment"),
    ]

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
        help_text="Associated account for this ledger entry",
    )
    entry_type = models.CharField(
        max_length=20, choices=ENTRY_TYPES, help_text="Type of ledger entry"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(99999999.99)],
        help_text="Ledger entry amount",
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="External reference number for reconciliation",
    )
    description = models.TextField(
        blank=True, help_text="Detailed description of ledger entry"
    )

    class Meta:
        db_table = "ledgers"
        verbose_name = "Ledger Entry"
        verbose_name_plural = "Ledger Entries"
        indexes = [
            models.Index(fields=["account", "entry_type", "is_active"]),
            models.Index(fields=["reference_number"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    entry_type__in=[
                        "debit",
                        "credit",
                        "adjustment",
                        "refund",
                        "payment",
                    ]
                ),
                name="valid_entry_type",
            )
        ]

    def validate_amount(self, expected_type: str) -> None:
        """
        Basic amount validation based on entry type.
        Complex validation logic should be in LedgerService.
        """
        if self.amount <= 0:
            raise ValueError("Ledger amount must be positive")

    def get_balance_impact(self) -> float:
        """
        Calculate balance impact based on entry type.
        Returns positive for credits, negative for debits.
        """
        impact_map = {
            "debit": -1,
            "credit": 1,
            "adjustment": 0,
            "refund": 1,
            "payment": -1,
        }
        return self.amount * impact_map.get(self.entry_type, 0)
