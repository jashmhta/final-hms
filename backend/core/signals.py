import json
import os
from datetime import date, datetime

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict

from appointments.models import Appointment
from billing.models import Bill, Payment
from patients.models import Patient
from pharmacy.models import Prescription

from .audit import send_audit_event
from .models import AuditLog

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC_APPT = os.getenv("KAFKA_TOPIC_APPOINTMENTS", "appointments_events")
try:
    from kafka import KafkaProducer

    _producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
except Exception:
    _producer = None


def log_action(instance, action, user=None):
    hospital = getattr(instance, "hospital", None)
    model = instance.__class__.__name__
    object_id = str(getattr(instance, "pk", ""))
    data = {}
    try:
        data = model_to_dict(instance)
        for key, value in data.items():
            if isinstance(value, (date, datetime)):
                data[key] = value.isoformat()
    except Exception:
        pass
    AuditLog.objects.create(
        hospital=hospital if hasattr(hospital, "pk") else None,
        user=user if user and hasattr(user, "pk") else None,
        model=model,
        object_id=object_id,
        action=action,
        data=data,
    )
    try:
        send_audit_event("backend", action.lower(), model.lower(), object_id)
    except Exception:
        pass


@receiver(post_save, sender=Patient)
@receiver(post_save, sender=Appointment)
@receiver(post_save, sender=Prescription)
@receiver(post_save, sender=Bill)
@receiver(post_save, sender=Payment)
def on_save(sender, instance, created, **kwargs):
    log_action(instance, "CREATE" if created else "UPDATE")
    if created and sender is Appointment and _producer:
        try:
            _producer.send(
                KAFKA_TOPIC_APPT,
                {
                    "event": "appointment_created",
                    "appointment_id": instance.pk,
                    "hospital_id": getattr(instance, "hospital_id", None),
                    "patient_id": getattr(instance, "patient_id", None),
                    "doctor_id": getattr(instance, "doctor_id", None),
                    "start_at": str(getattr(instance, "start_at", "")),
                    "end_at": str(getattr(instance, "end_at", "")),
                },
            )
        except Exception:
            pass


@receiver(post_delete, sender=Patient)
@receiver(post_delete, sender=Appointment)
@receiver(post_delete, sender=Prescription)
@receiver(post_delete, sender=Bill)
@receiver(post_delete, sender=Payment)
def on_delete(sender, instance, **kwargs):
    log_action(instance, "DELETE")
