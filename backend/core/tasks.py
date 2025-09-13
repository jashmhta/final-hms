from appointments.models import Appointment, AppointmentStatus
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from pharmacy.models import Medication


@shared_task
def send_appointment_reminders():
    now = timezone.now()
    upcoming = Appointment.objects.filter(
        status=AppointmentStatus.SCHEDULED,
        start_at__range=(now, now + timezone.timedelta(hours=24)),
    )
    for appt in upcoming.select_related("patient", "doctor"):
        subject = f"Appointment Reminder"
        body = f"Reminder: appointment on {appt.start_at} with doctor {appt.doctor_id}"
        # In real system, use patient email/phone
        send_mail(subject, body, None, ["admin@example.com"], fail_silently=True)


@shared_task
def check_low_stock_and_notify():
    low = Medication.objects.filter(stock_quantity__lt=models.F("min_stock_level"))
    if low.exists():
        names = ", ".join(low.values_list("name", flat=True)[:20])
        send_mail(
            "Low stock alert",
            f"Low stock items: {names}",
            None,
            ["admin@example.com"],
            fail_silently=True,
        )
