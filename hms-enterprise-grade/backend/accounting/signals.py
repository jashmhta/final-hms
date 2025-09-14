"""
Django signals for automatic accounting entry generation.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    AccountingAuditLog,
    AccountingInvoice,
    AccountingPayment,
    BookLock,
    Expense,
    PayrollEntry,
)
from .utils import DoubleEntryBookkeeping


@receiver(post_save, sender=AccountingInvoice)
def create_invoice_ledger_entries(sender, instance, created, **kwargs):
    """Automatically create ledger entries when invoice is created"""
    if created and instance.status != "DRAFT":
        # Check if books are locked for this date
        lock_exists = BookLock.objects.filter(
            hospital=instance.hospital, lock_date__gte=instance.invoice_date
        ).exists()

        if not lock_exists:
            try:
                DoubleEntryBookkeeping.post_invoice_entries(instance)
            except Exception as e:
                # Log the error but don't prevent invoice creation
                print(
                    f"Error creating ledger entries for invoice {instance.invoice_number}: {e}"
                )


@receiver(post_save, sender=AccountingPayment)
def create_payment_ledger_entries(sender, instance, created, **kwargs):
    """Automatically create ledger entries when payment is received"""
    if created and instance.status == "CLEARED":
        # Check if books are locked for this date
        lock_exists = BookLock.objects.filter(
            hospital=instance.hospital, lock_date__gte=instance.payment_date
        ).exists()

        if not lock_exists:
            try:
                DoubleEntryBookkeeping.post_payment_entries(instance)
            except Exception as e:
                # Log the error but don't prevent payment creation
                print(
                    f"Error creating ledger entries for payment {instance.payment_number}: {e}"
                )


@receiver(post_save, sender=Expense)
def create_expense_ledger_entries(sender, instance, created, **kwargs):
    """Automatically create ledger entries when expense is approved"""
    if instance.is_approved and not created:
        # Check if books are locked for this date
        lock_exists = BookLock.objects.filter(
            hospital=instance.hospital, lock_date__gte=instance.expense_date
        ).exists()

        if not lock_exists:
            try:
                DoubleEntryBookkeeping.post_expense_entries(instance)
            except Exception as e:
                # Log the error but don't prevent expense approval
                print(
                    f"Error creating ledger entries for expense {instance.expense_number}: {e}"
                )


@receiver(post_save, sender=PayrollEntry)
def create_payroll_ledger_entries(sender, instance, created, **kwargs):
    """Automatically create ledger entries when payroll is approved"""
    if instance.status == "APPROVED" and not created:
        # Check if books are locked for this date
        lock_exists = BookLock.objects.filter(
            hospital=instance.hospital, lock_date__gte=instance.pay_date
        ).exists()

        if not lock_exists:
            try:
                DoubleEntryBookkeeping.post_payroll_entries(instance)
            except Exception as e:
                # Log the error but don't prevent payroll approval
                print(f"Error creating ledger entries for payroll {instance.id}: {e}")


# Audit trail signals
@receiver(post_save)
def log_model_changes(sender, instance, created, **kwargs):
    """Log all model changes for audit trail"""
    # Only log accounting models
    if not sender._meta.app_label == "accounting":
        return

    # Skip audit logs to prevent recursion
    if sender == AccountingAuditLog:
        return

    try:
        # Get the user from the request (if available)
        # This would require middleware to store request in thread-local storage
        user = getattr(instance, "created_by", None) or getattr(
            instance, "updated_by", None
        )

        action_type = "CREATE" if created else "UPDATE"

        # Create audit log entry
        AccountingAuditLog.objects.create(
            hospital=getattr(instance, "hospital", None),
            user=user,
            action_type=action_type,
            table_name=sender._meta.db_table,
            record_id=str(instance.pk),
            new_values={
                "model": sender.__name__,
                "timestamp": timezone.now().isoformat(),
            },
        )
    except Exception as e:
        # Don't let audit logging break the main operation
        print(f"Error logging audit trail: {e}")


@receiver(pre_delete)
def log_model_deletions(sender, instance, **kwargs):
    """Log model deletions for audit trail"""
    # Only log accounting models
    if not sender._meta.app_label == "accounting":
        return

    # Skip audit logs to prevent recursion
    if sender == AccountingAuditLog:
        return

    try:
        # Create audit log entry for deletion
        AccountingAuditLog.objects.create(
            hospital=getattr(instance, "hospital", None),
            action_type="DELETE",
            table_name=sender._meta.db_table,
            record_id=str(instance.pk),
            old_values={
                "model": sender.__name__,
                "deleted_at": timezone.now().isoformat(),
            },
        )
    except Exception as e:
        # Don't let audit logging break the main operation
        print(f"Error logging deletion audit trail: {e}")
