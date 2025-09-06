from django.test import TestCase
from django.contrib.auth import get_user_model
from hospitals.models import Hospital
from users.models import UserRole
from pharmacy.models import Medication


class LowStockTest(TestCase):
    def setUp(self):
        self.h = Hospital.objects.create(name='H', code='h')
        User = get_user_model()
        self.user = User.objects.create_user(username='u', password='x', role=UserRole.PHARMACIST, hospital=self.h)
        Medication.objects.create(hospital=self.h, name='MedA', stock_quantity=5, min_stock_level=10)
        Medication.objects.create(hospital=self.h, name='MedB', stock_quantity=20, min_stock_level=10)

    def test_low_stock(self):
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=self.user)
        res = client.get('/api/medications/low_stock/')
        self.assertEqual(res.status_code, 200)
        names = [m['name'] for m in res.data['results']] if isinstance(res.data, dict) and 'results' in res.data else [m['name'] for m in res.data]
        self.assertIn('MedA', names)
        self.assertNotIn('MedB', names)
