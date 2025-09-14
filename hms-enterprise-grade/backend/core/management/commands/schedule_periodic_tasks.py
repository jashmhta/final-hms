import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask


class Command(BaseCommand):
    help = (
        "Schedule periodic tasks for HMS (appointment reminders and low-stock checks)"
    )

    def handle(self, *args, **options):
        # Every 15 minutes: low stock check
        schedule_15, _ = IntervalSchedule.objects.get_or_create(
            every=15, period=IntervalSchedule.MINUTES
        )
        PeriodicTask.objects.get_or_create(
            interval=schedule_15,
            name="Low Stock Check",
            task="core.tasks.check_low_stock_and_notify",
        )
        # Every hour: send appointment reminders
        schedule_60, _ = IntervalSchedule.objects.get_or_create(
            every=60, period=IntervalSchedule.MINUTES
        )
        PeriodicTask.objects.get_or_create(
            interval=schedule_60,
            name="Appointment Reminders",
            task="core.tasks.send_appointment_reminders",
        )
        self.stdout.write(self.style.SUCCESS("Scheduled periodic tasks."))
