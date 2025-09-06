from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from hospitals.models import Hospital, Plan, HospitalPlan
from patients.models import Patient, PatientGender
from appointments.models import Appointment
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed demo data for HMS'

    def handle(self, *args, **options):
        hospital, _ = Hospital.objects.get_or_create(name='Demo Hospital', defaults={'code': 'DEMO', 'address': '123 Main St'})
        # Ensure a default plan and subscription
        plan, _ = Plan.objects.get_or_create(name='Enterprise', defaults={'max_users': 500})
        HospitalPlan.objects.get_or_create(hospital=hospital, defaults={'plan': plan})
        # Admin
        admin, created = User.objects.get_or_create(username='admin', defaults={'role': 'SUPER_ADMIN', 'is_staff': True, 'is_superuser': True})
        if created:
            admin.set_password('admin123')
            admin.save()
        # Hospital admin
        hadmin, _ = User.objects.get_or_create(username='hadmin', defaults={'role': 'HOSPITAL_ADMIN', 'hospital': hospital})
        hadmin.set_password('admin123'); hadmin.save()
        # Doctor
        doctor, _ = User.objects.get_or_create(username='drsmith', defaults={'role': 'DOCTOR', 'hospital': hospital, 'first_name': 'John', 'last_name': 'Smith'})
        doctor.set_password('doctor123'); doctor.save()
        # Patients
        first_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Ethan']
        last_names = ['Brown', 'Smith', 'Johnson', 'Williams', 'Jones']
        patients = []
        for i in range(10):
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            p, _ = Patient.objects.get_or_create(hospital=hospital, first_name=fn, last_name=ln, defaults={'gender': PatientGender.UNKNOWN, 'phone': f'999000{i:03d}', 'email': f'{fn.lower()}{i}@example.com'})
            patients.append(p)
        # Appointments
        now = timezone.now()
        for i in range(5):
            start = now + timezone.timedelta(days=1, hours=i)
            end = start + timezone.timedelta(minutes=30)
            Appointment.objects.get_or_create(hospital=hospital, patient=random.choice(patients), doctor=doctor, start_at=start, end_at=end, defaults={'reason': 'Consultation'})
        self.stdout.write(self.style.SUCCESS('Demo data seeded. Users: admin/admin123, hadmin/admin123, drsmith/doctor123'))