import json
import logging
import time
from datetime import datetime, timedelta
from functools import wraps

import requests
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from .models import Claim, PreAuth, Reimbursement

logger = logging.getLogger(__name__)


def cache_result(timeout=300):
    """Decorator to cache task results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator
@shared_task(bind=True, max_retries=3)
def submit_tpa_request(self, preauth_id):
    """Submit TPA request with proper error handling and resource management"""
    try:
        cache_key = f"tpa_status_{preauth_id}"
        cache.set(cache_key, "submitting", timeout=300)

        preauth = PreAuth.objects.select_related('patient').get(id=preauth_id)
        payload = {
            "patient_id": preauth.patient.id,
            "claim_amount": float(preauth.claim_amount),
            "status": preauth.status,
            "diagnosis_codes": [],
            "procedure_codes": [],
        }

        # Use session for connection pooling
        with requests.Session() as session:
            session.headers.update({
                "Authorization": f"Token {getattr(settings, 'TPA_API_TOKEN', '')}",
                "Content-Type": "application/json"
            })

            response = session.post(
                "http://mock-tpa.com/api/submit",
                json=payload,
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            preauth.tpa_response = json.dumps(result)
            preauth.status = "submitted"
            preauth.save()
            cache.set(cache_key, "submitted", timeout=300)

            logger.info(f"TPA request submitted successfully for preauth {preauth_id}")
            return {
                "status": "success",
                "transaction_id": result.get("transaction_id"),
                "response": result,
            }
        else:
            error_msg = f"TPA submission failed: {response.status_code}"
            logger.warning(error_msg)
            cache.set(cache_key, f"failed_{response.status_code}", timeout=300)
            return {
                "status": "error",
                "code": response.status_code,
                "reason": response.text,
            }

    except PreAuth.DoesNotExist:
        logger.error(f"PreAuth {preauth_id} not found")
        return {"status": "error", "reason": "PreAuth not found"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error in TPA submission: {e}")
        cache.set(cache_key, f"network_error: {e}", timeout=300)
        raise self.retry(countdown=60 * (2**self.request.retries))
    except Exception as e:
        logger.error(f"Unexpected error in TPA submission: {e}")
        cache.set(cache_key, f"error: {e}", timeout=300)
        raise self.retry(countdown=60 * (2**self.request.retries))
@shared_task(bind=True, max_retries=5)
@cache_result(timeout=60)
def poll_tpa_status(self, preauth_id):
    """Poll TPA status with connection pooling and caching"""
    try:
        cache_key = f"tpa_status_{preauth_id}"
        current_status = cache.get(cache_key)

        if current_status != "submitted":
            logger.info(f"PreAuth {preauth_id} not ready for polling: {current_status}")
            return {"status": "not_ready", "current_status": current_status}

        preauth = PreAuth.objects.get(id=preauth_id)
        response_data = json.loads(preauth.tpa_response) if preauth.tpa_response else {}
        transaction_id = response_data.get("transaction_id")

        if not transaction_id:
            logger.warning(f"No transaction ID for preauth {preauth_id}")
            return {"status": "no_transaction_id"}

        status_url = f"http://mock-tpa.com/api/status/{transaction_id}"

        # Use session for connection pooling
        with requests.Session() as session:
            session.headers.update({
                "Authorization": f"Token {getattr(settings, 'TPA_API_TOKEN', '')}",
                "Content-Type": "application/json"
            })

            response = session.get(status_url, timeout=30)

        if response.status_code == 200:
            status_data = response.json()
            preauth.status = status_data.get("status", "pending")
            preauth.tpa_response = json.dumps(status_data)
            preauth.save()
            cache.set(cache_key, preauth.status, timeout=300)

            if preauth.status in ["approved", "rejected"]:
                send_notification.delay(preauth_id, preauth.status)

            logger.info(f"Successfully polled status for preauth {preauth_id}: {preauth.status}")
            return {
                "status": "polled",
                "new_status": preauth.status,
                "status_data": status_data,
            }
        else:
            logger.warning(f"Poll failed for preauth {preauth_id}: {response.status_code}")
            return {"status": "poll_failed", "code": response.status_code}

    except PreAuth.DoesNotExist:
        logger.error(f"PreAuth {preauth_id} not found for polling")
        return {"status": "error", "reason": "PreAuth not found"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error polling TPA status: {e}")
        raise self.retry(countdown=300 * (2**self.request.retries))
    except Exception as e:
        logger.error(f"Unexpected error polling TPA status: {e}")
        raise self.retry(countdown=300 * (2**self.request.retries))
@shared_task
def send_notification(preauth_id, status):
    """Send notification with proper logging and error handling"""
    try:
        preauth = PreAuth.objects.select_related('patient').get(id=preauth_id)

        message = (
            f"Your pre-authorization request {preauth_id} has been {status}. "
            f"Amount: ${preauth.claim_amount}."
        )

        logger.info(f"Sending notification for preauth {preauth_id}: {message}")
        logger.info(
            f"To: {preauth.patient.email} (Email) / {preauth.patient.phone} (SMS)"
        )

        # Use more efficient cache key
        timestamp = int(timezone.now().timestamp())
        cache_key = f"notification_{preauth_id}_{status}_{timestamp}"

        cache.set(
            cache_key,
            {
                "message": message,
                "status": status,
                "timestamp": timezone.now().isoformat(),
                "patient_id": preauth.patient.id,
            },
            timeout=86400 * 30,  # 30 days
        )

        return {
            "status": "notification_sent",
            "preauth_id": preauth_id,
            "notification_type": "email_sms_mock",
        }

    except PreAuth.DoesNotExist:
        logger.error(f"PreAuth {preauth_id} not found for notification")
        return {"status": "error", "reason": "PreAuth not found"}
    except Exception as e:
        logger.error(f"Notification failed for preauth {preauth_id}: {e}")
        return {"status": "notification_failed", "error": str(e)}
@shared_task
def cleanup_old_records():
    """Clean up old records with proper batching and resource management"""
    cutoff_date = timezone.now() - timedelta(days=365)
    deleted_count = 0

    try:
        logger.info(f"Starting cleanup of records older than {cutoff_date}")

        # Batch delete PreAuth records to avoid memory issues
        old_preauths = PreAuth.objects.filter(created_at__lt=cutoff_date)
        count = old_preauths.count()
        if count > 0:
            # Delete in batches of 1000
            batch_size = 1000
            for i in range(0, count, batch_size):
                batch_ids = old_preauths.values_list('id', flat=True)[i:i + batch_size]
                PreAuth.objects.filter(id__in=batch_ids).delete()
                deleted_count += len(batch_ids)

            logger.info(f"Deleted {count} old PreAuth records")

        # Batch delete Reimbursement records
        old_reimbursements = Reimbursement.objects.filter(payment_date__lt=cutoff_date)
        count = old_reimbursements.count()
        if count > 0:
            # Delete in batches of 1000
            batch_size = 1000
            for i in range(0, count, batch_size):
                batch_ids = old_reimbursements.values_list('id', flat=True)[i:i + batch_size]
                Reimbursement.objects.filter(id__in=batch_ids).delete()
                deleted_count += len(batch_ids)

            logger.info(f"Deleted {count} old Reimbursement records")

        # Clear only relevant cache keys, not entire cache
        cache_pattern = "tpa_status_*"
        cache_keys = cache.keys(cache_pattern)
        if cache_keys:
            cache.delete_many(cache_keys)
            logger.info(f"Cleared {len(cache_keys)} TPA status cache entries")

        logger.info(f"Cleanup completed: {deleted_count} records deleted")
        return {
            "status": "cleanup_complete",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"status": "cleanup_failed", "error": str(e)}