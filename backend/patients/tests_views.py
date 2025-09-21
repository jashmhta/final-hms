import json
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.test import Client, TestCase
from django.urls import reverse

from ..models import (
    EmergencyContact,
    InsuranceInformation,
    Patient,
    PatientAlert,
    PatientStatus,
)

User = get_user_model()


class PatientViewTests(TestCase):
    """Comprehensive test suite for patient views"""

    def setUp(self):
        self.client = Client()
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123", hospital=self.hospital
        )
        self.client.login(username="testuser", password="testpass123")

    def test_patient_list_view_get(self):
        """Test GET request to patient list view"""
        # Create test patients
        Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )
        Patient.objects.create(
            hospital=self.hospital,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 1, 1),
            gender="FEMALE",
        )

        response = self.client.get(reverse("patients:patient-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/patient_list.html")
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Jane Smith")

    def test_patient_list_view_with_search(self):
        """Test patient list view with search functionality"""
        Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            medical_record_number="MRN123",
        )
        Patient.objects.create(
            hospital=self.hospital,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 1, 1),
            gender="FEMALE",
            medical_record_number="MRN456",
        )

        # Test search by first name
        response = self.client.get(reverse("patients:patient-list"), {"q": "John"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertNotContains(response, "Jane Smith")

        # Test search by MRN
        response = self.client.get(reverse("patients:patient-list"), {"q": "MRN456"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "John Doe")
        self.assertContains(response, "Jane Smith")

    def test_patient_list_view_with_filters(self):
        """Test patient list view with filtering"""
        Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            status=PatientStatus.ACTIVE,
        )
        Patient.objects.create(
            hospital=self.hospital,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 1, 1),
            gender="FEMALE",
            status=PatientStatus.INACTIVE,
        )

        # Test filter by status
        response = self.client.get(reverse("patients:patient-list"), {"status": "ACTIVE"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertNotContains(response, "Jane Smith")

    def test_patient_create_view_get(self):
        """Test GET request to patient create view"""
        response = self.client.get(reverse("patients:patient-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/patient_form.html")

    def test_patient_create_view_post_valid(self):
        """Test POST request to create patient with valid data"""
        patient_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "gender": "MALE",
            "phone_primary": "555-123-4567",
            "email": "john.doe@example.com",
            "address_line1": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
        }

        response = self.client.post(reverse("patients:patient-create"), data=patient_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation

        # Verify patient was created
        patient = Patient.objects.get(first_name="John", last_name="Doe")
        self.assertEqual(patient.email, "john.doe@example.com")
        self.assertEqual(patient.phone_primary, "555-123-4567")

    def test_patient_create_view_post_invalid(self):
        """Test POST request to create patient with invalid data"""
        invalid_data = {
            "first_name": "",  # Required field missing
            "last_name": "Doe",
            "date_of_birth": "invalid-date",  # Invalid date format
            "gender": "MALE",
        }

        response = self.client.post(reverse("patients:patient-create"), data=invalid_data)
        self.assertEqual(response.status_code, 200)  # Form re-rendered with errors
        self.assertTemplateUsed(response, "patients/patient_form.html")

    def test_patient_detail_view(self):
        """Test patient detail view"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        response = self.client.get(reverse("patients:patient-detail", kwargs={"pk": patient.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/patient_detail.html")
        self.assertContains(response, "John Doe")

    def test_patient_detail_view_404(self):
        """Test patient detail view with non-existent patient"""
        response = self.client.get(reverse("patients:patient-detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)

    def test_patient_update_view_get(self):
        """Test GET request to patient update view"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        response = self.client.get(reverse("patients:patient-update", kwargs={"pk": patient.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/patient_form.html")

    def test_patient_update_view_post_valid(self):
        """Test POST request to update patient with valid data"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        update_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1985-05-15",
            "gender": "FEMALE",
            "phone_primary": "555-987-6543",
        }

        response = self.client.post(reverse("patients:patient-update", kwargs={"pk": patient.pk}), data=update_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update

        # Verify patient was updated
        patient.refresh_from_db()
        self.assertEqual(patient.first_name, "Jane")
        self.assertEqual(patient.last_name, "Smith")
        self.assertEqual(patient.phone_primary, "555-987-6543")

    def test_patient_delete_view_get(self):
        """Test GET request to patient delete view"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        response = self.client.get(reverse("patients:patient-delete", kwargs={"pk": patient.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/patient_confirm_delete.html")

    def test_patient_delete_view_post(self):
        """Test POST request to delete patient"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        response = self.client.post(reverse("patients:patient-delete", kwargs={"pk": patient.pk}))
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion

        # Verify patient was deleted
        self.assertFalse(Patient.objects.filter(pk=patient.pk).exists())

    def test_emergency_contact_create_view(self):
        """Test emergency contact creation view"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        response = self.client.get(reverse("patients:emergency-contact-create", kwargs={"patient_pk": patient.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/emergency_contact_form.html")

    def test_emergency_contact_create_post(self):
        """Test POST request to create emergency contact"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        contact_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "relationship": "SPOUSE",
            "phone_primary": "555-123-4567",
            "email": "jane.doe@example.com",
        }

        response = self.client.post(
            reverse("patients:emergency-contact-create", kwargs={"patient_pk": patient.pk}), data=contact_data
        )
        self.assertEqual(response.status_code, 302)

        # Verify emergency contact was created
        contact = patient.emergency_contacts.first()
        self.assertEqual(contact.first_name, "Jane")
        self.assertEqual(contact.relationship, "SPOUSE")

    def test_insurance_create_view(self):
        """Test insurance information creation view"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        response = self.client.get(reverse("patients:insurance-create", kwargs={"patient_pk": patient.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/insurance_form.html")

    def test_insurance_create_post(self):
        """Test POST request to create insurance information"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        insurance_data = {
            "insurance_name": "Blue Cross Blue Shield",
            "insurance_type": "PRIMARY",
            "policy_number": "POL123456789",
            "effective_date": "2023-01-01",
            "insurance_company_name": "BCBS",
        }

        response = self.client.post(
            reverse("patients:insurance-create", kwargs={"patient_pk": patient.pk}), data=insurance_data
        )
        self.assertEqual(response.status_code, 302)

        # Verify insurance was created
        insurance = patient.insurance_plans.first()
        self.assertEqual(insurance.insurance_name, "Blue Cross Blue Shield")
        self.assertEqual(insurance.insurance_type, "PRIMARY")

    def test_patient_alert_create_view(self):
        """Test patient alert creation view"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        response = self.client.get(reverse("patients:alert-create", kwargs={"patient_pk": patient.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/alert_form.html")

    def test_patient_alert_create_post(self):
        """Test POST request to create patient alert"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        alert_data = {
            "alert_type": "ALLERGY",
            "severity": "HIGH",
            "title": "Penicillin Allergy",
            "description": "Patient has severe allergic reaction to penicillin",
        }

        response = self.client.post(
            reverse("patients:alert-create", kwargs={"patient_pk": patient.pk}), data=alert_data
        )
        self.assertEqual(response.status_code, 302)

        # Verify alert was created
        alert = patient.alerts.first()
        self.assertEqual(alert.alert_type, "ALLERGY")
        self.assertEqual(alert.severity, "HIGH")

    def test_patient_export_view(self):
        """Test patient data export view"""
        # Create test patients
        Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )
        Patient.objects.create(
            hospital=self.hospital,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 1, 1),
            gender="FEMALE",
        )

        response = self.client.get(reverse("patients:patient-export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="patients.csv"')

    def test_patient_search_view(self):
        """Test patient search view"""
        Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            medical_record_number="MRN123",
        )

        response = self.client.get(reverse("patients:patient-search"), {"q": "John"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/patient_search_results.html")
        self.assertContains(response, "John Doe")

    def test_patient_dashboard_view(self):
        """Test patient dashboard view"""
        response = self.client.get(reverse("patients:patient-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/patient_dashboard.html")

    def test_permissions_required(self):
        """Test that views require authentication"""
        self.client.logout()

        # Test that unauthenticated user is redirected to login
        response = self.client.get(reverse("patients:patient-list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))


class PatientAPITests(APITestCase):
    """Comprehensive test suite for patient API endpoints"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = User.objects.create_user(
            username="apiuser", email="api@example.com", password="apipass123", hospital=self.hospital
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    def test_patient_list_api_get(self):
        """Test GET request to patient list API"""
        Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["first_name"], "John")

    def test_patient_list_api_post(self):
        """Test POST request to create patient via API"""
        patient_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1985-05-15",
            "gender": "FEMALE",
            "phone_primary": "555-123-4567",
            "email": "jane.smith@example.com",
        }

        response = self.client.post("/api/patients/", patient_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        patient = Patient.objects.get(first_name="Jane", last_name="Smith")
        self.assertEqual(patient.email, "jane.smith@example.com")

    def test_patient_detail_api_get(self):
        """Test GET request to patient detail API"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        response = self.client.get(f"/api/patients/{patient.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "John")

    def test_patient_detail_api_put(self):
        """Test PUT request to update patient via API"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        update_data = {"first_name": "Jane", "last_name": "Smith", "date_of_birth": "1985-05-15", "gender": "FEMALE"}

        response = self.client.put(f"/api/patients/{patient.pk}/", update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        patient.refresh_from_db()
        self.assertEqual(patient.first_name, "Jane")
        self.assertEqual(patient.last_name, "Smith")

    def test_patient_detail_api_delete(self):
        """Test DELETE request to patient via API"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        response = self.client.delete(f"/api/patients/{patient.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Patient.objects.filter(pk=patient.pk).exists())

    def test_patient_search_api(self):
        """Test patient search API endpoint"""
        Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            medical_record_number="MRN123",
        )

        response = self.client.get("/api/patients/search/", {"q": "John"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["first_name"], "John")

    def test_patient_stats_api(self):
        """Test patient statistics API endpoint"""
        # Create test patients
        Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            status=PatientStatus.ACTIVE,
        )
        Patient.objects.create(
            hospital=self.hospital,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 1, 1),
            gender="FEMALE",
            status=PatientStatus.INACTIVE,
        )

        response = self.client.get("/api/patients/stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_patients", response.data)
        self.assertIn("active_patients", response.data)
        self.assertIn("inactive_patients", response.data)

    def test_emergency_contact_api_endpoints(self):
        """Test emergency contact API endpoints"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        # Create emergency contact
        contact_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "relationship": "SPOUSE",
            "phone_primary": "555-123-4567",
        }

        response = self.client.post(f"/api/patients/{patient.pk}/emergency-contacts/", contact_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get emergency contacts
        response = self.client.get(f"/api/patients/{patient.pk}/emergency-contacts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["first_name"], "Jane")

    def test_insurance_api_endpoints(self):
        """Test insurance API endpoints"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        # Create insurance
        insurance_data = {
            "insurance_name": "Blue Cross Blue Shield",
            "insurance_type": "PRIMARY",
            "policy_number": "POL123456789",
            "effective_date": "2023-01-01",
            "insurance_company_name": "BCBS",
        }

        response = self.client.post(f"/api/patients/{patient.pk}/insurance/", insurance_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get insurance plans
        response = self.client.get(f"/api/patients/{patient.pk}/insurance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["insurance_name"], "Blue Cross Blue Shield")

    def test_alert_api_endpoints(self):
        """Test patient alert API endpoints"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        # Create alert
        alert_data = {
            "alert_type": "ALLERGY",
            "severity": "HIGH",
            "title": "Penicillin Allergy",
            "description": "Patient has severe allergic reaction to penicillin",
        }

        response = self.client.post(f"/api/patients/{patient.pk}/alerts/", alert_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get alerts
        response = self.client.get(f"/api/patients/{patient.pk}/alerts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["alert_type"], "ALLERGY")

    def test_api_authentication_required(self):
        """Test that API endpoints require authentication"""
        self.client.credentials()  # Remove authentication

        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_permission_denied(self):
        """Test API permission handling"""
        # Create user without proper permissions
        limited_user = User.objects.create_user(username="limited", email="limited@example.com", password="limited123")
        limited_token = Token.objects.create(user=limited_user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + limited_token.key)

        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_validation_errors(self):
        """Test API validation error handling"""
        invalid_data = {
            "first_name": "",  # Required field missing
            "last_name": "Doe",
            "date_of_birth": "invalid-date",  # Invalid date
            "gender": "INVALID_GENDER",  # Invalid choice
        }

        response = self.client.post("/api/patients/", invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("first_name", response.data)
        self.assertIn("date_of_birth", response.data)

    def test_api_pagination(self):
        """Test API pagination"""
        # Create multiple patients
        for i in range(25):
            Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Patient{i}",
                last_name=f"Test{i}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertEqual(len(response.data["results"]), 20)  # Default page size

    @patch("backend.patients.views.enhanced_cache")
    def test_api_caching(self, mock_cache):
        """Test API caching functionality"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        # Test cache usage
        mock_cache.cache.get.return_value = None
        response = self.client.get(f"/api/patients/{patient.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify cache was checked
        mock_cache.cache.get.assert_called()
