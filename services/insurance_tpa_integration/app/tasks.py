import json
import time
from datetime import datetime, timedelta
import requests
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from .models import Claim, PreAuth, Reimbursement
@shared_task(bind=True, max_retries=3)
def submit_tpa_request(self, preauth_id):
    try:
        cache_key = "tpa_status_" + str(preauth_id)
        cache.set(cache_key, "submitting", timeout=300)
        preauth = PreAuth.objects.get(id=preauth_id)
        payload = {
            "patient_id": preauth.patient.id,
            "claim_amount": float(preauth.claim_amount),
            "status": preauth.status,
            "diagnosis_codes": [],
            "procedure_codes": [],
        }
        response = requests.post(
            "http://mock-tpa.com/api/submit",
            json=payload,
            timeout=30,
            headers={
                "Authorization": "Token " + getattr(settings, "TPA_API_TOKEN", "")
            },
        )
        if response.status_code == 200:
            result = response.json()
            preauth.tpa_response = json.dumps(result)
            preauth.status = "submitted"
            preauth.save()
            cache.set(cache_key, "submitted", timeout=300)
            return {
                "status": "success",
                "transaction_id": result.get("transaction_id"),
                "response": result,
            }
        else:
            cache.set(cache_key, "failed_" + str(response.status_code), timeout=300)
            return {
                "status": "error",
                "code": response.status_code,
                "reason": response.text,
            }
    except PreAuth.DoesNotExist:
        return {"status": "error", "reason": "PreAuth not found"}
    except Exception as e:
        cache.set(cache_key, "error: " + str(e), timeout=300)
        raise self.retry(countdown=60 * (2**self.request.retries))
@shared_task(bind=True, max_retries=5)
def poll_tpa_status(self, preauth_id):
    try:
        cache_key = "tpa_status_" + str(preauth_id)
        current_status = cache.get(cache_key)
        if current_status != "submitted":
            return {"status": "not_ready", "current_status": current_status}
        preauth = PreAuth.objects.get(id=preauth_id)
        response_data = json.loads(preauth.tpa_response) if preauth.tpa_response else {}
        transaction_id = response_data.get("transaction_id")
        if not transaction_id:
            return {"status": "no_transaction_id"}
        status_url = "http://mock-tpa.com/api/status/" + str(transaction_id)
        response = requests.get(
            status_url,
            timeout=30,
            headers={
                "Authorization": "Token " + getattr(settings, "TPA_API_TOKEN", "")
            },
        )
        if response.status_code == 200:
            status_data = response.json()
            preauth.status = status_data.get("status", "pending")
            preauth.tpa_response = json.dumps(status_data)
            preauth.save()
            cache.set(cache_key, preauth.status, timeout=300)
            if preauth.status in ["approved", "rejected"]:
                send_notification.delay(preauth_id, preauth.status)
            return {
                "status": "polled",
                "new_status": preauth.status,
                "status_data": status_data,
            }
        else:
            return {"status": "poll_failed", "code": response.status_code}
    except PreAuth.DoesNotExist:
        return {"status": "error", "reason": "PreAuth not found"}
    except Exception as e:
        raise self.retry(countdown=300 * (2**self.request.retries))
@shared_task
def send_notification(preauth_id, status):
    try:
        preauth = PreAuth.objects.get(id=preauth_id)
        message = (
            "Your pre-authorization request "
            + str(preauth_id)
            + " has been "
            + status
            + ". Amount: $"
            + str(preauth.claim_amount)
            + "."
        )
        print("NOTIFICATION: " + message)
        print(
            "To: "
            + str(preauth.patient.email)
            + " (Email) / "
            + str(preauth.patient.phone)
            + " (SMS)"
        )
        cache.set(
            "notification_"
            + str(preauth_id)
            + "_"
            + status
            + "_"
            + str(int(timezone.now().timestamp())),
            {
                "message": message,
                "status": status,
                "timestamp": timezone.now().isoformat(),
                "patient_id": preauth.patient.id,
            },
            timeout=86400 * 30,  
        )
        return {
            "status": "notification_sent",
            "preauth_id": preauth_id,
            "notification_type": "email_sms_mock",
        }
    except PreAuth.DoesNotExist:
        return {"status": "error", "reason": "PreAuth not found"}
    except Exception as e:
        print("Notification failed: " + str(e))
        return {"status": "notification_failed", "error": str(e)}
@shared_task
def cleanup_old_records():
    cutoff_date = timezone.now() - timedelta(days=365)
    deleted_count = 0
    try:
        old_preauths = PreAuth.objects.filter(created_at__lt=cutoff_date)
        count = old_preauths.count()
        old_preauths.delete()
        deleted_count += count
        old_reimbursements = Reimbursement.objects.filter(payment_date__lt=cutoff_date)
        count = old_reimbursements.count()
        old_reimbursements.delete()
        deleted_count += count
        cache.clear()
        return {
            "status": "cleanup_complete",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
        }
    except Exception as e:
        return {"status": "cleanup_failed", "error": str(e)}