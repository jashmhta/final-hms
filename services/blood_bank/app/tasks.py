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
    try:
        logger.info("Starting blood expiry alert check")
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
        message_body = f
        for unit in expiring_units:
            message_body += f"- Unit ID: {unit.unit_id} | Type: {unit.blood_type} | Expiry: {unit.expiry_date}\n"
        message_body += (
            "\nThis is an automated alert from the Blood Bank Management System."
        )
        try:
            email_subject = f"Blood Bank Alert: {alert_count} Units Expiring Soon"
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
            self.retry(countdown=60 * 5)  
        try:
            send_sms_expiry_alert(alert_count)
            logger.info("SMS alert sent successfully")
        except Exception as sms_error:
            logger.error(f"Failed to send SMS alert: {sms_error}")
        for unit in expiring_units:
            unit.save()  
        return {"status": "success", "alerts_sent": alert_count, "units": alert_count}
    except Exception as e:
        logger.error(f"Expiry alert task failed: {str(e)}")
        raise self.retry(countdown=60 * 10, exc=e)  
def send_sms_expiry_alert(unit_count):
    """
    Enterprise-grade SMS service integration for critical blood bank alerts
    HIPAA compliant with delivery confirmation and audit trail
    """
    try:
        # Import enterprise SMS service
        from .sms_service import SMSService

        # Initialize SMS service with enterprise configuration
        sms_service = SMSService()

        # Create HIPAA-compliant message
        sms_message = f"HMS Blood Bank: {unit_count} units expiring within 7 days. Immediate action required."

        # Get emergency contacts from configuration
        emergency_contacts = get_emergency_contacts()

        if not emergency_contacts:
            logger.warning("No emergency contacts configured for SMS alerts")
            return False

        # Send SMS with enterprise features
        delivery_results = []
        for contact in emergency_contacts:
            try:
                result = sms_service.send_sms(
                    recipient=contact['phone'],
                    message=sms_message,
                    priority='high',
                    message_type='emergency',
                    callback_url=generate_callback_url('blood_bank_expiry')
                )
                delivery_results.append(result)

                # Log for HIPAA compliance
                log_sms_communication(
                    recipient=contact['phone'],
                    message=sms_message,
                    message_id=result.get('message_id'),
                    status=result.get('status'),
                    purpose='blood_bank_expiry_alert'
                )

                logger.info(f"SMS alert sent to {contact['phone'][-4:]}: {result.get('status')}")

            except Exception as contact_error:
                logger.error(f"Failed to send SMS to {contact['phone'][-4:]}: {contact_error}")
                delivery_results.append({'phone': contact['phone'], 'status': 'failed', 'error': str(contact_error)})

        # Verify delivery success
        successful_deliveries = [r for r in delivery_results if r.get('status') == 'success']
        if len(successful_deliveries) == 0:
            raise Exception("No SMS deliveries successful")

        logger.info(f"SMS alerts sent successfully to {len(successful_deliveries)}/{len(emergency_contacts)} contacts")
        return True

    except ImportError:
        logger.error("SMS service not available - please configure enterprise SMS provider")
        return False
    except Exception as e:
        logger.error(f"SMS alert failed: {e}")
        # Fallback to email if SMS fails
        try:
            send_email_fallback(unit_count, e)
        except Exception as email_error:
            logger.error(f"Email fallback also failed: {email_error}")
        raise

