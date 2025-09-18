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
    if created and instance.status != "DRAFT":
        lock_exists = BookLock.objects.filter(
            hospital=instance.hospital, lock_date__gte=instance.invoice_date
        ).exists()
        if not lock_exists:
            try:
                DoubleEntryBookkeeping.post_invoice_entries(instance)
            except Exception as e:
                print(
                    f"Error creating ledger entries for invoice "
                    f"{instance.invoice_number}: {e}"
                )
@receiver(post_save, sender=AccountingPayment)
def create_payment_ledger_entries(sender, instance, created, **kwargs):
    if created and instance.status == "CLEARED":
        lock_exists = BookLock.objects.filter(
            hospital=instance.hospital, lock_date__gte=instance.payment_date
        ).exists()
        if not lock_exists:
            try:
                DoubleEntryBookkeeping.post_payment_entries(instance)
            except Exception as e:
                print(
                    f"Error creating ledger entries for payment "
                    f"{instance.payment_number}: "
                    f"{e}"
                )
@receiver(post_save, sender=Expense)
def create_expense_ledger_entries(sender, instance, created, **kwargs):
    if instance.is_approved and not created:
        lock_exists = BookLock.objects.filter(
            hospital=instance.hospital, lock_date__gte=instance.expense_date
        ).exists()
        if not lock_exists:
            try:
                DoubleEntryBookkeeping.post_expense_entries(instance)
            except Exception as e:
                print(
                    f"Error creating ledger entries for expense "
                    f"{instance.expense_number}: "
                    f"{e}"
                )
@receiver(post_save, sender=PayrollEntry)
def create_payroll_ledger_entries(sender, instance, created, **kwargs):
    if instance.status == "APPROVED" and not created:
        lock_exists = BookLock.objects.filter(
            hospital=instance.hospital, lock_date__gte=instance.pay_date
        ).exists()
        if not lock_exists:
            try:
                DoubleEntryBookkeeping.post_payroll_entries(instance)
            except Exception as e:
                print(
                    f"Error creating ledger entries for payroll " f"{instance.id}: {e}"
                )
@receiver(post_save)
def log_model_changes(sender, instance, created, **kwargs):
    if not sender._meta.app_label == "accounting":
        return
    if sender == AccountingAuditLog:
        return
    try:
        user = getattr(instance, "created_by", None) or getattr(
            instance, "updated_by", None
        )
        action_type = "CREATE" if created else "UPDATE"
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
        print(f"Error logging audit trail: {e}")
@receiver(pre_delete)
def log_model_deletions(sender, instance, **kwargs):
    if not sender._meta.app_label == "accounting":
        return
    if sender == AccountingAuditLog:
        return
    try:
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
        print(f"Error logging deletion audit trail: {e}")