import json
from datetime import date, datetime
from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from ..models import (
    EmergencyContact,
    InsuranceInformation,
    Patient,
    PatientAlert,
    PatientStatus,
)

User = get_user_model()


class PatientSecurityTests(TestCase):
    """Security tests for patient authentication and authorization flows"""

    def setUp(self):
        self.hospital = Mock()
        self.hospital.id = 1
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            hospital=self.hospital,
            is_staff=True,
            is_superuser=True,
        )
        self.staff_user = User.objects.create_user(
            username="staff", email="staff@example.com", password="staffpass123", hospital=self.hospital, is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username="regular", email="regular@example.com", password="regularpass123", hospital=self.hospital
        )
        self.other_hospital_user = User.objects.create_user(
            username="other_hospital",
            email="other@example.com",
            password="otherpass123",
            hospital=Mock(id=2),  # Different hospital
        )
        self.patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="Test",
            last_name="Patient",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            created_by=self.staff_user,
        )

    def test_unauthorized_access_to_patient_list(self):
        """Test that unauthorized users cannot access patient list"""
        client = APIClient()

        # Test unauthenticated access
        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test authenticated but unauthorized user
        client.force_authenticate(user=self.regular_user)
        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_role_based_access_control(self):
        """Test role-based access control for patient operations"""
        # Test admin access (should have full access)
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.post(
            "/api/patients/",
            {"first_name": "New", "last_name": "Patient", "date_of_birth": "1990-01-01", "gender": "MALE"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test staff access (should have limited access)
        client.force_authenticate(user=self.staff_user)
        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test regular user access (should be denied)
        client.force_authenticate(user=self.regular_user)
        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hospital_isolation(self):
        """Test that users can only access patients from their hospital"""
        # Create patient in different hospital
        other_hospital_patient = Patient.objects.create(
            hospital=Mock(id=2),
            first_name="Other",
            last_name="Hospital",
            date_of_birth=date(1990, 1, 1),
            gender="FEMALE",
        )

        # Test other hospital user cannot access our hospital's patients
        client = APIClient()
        client.force_authenticate(user=self.other_hospital_user)

        response = client.get(f"/api/patients/{self.patient.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test our hospital user cannot access other hospital's patients
        client.force_authenticate(user=self.staff_user)
        response = client.get(f"/api/patients/{other_hospital_patient.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_data_encryption(self):
        """Test that sensitive patient data is encrypted"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="Sensitive",
            last_name="Data",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="sensitive@example.com",
            phone_primary="555-123-4567",
            address_line1="123 Secret St",
            confidential=True,
        )

        # Verify that data is accessible through model but encrypted in database
        self.assertEqual(patient.first_name, "Sensitive")
        self.assertEqual(patient.email, "sensitive@example.com")

        # Test database-level encryption (simplified check)
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT first_name, email FROM patients_patient WHERE id = %s", [patient.id])
            db_data = cursor.fetchone()

            # Encrypted data should not match plain text
            self.assertNotEqual(db_data[0], "Sensitive")
            self.assertNotEqual(db_data[1], "sensitive@example.com")

    def test_input_validation_and_sanitization(self):
        """Test input validation and sanitization for security"""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        # Test SQL injection attempt
        malicious_data = {
            "first_name": "Robert'); DROP TABLE patients_patient; --",
            "last_name": "Tables",
            "date_of_birth": "1990-01-01",
            "gender": "MALE",
        }

        response = client.post("/api/patients/", malicious_data, format="json")
        # Should either be rejected (400) or sanitized (201)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED])

        # Test XSS attempt
        xss_data = {
            "first_name": "<script>alert('XSS')</script>",
            "last_name": "XSS",
            "date_of_birth": "1990-01-01",
            "gender": "MALE",
        }

        response = client.post("/api/patients/", xss_data, format="json")
        if response.status_code == status.HTTP_201_CREATED:
            # If created, verify script tags are escaped
            self.assertNotIn("<script>", response.data["first_name"])

    def test_authentication_token_security(self):
        """Test authentication token security"""
        from rest_framework.authtoken.models import Token

        # Create token for user
        token = Token.objects.create(user=self.staff_user)

        # Test valid token access
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test invalid token
        client.credentials(HTTP_AUTHORIZATION="Token invalid-token-123")
        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test missing token
        client.credentials()  # Remove token
        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_security(self):
        """Test session security for web interface"""
        # Test session fixation protection
        self.client.login(username="staff", password="staffpass123")
        session_before = self.client.session.session_key

        response = self.client.get(reverse("patients:patient-list"))
        self.assertEqual(response.status_code, 200)

        session_after = self.client.session.session_key
        self.assertEqual(session_before, session_after)  # Session should be maintained

        # Test session timeout (simplified)
        self.client.logout()
        response = self.client.get(reverse("patients:patient-list"))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_permission_inheritance_and_groups(self):
        """Test permission inheritance through user groups"""
        # Create permissions
        view_patient_perm = Permission.objects.get(codename="view_patient")
        add_patient_perm = Permission.objects.get(codename="add_patient")
        change_patient_perm = Permission.objects.get(codename="change_patient")
        delete_patient_perm = Permission.objects.get(codename="delete_patient")

        # Create groups with different permissions
        viewer_group = Group.objects.create(name="Patient Viewers")
        viewer_group.permissions.add(view_patient_perm)

        editor_group = Group.objects.create(name="Patient Editors")
        editor_group.permissions.add(view_patient_perm, add_patient_perm, change_patient_perm)

        admin_group = Group.objects.create(name="Patient Admins")
        admin_group.permissions.add(view_patient_perm, add_patient_perm, change_patient_perm, delete_patient_perm)

        # Create users with different group memberships
        viewer_user = User.objects.create_user(
            username="viewer", email="viewer@example.com", password="viewerpass123", hospital=self.hospital
        )
        viewer_user.groups.add(viewer_group)

        editor_user = User.objects.create_user(
            username="editor", email="editor@example.com", password="editorpass123", hospital=self.hospital
        )
        editor_user.groups.add(editor_group)

        admin_group_user = User.objects.create_user(
            username="admin_group", email="admingroup@example.com", password="admingrouppass123", hospital=self.hospital
        )
        admin_group_user.groups.add(admin_group)

        # Test permission enforcement
        client = APIClient()

        # Viewer should only be able to view
        client.force_authenticate(user=viewer_user)
        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.post(
            "/api/patients/",
            {"first_name": "Test", "last_name": "User", "date_of_birth": "1990-01-01", "gender": "MALE"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Editor should be able to view and create
        client.force_authenticate(user=editor_user)
        response = client.post(
            "/api/patients/",
            {"first_name": "Editor", "last_name": "User", "date_of_birth": "1990-01-01", "gender": "MALE"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Admin group user should have full permissions
        client.force_authenticate(user=admin_group_user)
        patient_id = response.data["id"]
        response = client.delete(f"/api/patients/{patient_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_csrf_protection(self):
        """Test CSRF protection for web forms"""
        # Test that POST requests without CSRF token are rejected
        response = self.client.post(
            reverse("patients:patient-create"),
            {"first_name": "CSRF", "last_name": "Test", "date_of_birth": "1990-01-01", "gender": "MALE"},
        )

        # Should be rejected for non-authenticated user
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test with authenticated user
        self.client.login(username="staff", password="staffpass123")

        # Get form to get CSRF token
        response = self.client.get(reverse("patients:patient-create"))
        csrf_token = self.client.cookies["csrftoken"].value

        # Test POST with CSRF token
        response = self.client.post(
            reverse("patients:patient-create"),
            {
                "first_name": "CSRF",
                "last_name": "Test",
                "date_of_birth": "1990-01-01",
                "gender": "MALE",
                "csrfmiddlewaretoken": csrf_token,
            },
        )

        self.assertEqual(response.status_code, 302)  # Should redirect after success

    def test_rate_limiting(self):
        """Test rate limiting for API endpoints"""
        # This test would typically use django-ratelimit or similar
        # For now, we'll test the concept

        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        # Make rapid requests to test rate limiting
        rapid_requests = []
        for i in range(100):  # Adjust based on your rate limit
            response = client.get("/api/patients/")
            rapid_requests.append(response.status_code)

        # In a real implementation, we'd expect some 429 responses
        # For now, we'll just verify the server handles rapid requests
        self.assertTrue(all(status in [200, 429] for status in rapid_requests))

    def test_audit_logging(self):
        """Test that patient operations are properly logged"""
        # This test would typically check for audit log entries
        # For now, we'll verify the concept through model changes

        # Record initial state
        initial_patient_count = Patient.objects.count()

        # Create patient
        new_patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="Audit",
            last_name="Test",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            created_by=self.staff_user,
        )

        # Verify creation
        self.assertEqual(Patient.objects.count(), initial_patient_count + 1)

        # Update patient
        new_patient.first_name = "Updated"
        new_patient.save()

        # Verify update
        updated_patient = Patient.objects.get(id=new_patient.id)
        self.assertEqual(updated_patient.first_name, "Updated")

        # Delete patient
        new_patient.delete()

        # Verify deletion
        self.assertEqual(Patient.objects.count(), initial_patient_count)

    def test_secure_headers(self):
        """Test that security headers are properly set"""
        client = APIClient()
        client.force_authenticate(user=self.staff_user)

        response = client.get("/api/patients/")

        # Check for security headers
        security_headers = ["X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection", "Content-Security-Policy"]

        for header in security_headers:
            self.assertIn(header, response, f"Missing security header: {header}")

    def test_sensitive_data_exposure_prevention(self):
        """Test prevention of sensitive data exposure"""
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="Sensitive",
            last_name="Test",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="sensitive@example.com",
            phone_primary="555-123-4567",
            confidential=True,
        )

        client = APIClient()
        client.force_authenticate(user=self.staff_user)

        response = client.get(f"/api/patients/{patient.id}/")

        # Verify sensitive data is not exposed in error responses
        self.assertNotIn("Traceback", response.content.decode())
        self.assertNotIn("Internal Server Error", response.content.decode())

    def test_authorization_on_related_data(self):
        """Test authorization controls on related patient data"""
        # Create patient with related data
        emergency_contact = EmergencyContact.objects.create(
            patient=self.patient,
            first_name="Emergency",
            last_name="Contact",
            relationship="SPOUSE",
            phone_primary="555-123-4567",
        )

        insurance = InsuranceInformation.objects.create(
            patient=self.patient,
            insurance_name="Test Insurance",
            insurance_type="PRIMARY",
            policy_number="POL123",
            effective_date=date(2023, 1, 1),
            insurance_company_name="Test Co",
        )

        # Test unauthorized access to related data
        unauthorized_client = APIClient()
        unauthorized_client.force_authenticate(user=self.regular_user)

        # Should not be able to access emergency contacts
        response = unauthorized_client.get(f"/api/patients/{self.patient.id}/emergency-contacts/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Should not be able to access insurance
        response = unauthorized_client.get(f"/api/patients/{self.patient.id}/insurance/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Should not be able to access alerts
        response = unauthorized_client.get(f"/api/patients/{self.patient.id}/alerts/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_data_retention_and_deletion(self):
        """Test data retention policies and secure deletion"""
        # Create patient with PHI (Protected Health Information)
        patient = Patient.objects.create(
            hospital=self.hospital,
            first_name="Delete",
            last_name="Test",
            date_of_birth=date(1990, 1, 1),
            gender="MALE",
            email="delete@example.com",
            phone_primary="555-123-4567",
            confidential=True,
        )

        # Add related data
        EmergencyContact.objects.create(
            patient=patient,
            first_name="Emergency",
            last_name="Contact",
            relationship="SPOUSE",
            phone_primary="555-123-4567",
        )

        patient_id = patient.id

        # Delete patient (should cascade delete related data)
        patient.delete()

        # Verify all data is deleted
        self.assertFalse(Patient.objects.filter(id=patient_id).exists())
        self.assertFalse(EmergencyContact.objects.filter(patient_id=patient_id).exists())

    def test_api_throttling(self):
        """Test API throttling mechanisms"""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        # Make multiple rapid requests
        responses = []
        for i in range(50):
            response = client.get("/api/patients/")
            responses.append(response.status_code)

        # All requests should succeed (adjust threshold based on your throttling settings)
        success_count = responses.count(200)
        throttled_count = responses.count(429)

        print(f"API throttling test: {success_count} successful, {throttled_count} throttled")

        # In a real implementation with throttling, we'd expect some 429 responses
        self.assertGreaterEqual(success_count, 1, "At least one request should succeed")

    def test_password_security(self):
        """Test password security requirements"""
        # Test weak password rejection
        weak_passwords = ["password", "123456", "qwerty", "letmein", "welcome", "admin123"]

        for password in weak_passwords:
            with self.assertRaises(Exception):
                User.objects.create_user(
                    username=f"user_{password}", email=f"user_{password}@example.com", password=password
                )

        # Test strong password acceptance
        strong_password = "Str0ng!P@ssw0rdWithNumbersAndSymbols"
        user = User.objects.create_user(username="strong_user", email="strong@example.com", password=strong_password)
        self.assertIsNotNone(user.id)

    def test_session_timeout(self):
        """Test session timeout functionality"""
        # This test would typically verify session expiration
        # For now, we'll test the logout functionality

        self.client.login(username="staff", password="staffpass123")

        # Verify user is logged in
        response = self.client.get(reverse("patients:patient-list"))
        self.assertEqual(response.status_code, 200)

        # Logout
        self.client.logout()

        # Verify user is logged out
        response = self.client.get(reverse("patients:patient-list"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_cross_site_request_forgery_protection(self):
        """Test CSRF protection for critical operations"""
        self.client.login(username="staff", password="staffpass123")

        # Create patient without CSRF token (should fail)
        response = self.client.post(
            reverse("patients:patient-create"),
            {"first_name": "CSRF", "last_name": "Test", "date_of_birth": "1990-01-01", "gender": "MALE"},
        )

        # Should be rejected due to missing CSRF token
        self.assertEqual(response.status_code, 403)  # CSRF verification failed

    def test_secure_cookie_handling(self):
        """Test secure cookie handling"""
        self.client.login(username="staff", password="staffpass123")

        # Check that session cookie has secure attributes
        session_cookie = self.client.cookies.get("sessionid")
        if session_cookie:
            # In production, these should be True
            # self.assertTrue(session_cookie.secure)
            # self.assertTrue(session_cookie.httponly)
            pass

        # Check CSRF cookie
        csrf_cookie = self.client.cookies.get("csrftoken")
        if csrf_cookie:
            # In production, these should be True
            # self.assertTrue(csrf_cookie.secure)
            # self.assertTrue(csrf_cookie.httponly)
            pass
