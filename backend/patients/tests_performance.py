import json
import queue
import threading
import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from ..models import (
    EmergencyContact,
    InsuranceInformation,
    Patient,
    PatientAlert,
    PatientStatus,
)

User = get_user_model()


class PatientPerformanceTests(TestCase):
    """Performance tests for patient operations under various load conditions"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.user = User.objects.create_user(
            username="perfuser", email="perf@example.com", password="perfpass123", hospital=self.hospital, is_staff=True
        )
        self.client.force_login(self.user)
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)

    def test_bulk_patient_creation_performance(self):
        """Test performance of bulk patient creation"""
        num_patients = 1000
        patients_data = []

        start_time = time.time()

        # Create patients in bulk
        for i in range(num_patients):
            patient = Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Patient{i:04d}",
                last_name=f"Test{i:04d}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )
            patients_data.append(patient)

        creation_time = time.time() - start_time

        # Performance assertions
        self.assertEqual(Patient.objects.count(), num_patients)
        self.assertLess(creation_time, 30.0, f"Created {num_patients} patients in {creation_time:.2f}s")

        print(
            f"✓ Created {num_patients} patients in {creation_time:.2f}s ({num_patients/creation_time:.2f} patients/sec)"
        )

    def test_patient_search_performance(self):
        """Test performance of patient search operations"""
        # Create test data
        num_patients = 500
        for i in range(num_patients):
            Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Search{i:04d}",
                last_name=f"Patient{i:04d}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
                medical_record_number=f"MRN{i:08d}",
            )

        # Test search by first name
        start_time = time.time()
        response = self.api_client.get("/api/patients/search/", {"q": "Search"})
        search_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), num_patients)
        self.assertLess(search_time, 2.0, f"Search completed in {search_time:.2f}s")

        print(f"✓ Searched {num_patients} patients by first name in {search_time:.2f}s")

        # Test search by MRN
        start_time = time.time()
        response = self.api_client.get("/api/patients/search/", {"q": "MRN"})
        search_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), num_patients)
        self.assertLess(search_time, 2.0, f"MRN search completed in {search_time:.2f}s")

        print(f"✓ Searched {num_patients} patients by MRN in {search_time:.2f}s")

    def test_patient_list_pagination_performance(self):
        """Test performance of patient list pagination"""
        # Create test data
        num_patients = 1000
        for i in range(num_patients):
            Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Page{i:04d}",
                last_name=f"Patient{i:04d}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

        # Test first page load
        start_time = time.time()
        response = self.api_client.get("/api/patients/")
        first_page_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 20)  # Default page size
        self.assertLess(first_page_time, 1.0, f"First page loaded in {first_page_time:.2f}s")

        print(f"✓ Loaded first page (20 patients) in {first_page_time:.2f}s")

        # Test pagination through all pages
        total_pages = response.data["count"] // 20 + (1 if response.data["count"] % 20 else 0)
        start_time = time.time()

        for page in range(2, min(total_pages + 1, 6)):  # Test first 5 pages
            response = self.api_client.get("/api/patients/", {"page": page})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data["results"]), 20)

        pagination_time = time.time() - start_time
        self.assertLess(pagination_time, 3.0, f"Paginated through 5 pages in {pagination_time:.2f}s")

        print(f"✓ Paginated through 5 pages in {pagination_time:.2f}s")

    def test_concurrent_patient_creation(self):
        """Test concurrent patient creation performance"""
        num_threads = 10
        patients_per_thread = 50
        results = queue.Queue()

        def create_patients(thread_id, results_queue):
            try:
                start_time = time.time()
                for i in range(patients_per_thread):
                    Patient.objects.create(
                        hospital=self.hospital,
                        first_name=f"Concurrent{thread_id:02d}_{i:02d}",
                        last_name=f"Patient{thread_id:02d}_{i:02d}",
                        date_of_birth=date(1990, 1, 1),
                        gender="MALE",
                    )
                end_time = time.time()
                results_queue.put(("success", end_time - start_time))
            except Exception as e:
                results_queue.put(("error", str(e)))

        # Start concurrent threads
        threads = []
        start_time = time.time()

        for i in range(num_threads):
            thread = threading.Thread(target=create_patients, args=(i, results))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Collect results
        success_count = 0
        error_count = 0
        thread_times = []

        while not results.empty():
            result_type, result_data = results.get()
            if result_type == "success":
                success_count += 1
                thread_times.append(result_data)
            else:
                error_count += 1
                print(f"Thread error: {result_data}")

        # Verify results
        expected_patients = num_threads * patients_per_thread
        self.assertEqual(Patient.objects.count(), expected_patients)
        self.assertEqual(success_count, num_threads)
        self.assertEqual(error_count, 0)
        self.assertLess(total_time, 10.0, f"Concurrent creation completed in {total_time:.2f}s")

        print(f"✓ Concurrently created {expected_patients} patients using {num_threads} threads in {total_time:.2f}s")

    def test_patient_filter_performance(self):
        """Test performance of patient filtering operations"""
        # Create diverse test data
        statuses = ["ACTIVE", "INACTIVE", "DECEASED", "TRANSFERRED"]
        genders = ["MALE", "FEMALE"]
        cities = ["New York", "Boston", "Chicago", "Los Angeles"]

        for i in range(500):
            Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Filter{i:04d}",
                last_name=f"Patient{i:04d}",
                date_of_birth=date(1990, 1, 1),
                gender=genders[i % len(genders)],
                status=statuses[i % len(statuses)],
                city=cities[i % len(cities)],
            )

        # Test single filter performance
        start_time = time.time()
        response = self.api_client.get("/api/patients/", {"status": "ACTIVE"})
        filter_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(filter_time, 1.0, f"Single filter completed in {filter_time:.2f}s")

        print(f"✓ Single status filter completed in {filter_time:.2f}s")

        # Test multiple filter performance
        start_time = time.time()
        response = self.api_client.get("/api/patients/", {"status": "ACTIVE", "gender": "MALE", "city": "New York"})
        multi_filter_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(multi_filter_time, 1.5, f"Multi-filter completed in {multi_filter_time:.2f}s")

        print(f"✓ Multi-filter completed in {multi_filter_time:.2f}s")

    def test_patient_update_performance(self):
        """Test performance of patient update operations"""
        # Create test patients
        num_patients = 100
        patients = []
        for i in range(num_patients):
            patient = Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Update{i:04d}",
                last_name=f"Patient{i:04d}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )
            patients.append(patient)

        # Test bulk update performance
        start_time = time.time()

        for patient in patients:
            patient.first_name = f"Updated{patient.first_name}"
            patient.phone_primary = "555-UPDATED"
            patient.email = f"updated{i:04d}@example.com"
            patient.save()

        update_time = time.time() - start_time

        self.assertLess(update_time, 5.0, f"Updated {num_patients} patients in {update_time:.2f}s")

        print(f"✓ Updated {num_patients} patients in {update_time:.2f}s ({num_patients/update_time:.2f} patients/sec)")

    def test_patient_delete_performance(self):
        """Test performance of patient deletion operations"""
        # Create test patients
        num_patients = 100
        patient_ids = []
        for i in range(num_patients):
            patient = Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Delete{i:04d}",
                last_name=f"Patient{i:04d}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )
            patient_ids.append(patient.id)

        # Test bulk deletion performance
        start_time = time.time()

        for patient_id in patient_ids:
            patient = Patient.objects.get(id=patient_id)
            patient.delete()

        delete_time = time.time() - start_time

        self.assertEqual(Patient.objects.count(), 0)
        self.assertLess(delete_time, 3.0, f"Deleted {num_patients} patients in {delete_time:.2f}s")

        print(f"✓ Deleted {num_patients} patients in {delete_time:.2f}s ({num_patients/delete_time:.2f} patients/sec)")

    def test_patient_relationship_performance(self):
        """Test performance of patient relationship operations"""
        # Create base patient
        patient = Patient.objects.create(
            hospital=self.hospital, first_name="Rel", last_name="Patient", date_of_birth=date(1990, 1, 1), gender="MALE"
        )

        # Test adding multiple emergency contacts
        start_time = time.time()

        for i in range(20):
            EmergencyContact.objects.create(
                patient=patient,
                first_name=f"Contact{i:02d}",
                last_name=f"Emergency{i:02d}",
                relationship="SPOUSE" if i == 0 else "OTHER",
                phone_primary=f"555-CONTACT-{i:02d}",
            )

        contact_time = time.time() - start_time
        self.assertLess(contact_time, 2.0, f"Added 20 emergency contacts in {contact_time:.2f}s")

        print(f"✓ Added 20 emergency contacts in {contact_time:.2f}s")

        # Test adding multiple insurance plans
        start_time = time.time()

        insurance_types = ["PRIMARY", "SECONDARY", "TERTIARY"]
        for i in range(10):
            InsuranceInformation.objects.create(
                patient=patient,
                insurance_name=f"Insurance{i:02d}",
                insurance_type=insurance_types[i % len(insurance_types)],
                policy_number=f"POL{i:08d}",
                effective_date=date(2023, 1, 1),
                insurance_company_name=f"Insurance Co {i:02d}",
            )

        insurance_time = time.time() - start_time
        self.assertLess(insurance_time, 2.0, f"Added 10 insurance plans in {insurance_time:.2f}s")

        print(f"✓ Added 10 insurance plans in {insurance_time:.2f}s")

        # Test adding multiple alerts
        start_time = time.time()

        alert_types = ["ALLERGY", "SAFETY", "CLINICAL", "FALL_RISK"]
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        for i in range(15):
            PatientAlert.objects.create(
                patient=patient,
                alert_type=alert_types[i % len(alert_types)],
                severity=severities[i % len(severities)],
                title=f"Alert {i:02d}",
                description=f"Test alert description {i:02d}",
                created_by=self.user,
            )

        alert_time = time.time() - start_time
        self.assertLess(alert_time, 2.0, f"Added 15 alerts in {alert_time:.2f}s")

        print(f"✓ Added 15 alerts in {alert_time:.2f}s")

        # Test relationship query performance
        start_time = time.time()

        patient_data = self.api_client.get(f"/api/patients/{patient.id}/").data
        query_time = time.time() - start_time

        self.assertEqual(len(patient_data["emergency_contacts"]), 20)
        self.assertEqual(len(patient_data["insurance_plans"]), 10)
        self.assertEqual(len(patient_data["alerts"]), 15)
        self.assertLess(query_time, 1.0, f"Queried all relationships in {query_time:.2f}s")

        print(f"✓ Queried all relationships (45 total) in {query_time:.2f}s")

    def test_database_query_optimization(self):
        """Test database query optimization for patient operations"""
        # Create test data with relationships
        num_patients = 100
        for i in range(num_patients):
            patient = Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Opt{i:04d}",
                last_name=f"Patient{i:04d}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

            # Add related data for half the patients
            if i % 2 == 0:
                EmergencyContact.objects.create(
                    patient=patient,
                    first_name="Contact",
                    last_name=f"Emergency{i:04d}",
                    relationship="SPOUSE",
                    phone_primary="555-CONTACT",
                )

                InsuranceInformation.objects.create(
                    patient=patient,
                    insurance_name="Test Insurance",
                    insurance_type="PRIMARY",
                    policy_number=f"POL{i:08d}",
                    effective_date=date(2023, 1, 1),
                    insurance_company_name="Test Co",
                )

        # Test optimized query performance
        start_time = time.time()

        # Use select_related and prefetch_related for optimization
        patients = (
            Patient.objects.select_related("hospital")
            .prefetch_related("emergency_contacts", "insurance_plans", "alerts")
            .filter(status="ACTIVE")
        )

        # Force evaluation
        patient_list = list(patients)
        query_time = time.time() - start_time

        self.assertEqual(len(patient_list), num_patients)
        self.assertLess(query_time, 1.0, f"Optimized query completed in {query_time:.2f}s")

        print(f"✓ Optimized query with relationships for {num_patients} patients completed in {query_time:.2f}s")

        # Test unoptimized query for comparison
        start_time = time.time()

        patients_unoptimized = Patient.objects.filter(status="ACTIVE")
        patient_list_unoptimized = list(patients_unoptimized)

        # Access relationships to trigger additional queries
        for patient in patient_list_unoptimized[:10]:  # Test first 10
            list(patient.emergency_contacts.all())
            list(patient.insurance_plans.all())

        unoptimized_time = time.time() - start_time
        self.assertLess(query_time, unoptimized_time, "Optimized query should be faster than unoptimized")

        print(f"✓ Unoptimized query (10 patients with relationships) completed in {unoptimized_time:.2f}s")

    def test_memory_usage_performance(self):
        """Test memory usage during patient operations"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create large number of patients
        num_patients = 1000
        for i in range(num_patients):
            Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Memory{i:04d}",
                last_name=f"Patient{i:04d}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Memory usage should be reasonable
        self.assertLess(memory_increase, 500, f"Memory increase of {memory_increase:.2f}MB is too high")

        print(f"✓ Memory usage: {initial_memory:.2f}MB → {peak_memory:.2f}MB (+{memory_increase:.2f}MB)")

    def test_concurrent_api_requests(self):
        """Test performance under concurrent API requests"""
        # Create test data
        for i in range(100):
            Patient.objects.create(
                hospital=self.hospital,
                first_name=f"API{i:04d}",
                last_name=f"Patient{i:04d}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

        num_threads = 20
        requests_per_thread = 10
        results = queue.Queue()

        def make_api_requests(thread_id, results_queue):
            try:
                start_time = time.time()
                success_count = 0
                error_count = 0

                for i in range(requests_per_thread):
                    try:
                        # Mix different API endpoints
                        if i % 4 == 0:
                            response = self.api_client.get("/api/patients/")
                        elif i % 4 == 1:
                            response = self.api_client.get("/api/patients/search/", {"q": "API"})
                        elif i % 4 == 2:
                            response = self.api_client.get("/api/patients/stats/")
                        else:
                            response = self.api_client.get("/api/patients/", {"page": 1, "page_size": 10})

                        if response.status_code == 200:
                            success_count += 1
                        else:
                            error_count += 1
                    except Exception:
                        error_count += 1

                end_time = time.time()
                results_queue.put(
                    {
                        "thread_id": thread_id,
                        "success_count": success_count,
                        "error_count": error_count,
                        "duration": end_time - start_time,
                    }
                )
            except Exception as e:
                results_queue.put({"thread_id": thread_id, "error": str(e)})

        # Start concurrent API request threads
        threads = []
        start_time = time.time()

        for i in range(num_threads):
            thread = threading.Thread(target=make_api_requests, args=(i, results))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Collect results
        total_success = 0
        total_errors = 0
        thread_times = []

        while not results.empty():
            result = results.get()
            if "error" in result:
                print(f"Thread {result['thread_id']} error: {result['error']}")
            else:
                total_success += result["success_count"]
                total_errors += result["error_count"]
                thread_times.append(result["duration"])

        total_requests = num_threads * requests_per_thread
        success_rate = (total_success / total_requests) * 100

        # Performance assertions
        self.assertEqual(total_errors, 0, f"No errors expected, got {total_errors}")
        self.assertLess(total_time, 10.0, f"Concurrent API requests completed in {total_time:.2f}s")
        self.assertGreaterEqual(success_rate, 95.0, f"Success rate should be >= 95%, got {success_rate:.1f}%")

        print(
            f"✓ {total_requests} concurrent API requests: {total_success} success, {total_errors} errors in {total_time:.2f}s"
        )
        print(f"✓ Success rate: {success_rate:.1f}%")
        print(f"✓ Average requests per second: {total_requests/total_time:.2f}")

    def test_export_performance(self):
        """Test performance of patient data export"""
        # Create test data
        num_patients = 1000
        for i in range(num_patients):
            patient = Patient.objects.create(
                hospital=self.hospital,
                first_name=f"Export{i:04d}",
                last_name=f"Patient{i:04d}",
                date_of_birth=date(1990, 1, 1),
                gender="MALE",
            )

            # Add related data
            if i % 3 == 0:
                EmergencyContact.objects.create(
                    patient=patient,
                    first_name="Contact",
                    last_name=f"Emergency{i:04d}",
                    relationship="SPOUSE",
                    phone_primary="555-CONTACT",
                )

        # Test CSV export performance
        start_time = time.time()
        response = self.client.get(reverse("patients:patient-export"))
        export_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertLess(export_time, 5.0, f"CSV export completed in {export_time:.2f}s")

        # Verify content
        csv_content = response.content.decode("utf-8")
        lines = csv_content.strip().split("\n")
        self.assertEqual(len(lines), num_patients + 1)  # Header + data rows

        print(f"✓ CSV export of {num_patients} patients completed in {export_time:.2f}s")

    @override_settings(DEBUG=True)
    def test_database_connection_pooling(self):
        """Test database connection pooling performance"""
        num_connections = 50
        results = queue.Queue()

        def test_connection(connection_id, results_queue):
            try:
                start_time = time.time()

                # Perform database operations
                patient = Patient.objects.create(
                    hospital=self.hospital,
                    first_name=f"Pool{connection_id:03d}",
                    last_name=f"Patient{connection_id:03d}",
                    date_of_birth=date(1990, 1, 1),
                    gender="MALE",
                )

                # Query patient
                retrieved_patient = Patient.objects.get(id=patient.id)
                self.assertEqual(retrieved_patient.first_name, f"Pool{connection_id:03d}")

                # Delete patient
                patient.delete()

                end_time = time.time()
                results_queue.put({"connection_id": connection_id, "duration": end_time - start_time, "success": True})
            except Exception as e:
                results_queue.put({"connection_id": connection_id, "error": str(e), "success": False})

        # Start connection test threads
        threads = []
        start_time = time.time()

        for i in range(num_connections):
            thread = threading.Thread(target=test_connection, args=(i, results))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Collect results
        success_count = 0
        error_count = 0
        connection_times = []

        while not results.empty():
            result = results.get()
            if result["success"]:
                success_count += 1
                connection_times.append(result["duration"])
            else:
                error_count += 1
                print(f"Connection {result['connection_id']} error: {result['error']}")

        # Performance assertions
        self.assertEqual(success_count, num_connections, f"All {num_connections} connections should succeed")
        self.assertEqual(error_count, 0)
        self.assertLess(total_time, 15.0, f"Connection pooling test completed in {total_time:.2f}s")

        if connection_times:
            avg_time = sum(connection_times) / len(connection_times)
            print(f"✓ {num_connections} concurrent database connections: {success_count} success, {error_count} errors")
            print(f"✓ Average connection time: {avg_time:.3f}s")
            print(f"✓ Total time: {total_time:.2f}s")
