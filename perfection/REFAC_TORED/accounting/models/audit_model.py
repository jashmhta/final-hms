import uuid
from typing import Any, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db import models

from .account_model import BaseModel
from .transaction_model import Transaction


class Audit(BaseModel):
    """
    Audit trail model for tracking changes in healthcare accounting system.

    Follows SRP: Manages audit trail data persistence and basic validation only.
    Complex audit analysis and reporting delegated to AuditService.

    Fields:
        transaction: Foreign key to Transaction (if auditing a transaction)
        action: Type of audit action (create, update, delete, etc.)
        entity_type: Type of entity being audited (Account, Ledger, Transaction)
        entity_id: ID of the audited entity
        old_values: JSON field storing previous values
        new_values: JSON field storing current values
        changed_fields: List of fields that were modified
        user_id: ID of user who made the change
        ip_address: IP address of the user (for security auditing)
        audit_notes: Additional audit information
    """

    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("view", "View"),
        ("revert", "Revert"),
        ("system", "System Action"),
    ]

    ENTITY_TYPES = [
        ("account", "Account"),
        ("ledger", "Ledger"),
        ("transaction", "Transaction"),
        ("audit", "Audit"),
        ("system", "System"),
    ]

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_trail",
        help_text="Associated transaction (if auditing transaction changes)",
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type of audit action performed",
    )
    entity_type = models.CharField(
        max_length=20, choices=ENTITY_TYPES, help_text="Type of entity being audited"
    )
    entity_id = models.UUIDField(help_text="ID of the audited entity")
    old_values = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Previous values of the entity before change",
    )
    new_values = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Current values of the entity after change",
    )
    changed_fields = models.JSONField(
        default=list, help_text="List of fields that were modified"
    )
    user_id = models.IntegerField(
        null=True, blank=True, help_text="ID of user who performed the action"
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, help_text="IP address of the user for security auditing"
    )
    audit_notes = models.TextField(
        blank=True, help_text="Additional notes about the audit event"
    )

    class Meta:
        db_table = "audits"
        verbose_name = "Audit Trail"
        verbose_name_plural = "Audit Trails"
        indexes = [
            models.Index(fields=["entity_type", "entity_id", "is_active"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user_id"]),
            models.Index(fields=["transaction"]),
            models.Index(fields=["entity_type", "action", "created_at"]),
        ]

    def clean(self) -> None:
        """
        Validate audit trail integrity.
        Complex audit validation should be in AuditService.
        """
        super().clean()
        if not self.entity_id:
            raise ValidationError("Entity ID is required for audit records")

        if self.action not in dict(self.ACTION_CHOICES).keys():
            raise ValidationError(f"Invalid action type: {self.action}")

        if self.changed_fields and not isinstance(self.changed_fields, list):
            raise ValidationError("Changed fields must be a list")

        # Ensure audit records are never deleted (immutable)
        if not self.is_active:
            raise ValidationError("Audit records cannot be deleted")

    def generate_audit_summary(self) -> str:
        """
        Generate a human-readable summary of the audit event.
        Detailed analysis should be in AuditService.
        """
        summary = f"{self.get_action_display()} on {self.get_entity_type_display()} {self.entity_id}"
        if self.user_id:
            summary += f" by user {self.user_id}"
        if self.changed_fields:
            summary += f" (changed: {', '.join(self.changed_fields[:3])})"
        return summary

    @classmethod
    def create_system_audit(
        cls, entity_type: str, entity_id: str, action: str, notes: str = ""
    ) -> "Audit":
        """
        Create a system-generated audit record.
        This method is for internal system use only.
        """
        return cls.objects.create(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            audit_notes=notes,
            is_active=True,  # Audit records are always active
        )
