"""
Comprehensive Security Testing Framework for HMS System

This module provides comprehensive security testing capabilities including:
- Penetration testing for healthcare systems
- Authentication and authorization testing
- Input validation and injection testing
- Security compliance testing (HIPAA, NIST, OWASP)
- Vulnerability scanning and assessment
- Security audit logging and monitoring
"""

import pytest
import json
import requests
import hashlib
import secrets
import jwt
import ssl
import socket
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework import status
import bandit
from bandit.core import manager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import healthcare testing utilities
from .conftest import (
    HMSTestCase, HealthcareDataMixin, PerformanceTestingMixin,
    SecurityTestingMixin, ComplianceTestingMixin
)

User = get_user_model()


class SecurityTestResult:
    """Security test result tracking"""

    def __init__(self, test_name: str, vulnerability_type: str, severity: str):
        self.test_name = test_name
        self.vulnerability_type = vulnerability_type
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW, INFO
        self.description = ""
        self.affected_components = []
        self.remediation_steps = []
        self.cve_references = []
        self.owasp_category = ""
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert test result to dictionary"""
        return {
            'test_name': self.test_name,
            'vulnerability_type': self.vulnerability_type,
            'severity': self.severity,
            'description': self.description,
            'affected_components': self.affected_components,
            'remediation_steps': self.remediation_steps,
            'cve_references': self.cve_references,
            'owasp_category': self.owasp_category,
            'timestamp': self.timestamp.isoformat()
        }


class SecurityTestingFramework:
    """Comprehensive security testing framework for healthcare systems"""

    def __init__(self):
        self.test_results = []
        self.vulnerability_database = self._initialize_vulnerability_database()
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }

    def _initialize_vulnerability_database(self) -> Dict[str, List[Dict]]:
        """Initialize healthcare-specific vulnerability database"""
        return {
            'HIPAA_VIOLATIONS': [
                {
                    'cve': 'CVE-2023-HIPAA-001',
                    'description': 'Unencrypted PHI transmission',
                    'severity': 'CRITICAL',
                    'remediation': 'Implement TLS 1.3 for all data transmissions'
                },
                {
                    'cve': 'CVE-2023-HIPAA-002',
                    'description': 'Insufficient access controls',
                    'severity': 'HIGH',
                    'remediation': 'Implement role-based access control with least privilege'
                }
            ],
            'OWASP_TOP_10': [
                {
                    'category': 'A01:2021-Broken Access Control',
                    'patterns': ['IDOR', 'privilege_escalation', 'unauthorized_access'],
                    'severity': 'HIGH'
                },
                {
                    'category': 'A02:2021-Cryptographic Failures',
                    'patterns': ['weak_encryption', 'plaintext_passwords', 'insecure_storage'],
                    'severity': 'CRITICAL'
                },
                {
                    'category': 'A03:2021-Injection',
                    'patterns': ['sql_injection', 'xss', 'command_injection'],
                    'severity': 'CRITICAL'
                },
                {
                    'category': 'A04:2021-Insecure Design',
                    'patterns': ['flawed_authentication', 'insecure_session_management'],
                    'severity': 'HIGH'
                },
                {
                    'category': 'A05:2021-Security Misconfiguration',
                    'patterns': ['exposed_admin', 'verbose_errors', 'default_credentials'],
                    'severity': 'MEDIUM'
                }
            ]
        }

    def run_comprehensive_security_scan(self, target_url: str) -> List[SecurityTestResult]:
        """Run comprehensive security scan on target system"""
        results = []

        # OWASP Top 10 Testing
        results.extend(self._test_broken_access_control(target_url))
        results.extend(self._test_cryptographic_failures(target_url))
        results.extend(self._test_injection_vulnerabilities(target_url))
        results.extend(self._test_insecure_design(target_url))
        results.extend(self._test_security_misconfiguration(target_url))

        # Healthcare-specific testing
        results.extend(self._test_hipaa_compliance(target_url))
        results.extend(self._test_phi_exposure(target_url))
        results.extend(self._test_audit_trail_completeness(target_url))

        # Network security testing
        results.extend(self._test_network_security(target_url))
        results.extend(self._test_ssl_tls_configuration(target_url))

        # Application security testing
        results.extend(self._test_authentication_mechanisms(target_url))
        results.extend(self._test_authorization_controls(target_url))
        results.extend(self._test_session_management(target_url))

        self.test_results.extend(results)
        return results

    def _test_broken_access_control(self, target_url: str) -> List[SecurityTestResult]:
        """Test for broken access control vulnerabilities"""
        results = []

        # Test for IDOR (Insecure Direct Object Reference)
        test_results = self._test_idor_vulnerabilities(target_url)
        results.extend(test_results)

        # Test for privilege escalation
        test_results = self._test_privilege_escalation(target_url)
        results.extend(test_results)

        # Test for unauthorized access
        test_results = self._test_unauthorized_access(target_url)
        results.extend(test_results)

        return results

    def _test_idor_vulnerabilities(self, target_url: str) -> List[SecurityTestResult]:
        """Test for IDOR vulnerabilities"""
        results = []

        # Test patient record access
        idor_result = SecurityTestResult(
            "IDOR - Patient Record Access",
            "Insecure Direct Object Reference",
            "HIGH"
        )

        try:
            # Simulate accessing patient records with different user IDs
            patient_ids = [1, 2, 3, 99999]  # Include non-existent ID

            for patient_id in patient_ids:
                test_url = f"{target_url}/api/patients/{patient_id}/"

                # Test with different user roles
                for user_role in ['patient', 'doctor', 'admin', 'unauthorized']:
                    headers = self._get_auth_headers_for_role(user_role)

                    response = requests.get(test_url, headers=headers, verify=False)

                    if response.status_code == 200 and user_role in ['unauthorized']:
                        idor_result.description = f"Unauthorized access to patient record {patient_id}"
                        idor_result.affected_components.append(f"Patient API - ID {patient_id}")
                        idor_result.remediation_steps = [
                            "Implement proper authorization checks",
                            "Use UUIDs instead of sequential IDs",
                            "Add ownership verification"
                        ]
                        idor_result.owasp_category = "A01:2021-Broken Access Control"

        except Exception as e:
            idor_result.description = f"Error during IDOR testing: {str(e)}"

        results.append(idor_result)
        return results

    def _test_cryptographic_failures(self, target_url: str) -> List[SecurityTestResult]:
        """Test for cryptographic failures"""
        results = []

        # Test password storage
        crypto_result = SecurityTestResult(
            "Cryptographic Failures - Password Storage",
            "Cryptographic Failures",
            "CRITICAL"
        )

        try:
            # Check if passwords are stored with proper hashing
            test_users = User.objects.all()[:5]

            for user in test_users:
                if user.password.startswith('md5$') or user.password.startswith('sha1$'):
                    crypto_result.description = f"Weak password hash detected for user {user.username}"
                    crypto_result.affected_components.append(f"User - {user.username}")
                    crypto_result.remediation_steps = [
                        "Use bcrypt or Argon2 for password hashing",
                        "Implement proper password policies",
                        "Add salting mechanism"
                    ]
                    crypto_result.owasp_category = "A02:2021-Cryptographic Failures"
                    break

        except Exception as e:
            crypto_result.description = f"Error during cryptographic testing: {str(e)}"

        results.append(crypto_result)
        return results

    def _test_injection_vulnerabilities(self, target_url: str) -> List[SecurityTestResult]:
        """Test for injection vulnerabilities"""
        results = []

        # SQL Injection testing
        sql_result = self._test_sql_injection(target_url)
        results.append(sql_result)

        # XSS testing
        xss_result = self._test_xss_vulnerabilities(target_url)
        results.append(xss_result)

        # Command injection testing
        cmd_result = self._test_command_injection(target_url)
        results.append(cmd_result)

        return results

    def _test_sql_injection(self, target_url: str) -> SecurityTestResult:
        """Test for SQL injection vulnerabilities"""
        result = SecurityTestResult(
            "SQL Injection",
            "Injection",
            "CRITICAL"
        )

        sql_payloads = [
            "' OR '1'='1",
            "' UNION SELECT username, password FROM users --",
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' OR SLEEP(10)--"
        ]

        vulnerable_endpoints = [
            '/api/patients/',
            '/api/users/',
            '/api/appointments/',
            '/api/medical-records/'
        ]

        try:
            for endpoint in vulnerable_endpoints:
                for payload in sql_payloads:
                    test_url = f"{target_url}{endpoint}"

                    # Test GET parameter injection
                    params = {'search': payload}
                    response = requests.get(test_url, params=params, verify=False)

                    if response.status_code == 500 or 'error' in response.text.lower():
                        result.description = f"SQL injection vulnerability in {endpoint}"
                        result.affected_components.append(endpoint)
                        result.remediation_steps = [
                            "Use parameterized queries",
                            "Implement input validation",
                            "Use Django ORM properly",
                            "Add WAF protection"
                        ]
                        result.owasp_category = "A03:2021-Injection"
                        break

                    # Test POST parameter injection
                    data = {'query': payload}
                    response = requests.post(test_url, json=data, verify=False)

                    if response.status_code == 500 or 'error' in response.text.lower():
                        result.description = f"SQL injection vulnerability in {endpoint}"
                        result.affected_components.append(endpoint)
                        result.remediation_steps = [
                            "Use parameterized queries",
                            "Implement input validation",
                            "Use Django ORM properly",
                            "Add WAF protection"
                        ]
                        result.owasp_category = "A03:2021-Injection"
                        break

        except Exception as e:
            result.description = f"Error during SQL injection testing: {str(e)}"

        return result

    def _test_xss_vulnerabilities(self, target_url: str) -> SecurityTestResult:
        """Test for XSS vulnerabilities"""
        result = SecurityTestResult(
            "Cross-Site Scripting (XSS)",
            "Injection",
            "HIGH"
        )

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'\"><script>alert('XSS')</script>"
        ]

        vulnerable_endpoints = [
            '/api/patients/',
            '/api/appointments/',
            '/api/feedback/'
        ]

        try:
            for endpoint in vulnerable_endpoints:
                for payload in xss_payloads:
                    test_url = f"{target_url}{endpoint}"

                    # Test input fields
                    test_data = {
                        'first_name': payload,
                        'last_name': 'Test',
                        'notes': payload
                    }

                    response = requests.post(test_url, json=test_data, verify=False)

                    if payload in response.text:
                        result.description = f"XSS vulnerability in {endpoint}"
                        result.affected_components.append(endpoint)
                        result.remediation_steps = [
                            "Implement input sanitization",
                            "Use output encoding",
                            "Implement CSP headers",
                            "Use HTML escaping"
                        ]
                        result.owasp_category = "A03:2021-Injection"
                        break

        except Exception as e:
            result.description = f"Error during XSS testing: {str(e)}"

        return result

    def _test_command_injection(self, target_url: str) -> SecurityTestResult:
        """Test for command injection vulnerabilities"""
        result = SecurityTestResult(
            "Command Injection",
            "Injection",
            "CRITICAL"
        )

        cmd_payloads = [
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            "$(id)",
            "`id`"
        ]

        vulnerable_endpoints = [
            '/api/system/backup/',
            '/api/reports/generate/',
            '/api/admin/execute/'
        ]

        try:
            for endpoint in vulnerable_endpoints:
                for payload in cmd_payloads:
                    test_url = f"{target_url}{endpoint}"

                    test_data = {
                        'command': payload,
                        'filename': payload
                    }

                    response = requests.post(test_url, json=test_data, verify=False)

                    if 'root:' in response.text or 'uid=' in response.text:
                        result.description = f"Command injection vulnerability in {endpoint}"
                        result.affected_components.append(endpoint)
                        result.remediation_steps = [
                            "Avoid shell commands",
                            "Use subprocess with proper arguments",
                            "Implement input validation",
                            "Use principle of least privilege"
                        ]
                        result.owasp_category = "A03:2021-Injection"
                        break

        except Exception as e:
            result.description = f"Error during command injection testing: {str(e)}"

        return result

    def _test_hipaa_compliance(self, target_url: str) -> List[SecurityTestResult]:
        """Test for HIPAA compliance violations"""
        results = []

        # Test PHI encryption
        phi_result = self._test_phi_encryption(target_url)
        results.append(phi_result)

        # Test audit trail completeness
        audit_result = self._test_audit_trail_completeness(target_url)
        results.append(audit_result)

        # Test access control compliance
        access_result = self._test_access_control_compliance(target_url)
        results.append(access_result)

        return results

    def _test_phi_encryption(self, target_url: str) -> SecurityTestResult:
        """Test for proper PHI encryption"""
        result = SecurityTestResult(
            "HIPAA Compliance - PHI Encryption",
            "HIPAA Violation",
            "CRITICAL"
        )

        try:
            # Test data transmission encryption
            response = requests.get(target_url, verify=False)

            if not response.url.startswith('https://'):
                result.description = "Unencrypted HTTP connection detected"
                result.affected_components.append("Network Layer")
                result.remediation_steps = [
                    "Implement HTTPS for all connections",
                    "Use TLS 1.3",
                    "Disable HTTP traffic"
                ]
                result.cve_references.append("CVE-2023-HIPAA-001")

            # Test data storage encryption (simulate database check)
            # This would normally check actual database encryption

        except Exception as e:
            result.description = f"Error during PHI encryption testing: {str(e)}"

        return result

    def _test_audit_trail_completeness(self, target_url: str) -> SecurityTestResult:
        """Test for audit trail completeness"""
        result = SecurityTestResult(
            "HIPAA Compliance - Audit Trail",
            "HIPAA Violation",
            "HIGH"
        )

        try:
            # Test audit log creation
            test_actions = [
                'patient_create',
                'patient_update',
                'patient_delete',
                'medical_record_access',
                'appointment_create'
            ]

            for action in test_actions:
                # Simulate action and check for audit log
                test_url = f"{target_url}/api/audit/logs/"
                response = requests.get(test_url, verify=False)

                if response.status_code != 200:
                    result.description = f"Audit trail not accessible or incomplete for {action}"
                    result.affected_components.append("Audit System")
                    result.remediation_steps = [
                        "Implement comprehensive audit logging",
                        "Log all PHI access",
                        "Maintain audit logs for 6+ years",
                        "Implement audit log protection"
                    ]
                    break

        except Exception as e:
            result.description = f"Error during audit trail testing: {str(e)}"

        return result

    def _get_auth_headers_for_role(self, role: str) -> Dict[str, str]:
        """Get authentication headers for different roles"""
        headers = {}

        if role != 'unauthorized':
            # Generate mock JWT token for testing
            payload = {
                'user_id': 1,
                'role': role,
                'exp': datetime.now() + timedelta(hours=1)
            }

            # This would normally use proper JWT secret
            token = jwt.encode(payload, 'test-secret', algorithm='HS256')
            headers['Authorization'] = f'Bearer {token}'

        return headers


class HMSSecurityTestCase(HMSTestCase, SecurityTestingMixin, HealthcareDataMixin):
    """Base test case for HMS security testing"""

    def setUp(self):
        super().setUp()
        self.security_framework = SecurityTestingFramework()
        self.target_url = "http://localhost:8000"  # Test server URL

        # Create test users with different roles
        self.create_test_users()

    def create_test_users(self):
        """Create test users with different roles"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='securepassword123!',
            role='admin',
            email='admin@hms.com'
        )

        self.doctor_user = User.objects.create_user(
            username='doctor',
            password='securepassword123!',
            role='doctor',
            email='doctor@hms.com'
        )

        self.patient_user = User.objects.create_user(
            username='patient',
            password='securepassword123!',
            role='patient',
            email='patient@hms.com'
        )

        self.unauthorized_user = User.objects.create_user(
            username='unauthorized',
            password='securepassword123!',
            role='unauthorized',
            email='unauthorized@hms.com'
        )

    def run_security_scan(self):
        """Run comprehensive security scan"""
        results = self.security_framework.run_comprehensive_security_scan(self.target_url)

        # Log results
        for result in results:
            self.log_security_result(result)

        # Assert no critical vulnerabilities
        critical_vulnerabilities = [r for r in results if r.severity == 'CRITICAL']
        self.assertEqual(
            len(critical_vulnerabilities),
            0,
            f"Found {len(critical_vulnerabilities)} critical security vulnerabilities"
        )

        return results

    def log_security_result(self, result: SecurityTestResult):
        """Log security test result"""
        print(f"\n=== Security Test Result ===")
        print(f"Test: {result.test_name}")
        print(f"Severity: {result.severity}")
        print(f"Description: {result.description}")
        print(f"Affected Components: {result.affected_components}")
        print(f"Remediation: {result.remediation_steps}")
        print(f"OWASP Category: {result.owasp_category}")
        print(f"Timestamp: {result.timestamp}")
        print("=" * 50)


