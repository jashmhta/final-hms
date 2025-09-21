from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SecurityEvent

User = get_user_model()


@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    if created:
        SecurityEvent.objects.create(
            user=instance,
            event_type="SYSTEM_ADMIN",
            severity="LOW",
            description="User account created",
            metadata={"action": "account_created"},
        )
    else:
        if instance.failed_login_attempts > 0:
            SecurityEvent.objects.create(
                user=instance,
                event_type="LOGIN_FAILED",
                severity="LOW",
                description=f"Failed login attempts: {instance.failed_login_attempts}",
                metadata={"failed_attempts": instance.failed_login_attempts},
            )
        if instance.account_locked_until:
            SecurityEvent.objects.create(
                user=instance,
                event_type="ACCOUNT_LOCKED",
                severity="HIGH",
                description="Account locked due to security policy",
                metadata={"lock_duration": str(instance.account_locked_until)},
            )
