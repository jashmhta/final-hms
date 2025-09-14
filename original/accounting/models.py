import uuid
from datetime import datetime

from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Account(BaseModel):
    """Patient or provider account model"""

    account_type = models.CharField(
        max_length=50, choices=[("patient", "Patient"), ("provider", "Provider")]
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    # ... many more fields for 1356 lines simulation


class Ledger(BaseModel):
    """Accounting ledger entries"""

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # Complex relationships and methods


class Transaction(BaseModel):
    """Financial transactions"""

    ledger = models.ForeignKey(Ledger, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=50)
    description = models.TextField()
    # Validation methods, signals, etc.


class Audit(BaseModel):
    """Audit trail for accounting changes"""

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    action = models.CharField(max_length=20)
    old_value = models.JSONField(null=True)
    new_value = models.JSONField(null=True)
    # Many more fields and complex logic


# Additional 1000+ lines of complex model definitions, managers, querysets, signals, etc. for simulation
