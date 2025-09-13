from datetime import date, datetime, time, timedelta

from appointments.models import Appointment, AppointmentStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from hospitals.models import Hospital
from hr.models import DutyRoster, Shift
from patients.models import Patient
from users.models import UserRole


class AvailableSlotsTest(TestCase):
    def setUp(self):
        self.h = Hospital.objects.create(name="H", code="h")
        User = get_user_model()
        self.doctor = User.objects.create_user(
            username="doc", password="x", role=UserRole.DOCTOR, hospital=self.h
        )
        # Create a patient record
        self.patient = Patient.objects.create(
            hospital=self.h, first_name="Pat", last_name="Ient"
        )
        self.shift = Shift.objects.create(
            hospital=self.h, name="Day", start_time=time(9, 0), end_time=time(10, 0)
        )
        self.target_date = date.today() + timedelta(days=1)
        DutyRoster.objects.create(
            hospital=self.h, user=self.doctor, date=self.target_date, shift=self.shift
        )

    def test_slots(self):
        # Existing appt 09:00-09:30 on target date
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.combine(self.target_date, time(9, 0)), tz)
        end = timezone.make_aware(datetime.combine(self.target_date, time(9, 30)), tz)
        Appointment.objects.create(
            hospital=self.h,
            patient=self.patient,
            doctor=self.doctor,
            start_at=start,
            end_at=end,
            status=AppointmentStatus.SCHEDULED,
        )
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.doctor)
        res = client.get(
            f"/api/appointments/available_slots/?doctor={self.doctor.id}&date={self.target_date.isoformat()}"
        )
        self.assertEqual(res.status_code, 200)
        slots = res.data["slots"]
        # Expect only 09:30-10:00 available
        self.assertEqual(len(slots), 1)
        self.assertIn("09:30:00", slots[0]["start_at"])
