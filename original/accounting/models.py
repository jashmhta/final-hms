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
    account_type = models.CharField(
        max_length=50, choices=[("patient", "Patient"), ("provider", "Provider")]
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
class Ledger(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
class Transaction(BaseModel):
    ledger = models.ForeignKey(Ledger, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=50)
    description = models.TextField()
class Audit(BaseModel):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    action = models.CharField(max_length=20)
    old_value = models.JSONField(null=True)
    new_value = models.JSONField(null=True)