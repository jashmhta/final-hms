from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import AuditLog, PatientConsent
from .utils import HIPAAEncryptionUtils


@receiver(post_save, sender=PatientConsent)
def log_consent_creation(sender, instance, created, **kwargs):
    """Log all consent creation/modification to audit trail."""
    if created:
        action = "CREATE_CONSENT"
    else:
        action = "UPDATE_CONSENT"

    AuditLog.objects.create(
        user=instance.patient,
        action=action,
        phi_accessed=f"Consent ID: {instance.id}, Type: {instance.consent_type}",
        ip_address="system",  # Signal-based, no direct request context
    )


@receiver(pre_delete, sender=PatientConsent)
def log_consent_deletion(sender, instance, **kwargs):
    """Log consent deletions to audit trail."""
    AuditLog.objects.create(
        user=instance.patient,
        action="DELETE_CONSENT",
        phi_accessed=f"Consent ID: {instance.id} (permanently deleted)",
        ip_address="system",
    )


@receiver(post_save, sender=User)
def log_user_phi_access(sender, instance, created, **kwargs):
    """Log user creation for PHI access tracking."""
    if created:
        AuditLog.objects.create(
            user=instance,
            action="USER_CREATED",
            phi_accessed="New user account created - PHI access enabled",
            ip_address="system",
        )
