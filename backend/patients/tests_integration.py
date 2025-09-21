import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection, transaction
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from ..models import (
    EmergencyContact,
    InsuranceInformation,
    Patient,
    PatientAlert,
    PatientStatus,
)

User = get_user_model()


class PatientWorkflowIntegrationTests(TransactionTestCase):
    """Integration tests for complete patient workflows"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123", hospital=self.hospital, is_staff=True
        )
        self.client.force_login(self.user)
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)

    def test_complete_patient_registration_workflow(self):
        """Test complete patient registration workflow from creation to all records"""
        # Step 1: Create patient via API
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
            "blood_type": "A+",
        }

        response = self.api_client.post("/api/patients/", patient_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        patient_id = response.data["id"]
        patient = Patient.objects.get(id=patient_id)

        # Verify basic patient data
        self.assertEqual(patient.first_name, "John")
        self.assertEqual(patient.last_name, "Doe")
        self.assertEqual(patient.medical_record_number, response.data["medical_record_number"])

        # Step 2: Add emergency contact
        emergency_contact_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "relationship": "SPOUSE",
            "phone_primary": "555-987-6543",
            "email": "jane.doe@example.com",
            "can_make_medical_decisions": True,
        }

        response = self.api_client.post(
            f"/api/patients/{patient_id}/emergency-contacts/", emergency_contact_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 3: Add insurance information
        insurance_data = {
            "insurance_name": "Blue Cross Blue Shield",
            "insurance_type": "PRIMARY",
            "policy_number": "POL123456789",
            "effective_date": "2023-01-01",
            "insurance_company_name": "BCBS",
            "copay_amount": "25.00",
            "deductible_amount": "1000.00",
        }

        response = self.api_client.post(f"/api/patients/{patient_id}/insurance/", insurance_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 4: Add medical alerts
        alert_data = {
            "alert_type": "ALLERGY",
            "severity": "HIGH",
            "title": "Penicillin Allergy",
            "description": "Patient has severe allergic reaction to penicillin",
            "requires_acknowledgment": True,
        }

        response = self.api_client.post(f"/api/patients/{patient_id}/alerts/", alert_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 5: Verify complete patient record
        response = self.api_client.get(f"/api/patients/{patient_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        patient_data = response.data
        self.assertEqual(len(patient_data["emergency_contacts"]), 1)
        self.assertEqual(len(patient_data["insurance_plans"]), 1)
        self.assertEqual(len(patient_data["alerts"]), 1)

        # Step 6: Test patient search functionality
        search_response = self.api_client.get("/api/patients/search/", {"q": "John Doe"})
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(search_response.data["results"]), 1)

    def test_patient_update_workflow(self):
        """Test patient information update workflow"""
        # Create initial patient
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        # Update basic information
        update_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone_primary": "555-555-5555",
            "email": "jane.smith@example.com",
        }

        response = self.api_client.put(f"/api/patients/{patient.id}/", update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        patient.refresh_from_db()
        self.assertEqual(patient.first_name, "Jane")
        self.assertEqual(patient.last_name, "Smith")

        # Verify all related data is still accessible
        response = self.api_client.get(f"/api/patients/{patient.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patient_status_change_workflow(self):
        """Test patient status change workflow"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1950, 1, 1),
            gender="MALE",
            status=PatientStatus.ACTIVE,
        )

        # Change to deceased status with date of death
        update_data = {"status": "DECEASED", "date_of_death": "2023-01-01", "cause_of_death": "Natural causes"}

        response = self.api_client.patch(f"/api/patients/{patient.id}/", update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        patient.refresh_from_db()
        self.assertEqual(patient.status, PatientStatus.DECEASED)
        self.assertEqual(patient.date_of_death, date(2023, 1, 1))

    def test_patient_insurance_lifecycle(self):
        """Test complete insurance information lifecycle"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        # Add primary insurance
        primary_insurance = {
            "insurance_name": "Primary Insurance Co",
            "insurance_type": "PRIMARY",
            "policy_number": "POL123",
            "effective_date": "2023-01-01",
            "insurance_company_name": "Primary Co",
            "verification_status": "PENDING",
        }

        response = self.api_client.post(f"/api/patients/{patient.id}/insurance/", primary_insurance, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        insurance_id = response.data["id"]

        # Update insurance verification
        update_verification = {"verification_status": "VERIFIED", "verification_date": "2023-01-15"}

        response = self.api_client.patch(
            f"/api/patients/{patient.id}/insurance/{insurance_id}/", update_verification, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Add secondary insurance
        secondary_insurance = {
            "insurance_name": "Secondary Insurance Co",
            "insurance_type": "SECONDARY",
            "policy_number": "POL456",
            "effective_date": "2023-01-01",
            "insurance_company_name": "Secondary Co",
        }

        response = self.api_client.post(f"/api/patients/{patient.id}/insurance/", secondary_insurance, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify insurance ordering (primary first)
        response = self.api_client.get(f"/api/patients/{patient.id}/insurance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["insurance_type"], "PRIMARY")

    def test_patient_alert_acknowledgment_workflow(self):
        """Test patient alert acknowledgment workflow"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        # Create alert requiring acknowledgment
        alert_data = {
            "alert_type": "SAFETY",
            "severity": "CRITICAL",
            "title": "Fall Risk",
            "description": "Patient identified as high fall risk",
            "requires_acknowledgment": True,
        }

        response = self.api_client.post(f"/api/patients/{patient.id}/alerts/", alert_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        alert_id = response.data["id"]

        # Acknowledge alert
        acknowledgment_data = {"acknowledged": True}

        response = self.api_client.patch(
            f"/api/patients/{patient.id}/alerts/{alert_id}/", acknowledgment_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify acknowledgment
        response = self.api_client.get(f"/api/patients/{patient.id}/alerts/{alert_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["acknowledged_by"])
        self.assertIsNotNone(response.data["acknowledged_at"])

    def test_patient_emergency_contact_management(self):
        """Test emergency contact management workflow"""
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        # Add multiple emergency contacts
        contacts_data = [
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "relationship": "SPOUSE",
                "phone_primary": "555-123-4567",
                "is_primary": True,
                "can_make_medical_decisions": True,
            },
            {
                "first_name": "John",
                "last_name": "Smith",
                "relationship": "FATHER",
                "phone_primary": "555-987-6543",
                "is_primary": False,
            },
        ]

        for contact_data in contacts_data:
            response = self.api_client.post(
                f"/api/patients/{patient.id}/emergency-contacts/", contact_data, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify contacts ordering (primary first)
        response = self.api_client.get(f"/api/patients/{patient.id}/emergency-contacts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue(response.data[0]["is_primary"])

        # Update primary contact
        primary_contact_id = response.data[0]["id"]
        update_data = {"phone_secondary": "555-555-5555"}

        response = self.api_client.patch(
            f"/api/patients/{patient.id}/emergency-contacts/{primary_contact_id}/", update_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patient_data_export_workflow(self):
        """Test patient data export workflow"""
        # Create test patients with various data
        for i in range(5):
            patient = Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Patient{i}",
                last_name=f"Test{i}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

            # Add emergency contact
            EmergencyContact.objects.create(
                patient=patient,
                first_name=f"Emergency{i}",
                last_name=f"Contact{i}",
                relationship="SPOUSE",
                phone_primary="555-123-4567",
            )

            # Add insurance
            InsuranceInformation.objects.create(
                patient=patient,
                insurance_name=f"Insurance{i}",
                insurance_type="PRIMARY",
                policy_number=f"POL{i}",
                effective_date=date(2023, 1, 1),
                insurance_company_name="Test Co",
            )

            # Add alert
            PatientAlert.objects.create(
                patient=patient,
                alert_type="ALLERGY",
                severity="HIGH",
                title=f"Allergy{i}",
                description=f"Test allergy {i}",
                created_by=self.user,
            )

        # Test CSV export
        response = self.client.get(reverse("patients:patient-export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

        # Parse CSV content
        csv_content = response.content.decode("utf-8")
        lines = csv_content.strip().split("\n")

        # Should have header + 5 patient rows
        self.assertEqual(len(lines), 6)

        # Verify data in CSV
        self.assertIn("Patient0,Test0", lines[1])
        self.assertIn("Patient1,Test1", lines[2])

    def test_patient_search_and_filter_workflow(self):
        """Test comprehensive patient search and filtering"""
        # Create diverse patient data
        patients_data = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": date(1990, 1, 1),
                "gender": "MALE",
                "status": "ACTIVE",
                "city": "New York",
            },
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "date_of_birth": date(1985, 5, 15),
                "gender": "FEMALE",
                "status": "ACTIVE",
                "city": "Boston",
            },
            {
                "first_name": "John",
                "last_name": "Smith",
                "date_of_birth": date(1980, 3, 10),
                "gender": "MALE",
                "status": "INACTIVE",
                "city": "Chicago",
            },
        ]

        created_patients = []
        for data in patients_data:
            patient = Patient.objects.create(hospital=self.hospital, **data)
            created_patients.append(patient)

        # Test search by first name
        response = self.api_client.get("/api/patients/search/", {"q": "John"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Test search by last name
        response = self.api_client.get("/api/patients/search/", {"q": "Doe"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Test filter by status
        response = self.api_client.get("/api/patients/", {"status": "ACTIVE"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Test filter by city
        response = self.api_client.get("/api/patients/", {"city": "New York"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Test combined search and filters
        response = self.api_client.get("/api/patients/", {"q": "John", "status": "ACTIVE"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_patient_data_integrity_workflow(self):
        """Test data integrity across patient operations"""
        # Create patient with comprehensive data
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="john.doe@example.com",
            phone_primary="555-123-4567",
        )

        # Add related data
        emergency_contact = EmergencyContact.objects.create(
            patient=patient, first_name="Jane", last_name="Doe", relationship="SPOUSE", phone_primary="555-987-6543"
        )

        insurance = InsuranceInformation.objects.create(
            patient=patient,
            insurance_name="Test Insurance",
            insurance_type="PRIMARY",
            policy_number="POL123",
            effective_date=date(2023, 1, 1),
            insurance_company_name="Test Co",
        )

        alert = PatientAlert.objects.create(
            patient=patient,
            alert_type="ALLERGY",
            severity="HIGH",
            title="Test Allergy",
            description="Test description",
            created_by=self.user,
        )

        # Update patient data
        patient.email = "john.new@example.com"
        patient.save()

        # Verify related data is still intact
        self.assertTrue(patient.emergency_contacts.exists())
        self.assertTrue(patient.insurance_plans.exists())
        self.assertTrue(patient.alerts.exists())

        # Test cascade behavior
        patient_id = patient.id
        patient.delete()

        # Verify related data is also deleted
        self.assertFalse(EmergencyContact.objects.filter(patient_id=patient_id).exists())
        self.assertFalse(InsuranceInformation.objects.filter(patient_id=patient_id).exists())
        self.assertFalse(PatientAlert.objects.filter(patient_id=patient_id).exists())

    def test_patient_performance_workflow(self):
        """Test performance of patient operations"""
        # Create multiple patients
        start_time = timezone.now()

        for i in range(100):
            Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Patient{i}",
                last_name=f"Test{i}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

        creation_time = (timezone.now() - start_time).total_seconds()
        print(f"Created 100 patients in {creation_time:.2f} seconds")

        # Test search performance
        start_time = timezone.now()
        response = self.api_client.get("/api/patients/search/", {"q": "Patient"})
        search_time = (timezone.now() - start_time).total_seconds()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 100)
        print(f"Searched 100 patients in {search_time:.2f} seconds")

        # Test list performance with pagination
        start_time = timezone.now()
        response = self.api_client.get("/api/patients/")
        list_time = (timezone.now() - start_time).total_seconds()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 20)  # Default page size
        print(f"Listed first 20 patients in {list_time:.2f} seconds")

        # Performance assertions (adjust thresholds as needed)
        self.assertLess(creation_time, 10.0, "Patient creation should be fast")
        self.assertLess(search_time, 2.0, "Patient search should be fast")
        self.assertLess(list_time, 1.0, "Patient listing should be fast")


class PatientDatabaseIntegrationTests(TransactionTestCase):
    """Database-level integration tests for patient data"""

    def test_database_constraints(self):
        """Test database constraint enforcement"""
        self.hospital = Mock()
        self.hospital.id = 1

        # Test unique constraint on UUID
        patient1 = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        with self.assertRaises(Exception):  # Should violate unique constraint
            patient2 = Patient(
                hospital=self.hospital,
                first_name="Jane",
                last_name="Doe",
                date_of_birth=date(1985, 1, 1),
                gender="FEMALE",
            )
            patient2.uuid = patient1.uuid
            patient2.save()

    def test_database_indexes(self):
        """Test database index usage"""
        self.hospital = Mock()
        self.hospital.id = 1

        # Create test data
        for i in range(100):
            Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Patient{i}",
                last_name=f"Test{i}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

        # Test index usage with explain
        with connection.cursor() as cursor:
            cursor.execute("EXPLAIN ANALYZE SELECT * FROM patients_patient WHERE last_name = 'Test0'")
            explain_plan = cursor.fetchone()[0]
            self.assertIn("Index Scan", explain_plan)

    def test_database_transactions(self):
        """Test database transaction behavior"""
        self.hospital = Mock()
        self.hospital.id = 1

        with transaction.atomic():
            patient = Patient.objects.create(
                hospital=self.hospital,
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

            # This should be rolled back
            with self.assertRaises(Exception):
                with transaction.atomic():
                    Patient.objects.create(
                        hospital=self.hospital,
                        first_name="Jane",
                        last_name="Invalid",
                        date_of_birth=None,  # Invalid
                        gender="FEMALE",
                    )

        # Only first patient should exist
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Patient.objects.get().first_name, "John")

    def test_database_cascade_operations(self):
        """Test database cascade operations"""
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = Mock()
        self.user.id = 1

        patient = Patient.objects.create(
            hospital=self.hospital, first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        EmergencyContact.objects.create(
            patient=patient, first_name="Jane", last_name="Doe", relationship="SPOUSE", phone_primary="555-123-4567"
        )

        InsuranceInformation.objects.create(
            patient=patient,
            insurance_name="Test Insurance",
            insurance_type="PRIMARY",
            policy_number="POL123",
            effective_date=date(2023, 1, 1),
            insurance_company_name="Test Co",
        )

        # Delete patient and verify cascade
        patient_id = patient.id
        patient.delete()

        self.assertFalse(Patient.objects.filter(id=patient_id).exists())
        self.assertFalse(EmergencyContact.objects.filter(patient_id=patient_id).exists())
        self.assertFalse(InsuranceInformation.objects.filter(patient_id=patient_id).exists())

    def test_database_concurrent_operations(self):
        """Test concurrent database operations"""
        self.hospital = Mock()
        self.hospital.id = 1

        def create_patient(i):
            return Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Concurrent{i}",
                last_name=f"Patient{i}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

        # Create patients concurrently
        import time
        from threading import Thread

        threads = []
        for i in range(10):
            thread = Thread(target=create_patient, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all patients were created
        self.assertEqual(Patient.objects.count(), 10)

        # Verify data integrity
        for i in range(10):
            patient = Patient.objects.get(first_name=f"Concurrent{i}")
            self.assertEqual(patient.last_name, f"Patient{i}")