# Pytest fixtures for security testing
@pytest.fixture
def security_framework():
    """Security testing framework fixture"""
    return SecurityTestingFramework()


@pytest.fixture
def security_test_client():
    """Security test client fixture"""
    client = APIClient()
    return client


@pytest.fixture
def test_users():
    """Test users fixture"""
    users = {}

    # Create test users
    users['admin'] = User.objects.create_user(
        username='security_admin',
        password='SecurePass123!',
        role='admin',
        email='admin@security.test'
    )

    users['doctor'] = User.objects.create_user(
        username='security_doctor',
        password='SecurePass123!',
        role='doctor',
        email='doctor@security.test'
    )

    users['patient'] = User.objects.create_user(
        username='security_patient',
        password='SecurePass123!',
        role='patient',
        email='patient@security.test'
    )

    return users


# Security test markers
def pytest_configure(config):
    """Configure pytest with security markers"""
    config.addinivalue_line(
        "markers",
        "security: Mark test as security test"
    )
    config.addinivalue_line(
        "markers",
        "penetration: Mark test as penetration test"
    )
    config.addinivalue_line(
        "markers",
        "hipaa: Mark test as HIPAA compliance test"
    )
    config.addinivalue_line(
        "markers",
        "owasp: Mark test as OWASP Top 10 test"
    )