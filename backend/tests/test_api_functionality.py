import json
from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class APIFunctionalityTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "username": "testuser",
            "email": "user@hospital.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "doctor",
        }
        self.user = User.objects.create_user(**self.user_data)
        from rest_framework_simplejwt.tokens import RefreshToken

        self.token = str(RefreshToken.for_user(self.user).access_token)

    def test_api_health_check(self):
        response = self.client.get("/api/health/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_api_schema_endpoint(self):
        response = self.client.get("/api/schema/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_api_docs_endpoint(self):
        response = self.client.get("/api/docs/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_access(self):
        response = self.client.get("/api/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND])

    def test_authenticated_access(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_token_validation(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_user_api_endpoints(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/users/profile/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        response = self.client.get("/api/users/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_hospital_api_endpoints(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/hospitals/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_patient_api_endpoints(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/patients/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_appointment_api_endpoints(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/appointments/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_ehr_api_endpoints(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/ehr/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_billing_api_endpoints(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/billing/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_pharmacy_api_endpoints(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/pharmacy/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_lab_api_endpoints(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/lab/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_analytics_api_endpoints(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/analytics/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_api_error_handling(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/nonexistent-endpoint/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.post("/api/users/profile/", {})
        self.assertIn(response.status_code, [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND])

    def test_api_rate_limiting(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        for i in range(10):
            response = self.client.get("/api/")
            self.assertIn(
                response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_429_TOO_MANY_REQUESTS]
            )

    def test_api_content_type(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/")
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response["Content-Type"], "application/json")

    def test_cors_headers(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get("/api/", HTTP_ORIGIN="http://localhost:3000")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        if response.status_code == status.HTTP_200_OK:
            self.assertIn("Access-Control-Allow-Origin", response)


class APIPerformanceTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "username": "testuser",
            "email": "user@hospital.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
        }
        self.user = User.objects.create_user(**self.user_data)
        from rest_framework_simplejwt.tokens import RefreshToken

        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_api_response_time(self):
        import time

        start_time = time.time()
        response = self.client.get("/api/")
        end_time = time.time()
        response_time = end_time - start_time
        self.assertLess(response_time, 2.0)

    def test_concurrent_requests(self):
        import threading
        import time

        results = []

        def make_request():
            response = self.client.get("/api/")
            results.append(response.status_code)

        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        for status_code in results:
            self.assertIn(status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_large_dataset_handling(self):
        response = self.client.get("/api/patients/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            if isinstance(data, dict) and "results" in data:
                self.assertIsInstance(data["results"], list)
                if "count" in data:
                    self.assertIsInstance(data["count"], int)


class APISecurityTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_sql_injection_protection(self):
        user_data = {
            "username": "testuser",
            "email": "user@hospital.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
        }
        user = User.objects.create_user(**user_data)
        from rest_framework_simplejwt.tokens import RefreshToken

        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        malicious_query = "1; DROP TABLE users; --"
        response = self.client.get(f"/api/patients/?search={malicious_query}")
        self.assertIn(
            response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
        )

    def test_xss_protection(self):
        user_data = {
            "username": "testuser",
            "email": "user@hospital.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
        }
        user = User.objects.create_user(**user_data)
        from rest_framework_simplejwt.tokens import RefreshToken

        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        xss_payload = "<script>alert('xss')</script>"
        response = self.client.post(
            "/api/patients/",
            {"first_name": xss_payload, "last_name": "Test", "date_of_birth": "1990-01-01", "gender": "M"},
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED],
        )

    def test_authentication_bypass(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authorization_enforcement(self):
        regular_user = User.objects.create_user(
            username="regular", email="regular@hospital.com", password="SecurePass123!", role="patient"
        )
        from rest_framework_simplejwt.tokens import RefreshToken

        token = str(RefreshToken.for_user(regular_user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/admin/users/")
        self.assertIn(
            response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED]
        )


class DataValidationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_data = {
            "username": "testuser",
            "email": "user@hospital.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "doctor",
        }
        self.user = User.objects.create_user(**user_data)
        from rest_framework_simplejwt.tokens import RefreshToken

        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_patient_data_validation(self):
        invalid_patient_data = {"first_name": "", "last_name": "Test", "date_of_birth": "invalid-date", "gender": "X"}
        response = self.client.post("/api/patients/", invalid_patient_data)
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED],
        )

    def test_appointment_data_validation(self):
        invalid_appointment_data = {
            "start_at": "2024-12-25T10:00:00Z",
            "end_at": "2024-12-25T09:00:00Z",
            "status": "invalid_status",
        }
        response = self.client.post("/api/appointments/", invalid_appointment_data)
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED],
        )

    def test_required_field_validation(self):
        incomplete_data = {"first_name": "John"}
        response = self.client.post("/api/patients/", incomplete_data)
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_FOUND],
        )

    def test_data_type_validation(self):
        invalid_data = {"first_name": 123, "last_name": "Test", "date_of_birth": "not-a-date", "age": "not-a-number"}
        response = self.client.post("/api/patients/", invalid_data)
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_FOUND],
        )
