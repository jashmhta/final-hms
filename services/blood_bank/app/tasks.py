import smtplib
from datetime import date, timedelta
from email.mime.text import MimeText

from auditlog.models import LogEntry as AuditLog
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.db.models import Q
from django.utils import timezone

from .models import BloodInventory, LogEntry
from .views import BloodInventoryViewSet

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def check_expiry_alerts(self):
    """
    Daily Celery task to check for blood inventory expiring within 7 days
    Runs at 00:00 daily via Celery Beat
    """
    try:
        logger.info("Starting blood expiry alert check")

        # Get inventory expiring within 7 days
        expiry_threshold = date.today() + timedelta(days=7)
        expiring_units = BloodInventory.objects.filter(
            expiry_date__lte=expiry_threshold,
            status="AVAILABLE",
            expiry_date__gt=date.today(),
        ).select_related("donor")

        alert_count = expiring_units.count()
        logger.info(f"Found {alert_count} units expiring soon")

        if alert_count == 0:
            logger.info("No expiring units found")
            return {"status": "success", "alerts_sent": 0}

        # Prepare notification message (HIPAA compliant - no PII)
        message_body = f"""
Blood Bank Expiry Alert
========================

{alert_count} blood units are scheduled to expire within 7 days.

Please review inventory and take appropriate action:
- Transfuse compatible units
- Contact donors for replacement donations
- Consider disposal procedures for expired units

Units affected:
"""

        for unit in expiring_units:
            message_body += f"- Unit ID: {unit.unit_id} | Type: {unit.blood_type} | Expiry: {unit.expiry_date}\n"

        message_body += (
            "\nThis is an automated alert from the Blood Bank Management System."
        )

        # Send email alert to blood bank administrators
        try:
            email_subject = f"Blood Bank Alert: {alert_count} Units Expiring Soon"

            # Send to configured email recipients (from settings)
            if hasattr(settings, "BLOOD_BANK_ALERT_EMAILS"):
                recipients = settings.BLOOD_BANK_ALERT_EMAILS
            else:
                recipients = ["admin@hospital.com"]

            send_mail(
                subject=email_subject,
                message=message_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
            logger.info(f"Email alert sent to {len(recipients)} recipients")

        except Exception as email_error:
            logger.error(f"Failed to send email alert: {email_error}")
            # Retry email sending
            self.retry(countdown=60 * 5)  # Retry in 5 minutes

        # Send SMS alert via Twilio (mock implementation)
        try:
            send_sms_expiry_alert(alert_count)
            logger.info("SMS alert sent successfully")
        except Exception as sms_error:
            logger.error(f"Failed to send SMS alert: {sms_error}")

        # Mark units as 'EXPIRING_SOON' for tracking (add field if needed)
        for unit in expiring_units:
            unit.save()  # Trigger audit log

        return {"status": "success", "alerts_sent": alert_count, "units": alert_count}

    except Exception as e:
        logger.error(f"Expiry alert task failed: {str(e)}")
        raise self.retry(countdown=60 * 10, exc=e)  # Retry in 10 minutes


def send_sms_expiry_alert(unit_count):
    """
    Mock Twilio SMS implementation for expiry alerts
    In production, use actual Twilio client
    """
    try:
        # Mock SMS sending
        sms_message = f"Blood Bank Alert: {unit_count} units expiring within 7 days. Please check inventory."

        # In production:
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     body=sms_message,
        #     from_=settings.TWILIO_PHONE_NUMBER,
        #     to=settings.BLOOD_BANK_ADMIN_PHONE
        # )

        logger.info(f"SMS alert sent: {sms_message}")
        return True

    except Exception as e:
        logger.error(f"SMS alert failed: {e}")
        raise


@shared_task(bind=True, max_retries=2)
def purge_old_audit_logs(self):
    """
    Weekly Celery task to purge audit logs older than 365 days
    HIPAA retention policy compliance
    """
    try:
        logger.info("Starting audit log purge task")

        # Calculate retention threshold (365 days ago)
        retention_date = timezone.now() - timedelta(days=365)

        # Delete old audit logs (all models)
        old_logs = AuditLog.objects.filter(timestamp__lt=retention_date)

        log_count = old_logs.count()
        logger.info(f"Found {log_count} audit logs older than 365 days")

        if log_count == 0:
            logger.info("No old audit logs to purge")
            return {"status": "success", "logs_purged": 0}

        # Perform batch deletion for performance
        deleted_count, _ = old_logs.delete()

        logger.info(f"Purged {deleted_count} audit logs")

        # Log the purge action itself (meta-audit)
        purge_log = AuditLog(
            timestamp=timezone.now(),
            actor="SYSTEM",
            action="PURGE_AUDIT_LOGS",
            object_id=None,
            object_repr=f"Purged {deleted_count} audit logs older than 365 days",
            content_type_id=None,
            changes={},
        )
        purge_log.save()

        # Send purge confirmation email
        try:
            send_mail(
                subject="Audit Log Purge Completed",
                message=f"Purged {deleted_count} audit logs older than 365 days per HIPAA retention policy.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=(
                    [settings.BLOOD_BANK_ADMIN_EMAIL]
                    if hasattr(settings, "BLOOD_BANK_ADMIN_EMAIL")
                    else ["admin@hospital.com"]
                ),
                fail_silently=False,
            )
        except Exception as email_error:
            logger.error(f"Failed to send purge confirmation: {email_error}")

        return {"status": "success", "logs_purged": deleted_count}

    except Exception as e:
        logger.error(f"Audit log purge failed: {str(e)}")
        raise self.retry(countdown=60 * 60, exc=e)  # Retry in 1 hour


@shared_task
def process_transfusion_notification(transfusion_id):
    """
    Task to handle transfusion notifications and inventory updates
    """
    try:
        transfusion = TransfusionRecord.objects.get(id=transfusion_id)

        # Send transfusion confirmation
        message = f"""
Transfusion Completed
====================

Patient: {transfusion.patient.name}
Blood Unit: {transfusion.blood_unit.unit_id}
Quantity: {transfusion.quantity} units
Date: {transfusion.transfusion_date}
Performed by: {transfusion.performed_by.username}

This is a confirmation of successful transfusion.\n"""

        # Send email to patient and doctor
        send_mail(
            subject="Transfusion Confirmation",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[transfusion.patient.contact],  # Use encrypted contact
            fail_silently=True,
        )

        logger.info(f"Transfusion notification sent for ID {transfusion_id}")

    except TransfusionRecord.DoesNotExist:
        logger.error(f"Transfusion record {transfusion_id} not found")
    except Exception as e:
        logger.error(f"Transfusion notification failed: {e}")


# Celery beat schedule (to be configured in settings)
# from celery.schedules import crontab
# beat_schedule = {
#     'check-expiry-daily': {
#         'task': 'blood_bank.tasks.check_expiry_alerts',
#         'schedule': crontab(hour=0, minute=0),
#     },
#     'purge-audit-weekly': {
#         'task': 'blood_bank.tasks.purge_old_audit_logs',
#         'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Sunday 2AM
#     },
# }
