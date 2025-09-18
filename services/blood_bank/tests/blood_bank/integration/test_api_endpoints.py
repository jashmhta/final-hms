import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from ..app.models import BloodInventory, Crossmatch, Donor, TransfusionRecord
from ..app.serializers import BloodInventorySerializer, DonorSerializer
@pytest.mark.django_db
class TestBloodBankAPIEndpoints(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="testpass123",
            role="ADMIN",
        )
        self.doctor_user = User.objects.create_user(
            username="doctor_test",
            email="doctor@test.com",
            password="testpass123",
            role="DOCTOR",
        )
        self.patient_user = User.objects.create_user(
            username="patient_test",
            email="patient@test.com",
            password="testpass123",
            role="PATIENT",
        )
        self.patient = Patient.objects.create(
            id=1,
            name="John Doe",
            dob="1980-01-01",
            gender="Male",
            contact="123-456-7890",
            medical_history="Test patient",
        )
        self.donor = Donor.objects.create(
            name="Test Donor",
            dob="01/01/1980",
            ssn="123-45-6789",
            address="123 Test St",
            contact="1234567890",
            blood_type="O+",
            is_active=True,
        )
        self.inventory = BloodInventory.objects.create(
            donor=self.donor,
            blood_type="O+",
            unit_id="UNIT-001",
            expiry_date=date.today() + timedelta(days=45),
            status="AVAILABLE",
            quantity=1,
        )
    def get_admin_auth_headers(self):
        refresh = RefreshToken.for_user(self.admin_user)
        return {
            "HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}",
        }
    def get_doctor_auth_headers(self):
        refresh = RefreshToken.for_user(self.doctor_user)
        return {
            "HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}",
        }
    def test_donor_list_authenticated(self):
        response = self.client.get("/api/blood-bank/donors/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response = self.client.get(
            "/api/blood-bank/donors/", **self.get_admin_auth_headers()
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1  
    def test_donor_create_admin(self):
        donor_data = {
            "name": "New Test Donor",
            "dob": "03/03/1990",
            "ssn": "111-22-3333",
            "address": "789 New Test St",
            "contact": "1112223333",
            "blood_type": "A+",
            "is_active": True,
        }
        response = self.client.post(
            "/api/blood-bank/donors/", donor_data, **self.get_admin_auth_headers()
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Test Donor"
        assert response.data["blood_type"] == "A+"
        created_donor = Donor.objects.get(name="New Test Donor")
        assert created_donor.pk is not None
    def test_donor_create_doctor(self):
        donor_data = {
            "name": "Doctor Created Donor",
            "dob": "04/04/1995",
            "ssn": "444-55-6666",
            "address": "456 Doctor Ave",
            "contact": "4445556666",
            "blood_type": "B-",
            "is_active": True,
        }
        response = self.client.post(
            "/api/blood-bank/donors/", donor_data, **self.get_doctor_auth_headers()
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Doctor Created Donor"
    def test_donor_create_patient_forbidden(self):
        donor_data = {
            "name": "Patient Attempt",
            "dob": "05/05/2000",
            "ssn": "777-88-9999",
            "address": "789 Patient St",
            "contact": "7778889999",
            "blood_type": "AB+",
            "is_active": True,
        }
        refresh = RefreshToken.for_user(self.patient_user)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}
        response = self.client.post("/api/blood-bank/donors/", donor_data, **headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    def test_inventory_list_with_cache(self):
        response = self.client.get(
            "/api/blood-bank/inventory/", **self.get_admin_auth_headers()
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        response2 = self.client.get(
            "/api/blood-bank/inventory/", **self.get_admin_auth_headers()
        )
        assert response2.status_code == status.HTTP_200_OK
        assert response.data == response2.data
    def test_inventory_expiring_soon(self):
        expiring_inventory = BloodInventory.objects.create(
            donor=self.donor,
            blood_type="O+",
            unit_id="EXP-001",
            expiry_date=date.today() + timedelta(days=5),  
            status="AVAILABLE",
            quantity=1,
        )
        response = self.client.get(
            "/api/blood-bank/inventory/expiring_soon/", **self.get_admin_auth_headers()
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert any(unit["unit_id"] == "EXP-001" for unit in response.data)
    def test_inventory_reserve_action(self):
        response = self.client.post(
            f"/api/blood-bank/inventory/{self.inventory.pk}/reserve/",
            {},
            **self.get_admin_auth_headers(),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "RESERVED"
        updated_inventory = BloodInventory.objects.get(pk=self.inventory.pk)
        assert updated_inventory.status == "RESERVED"
    def test_transfusion_creation(self):
        transfusion_data = {
            "patient": self.patient.pk,
            "blood_unit": self.inventory.pk,
            "quantity": 1,
            "notes": "Test transfusion",
        }
        response = self.client.post(
            "/api/blood-bank/transfusion/",
            transfusion_data,
            **self.get_doctor_auth_headers(),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["quantity"] == 1
        assert response.data["blood_unit"] == self.inventory.pk
        updated_inventory = BloodInventory.objects.get(pk=self.inventory.pk)
        assert updated_inventory.status == "TRANSFUSED"
    def test_crossmatch_creation(self):
        crossmatch_data = {
            "patient": self.patient.pk,
            "blood_unit": self.inventory.pk,
            "compatibility_result": "COMPATIBLE",
            "notes": "Test crossmatch result",
        }
        response = self.client.post(
            "/api/blood-bank/crossmatch/",
            crossmatch_data,
            **self.get_doctor_auth_headers(),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["compatibility_result"] == "COMPATIBLE"
        assert response.data["patient"] == self.patient.pk
    def test_crossmatch_compatible_units(self):
        Crossmatch.objects.create(
            patient=self.patient,
            blood_unit=self.inventory,
            compatibility_result="COMPATIBLE",
            notes="Compatible test",
        )
        response = self.client.get(
            f"/api/blood-bank/crossmatch/compatible_units/?patient_id={self.patient.pk}",
            **self.get_admin_auth_headers(),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert any(
            crossmatch["blood_unit"] == self.inventory.pk
            for crossmatch in response.data
        )
    def test_invalid_blood_type_validation(self):
        donor_data = {
            "name": "Invalid Blood Type",
            "dob": "06/06/2005",
            "ssn": "000-00-0000",
            "address": "Invalid Address",
            "contact": "0000000000",
            "blood_type": "INVALID",  
            "is_active": True,
        }
        response = self.client.post(
            "/api/blood-bank/donors/", donor_data, **self.get_admin_auth_headers()
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "blood_type" in response.data
    def test_invalid_expiry_date_validation(self):
        inventory_data = {
            "donor": self.donor.pk,
            "blood_type": "O+",
            "unit_id": "INVALID-EXPIRY",
            "expiry_date": "2023-01-01",  
            "status": "AVAILABLE",
            "quantity": 1,
        }
        response = self.client.post(
            "/api/blood-bank/inventory/",
            inventory_data,
            **self.get_admin_auth_headers(),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "expiry_date" in response.data