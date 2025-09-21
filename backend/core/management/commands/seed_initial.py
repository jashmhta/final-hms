from django.core.management.base import BaseCommand

from billing.models import ServiceCatalog
from hospitals.models import Hospital
from hr.models import Shift


class Command(BaseCommand):
    help = "Seed initial HMS data (hospital, services, shifts)"

    def handle(self, *args, **options):
        hospital, _ = Hospital.objects.get_or_create(code="central", defaults={"name": "Central Hospital"})
        self.stdout.write(self.style.SUCCESS(f"Hospital: {hospital}"))
        services = [
            ("CONSULT", "Consultation", 5000),
            ("LAB_CBC", "Complete Blood Count", 2000),
            ("XR_CHEST", "X-Ray Chest", 8000),
        ]
        for code, name, price in services:
            obj, created = ServiceCatalog.objects.get_or_create(
                hospital=hospital,
                code=code,
                defaults={"name": name, "price_cents": price},
            )
            self.stdout.write(f"Service {code}: {'created' if created else 'exists'}")
        day_shift, created = Shift.objects.get_or_create(
            hospital=hospital,
            name="Day",
            defaults={"start_time": "09:00", "end_time": "17:00"},
        )
        self.stdout.write(f"Shift Day: {'created' if created else 'exists'}")
        self.stdout.write(self.style.SUCCESS("Seeding complete."))