def get_emergency_contacts():
    """
    Get emergency contacts from enterprise configuration
    """
    from django.conf import settings

    contacts = []

    # Get contacts from Django settings
    if hasattr(settings, 'BLOOD_BANK_EMERGENCY_CONTACTS'):
        contacts.extend(settings.BLOOD_BANK_EMERGENCY_CONTACTS)

    # Get contacts from environment variables
    emergency_phones = os.getenv('BLOOD_BANK_EMERGENCY_PHONES', '')
    if emergency_phones:
        for phone in emergency_phones.split(','):
            phone = phone.strip()
            if phone:
                contacts.append({'phone': phone, 'name': 'Emergency Contact'})

    # Get on-call staff from database
    try:
        from .models import StaffContact
        on_call_staff = StaffContact.objects.filter(
            is_on_call=True,
            receives_blood_bank_alerts=True
        ).values('phone', 'name', 'role')

        for staff in on_call_staff:
            contacts.append({
                'phone': staff['phone'],
                'name': f"{staff['name']} ({staff['role']})",
                'type': 'staff'
            })
    except Exception as e:
        logger.warning(f"Could not load on-call staff contacts: {e}")

    return contacts

def generate_callback_url(purpose):
    """
    Generate callback URL for SMS delivery confirmation
    """
    from django.conf import settings
    base_url = getattr(settings, 'SMS_CALLBACK_BASE_URL', 'https://api.hospital.com/sms-callback')
    return f"{base_url}/{purpose}"

def log_sms_communication(recipient, message, message_id, status, purpose):
    """
    Log SMS communication for HIPAA compliance audit trail
    """
    try:
        from .models import SMSLog
        from django.utils import timezone

        SMSLog.objects.create(
            recipient_last_4=recipient[-4:],  # Store only last 4 digits for privacy
            message_preview=message[:50] + '...' if len(message) > 50 else message,
            message_id=message_id,
            status=status,
            purpose=purpose,
            timestamp=timezone.now()
        )
    except Exception as e:
        logger.error(f"Failed to log SMS communication: {e}")

def send_email_fallback(unit_count, original_error):
    """
    Send email fallback when SMS fails
    """
    from django.conf import settings
    from django.core.mail import EmailMessage

    try:
        subject = f"URGENT: SMS System Failure - Blood Bank Expiry Alert"

        email_body = f"""
        CRITICAL SYSTEM ALERT

        The SMS alert system has failed. Please address immediately.

        Original Alert: {unit_count} blood units expiring within 7 days
        Error: {original_error}

        Manual intervention required:
        1. Check SMS service configuration
        2. Verify emergency contact list
        3. Manually notify blood bank staff
        4. Investigate expired units

        System: HMS Blood Bank Management
        Priority: CRITICAL
        """

        recipients = getattr(settings, 'BLOOD_BANK_ADMIN_EMAILS', ['admin@hospital.com'])

        email = EmailMessage(
            subject=subject,
            body=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
            headers={'X-Priority': '1', 'X-MSMail-Priority': 'High'}
        )
        email.send(fail_silently=False)

        logger.info(f"Email fallback sent to {len(recipients)} recipients")

    except Exception as email_error:
        logger.critical(f"Email fallback also failed: {email_error}")
        raise Exception(f"Both SMS and email systems failed - Manual intervention required")
@shared_task(bind=True, max_retries=2)
def purge_old_audit_logs(self):
    try:
        logger.info("Starting audit log purge task")
        retention_date = timezone.now() - timedelta(days=365)
        old_logs = AuditLog.objects.filter(timestamp__lt=retention_date)
        log_count = old_logs.count()
        logger.info(f"Found {log_count} audit logs older than 365 days")
        if log_count == 0:
            logger.info("No old audit logs to purge")
            return {"status": "success", "logs_purged": 0}
        deleted_count, _ = old_logs.delete()
        logger.info(f"Purged {deleted_count} audit logs")
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
        raise self.retry(countdown=60 * 60, exc=e)  
@shared_task
def process_transfusion_notification(transfusion_id):
    try:
        transfusion = TransfusionRecord.objects.get(id=transfusion_id)
        message = f
        send_mail(
            subject="Transfusion Confirmation",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[transfusion.patient.contact],  
            fail_silently=True,
        )
        logger.info(f"Transfusion notification sent for ID {transfusion_id}")
    except TransfusionRecord.DoesNotExist:
        logger.error(f"Transfusion record {transfusion_id} not found")
    except Exception as e:
        logger.error(f"Transfusion notification failed: {e}")