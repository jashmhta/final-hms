"""
Comprehensive Compliance Testing Suite for HMS System

This module implements comprehensive compliance tests for healthcare regulations:
- HIPAA compliance validation
- GDPR compliance validation
- PCI DSS compliance validation
- HITECH Act compliance
- NIST Cybersecurity Framework
- Healthcare data privacy testing
- Audit trail completeness testing
- Risk assessment validation
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
import requests
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import Client, TestCase
from django.urls import reverse

from ..conftest import HealthcareDataMixin, PerformanceTestingMixin

# Import compliance framework
from .compliance_framework import (
    ComplianceCategory,
    ComplianceFramework,
    ComplianceLevel,
    ComplianceTestResult,
    HealthcareComplianceFramework,
    HealthcareComplianceTestCase,
)

User = get_user_model()


class ComplianceComprehensiveTestSuite(HealthcareComplianceTestCase):
    """Comprehensive compliance testing suite for HMS system"""

    @pytest.mark.compliance
    @pytest.mark.hipaa
    def test_hipaa_privacy_rule_comprehensive(self):
        """Test HIPAA Privacy Rule compliance"""
        print("\n=== Testing HIPAA Privacy Rule ===")

        # Test 1: PHI identification and protection
        self.test_phi_identification()

        # Test 2: Use and disclosure limitations
        self.test_phi_use_disclosure()

        # Test 3: Patient rights implementation
        self.test_patient_rights()

        # Test 4: Authorization requirements
        self.test_authorization_requirements()

        # Test 5: Minimum necessary standard
        self.test_minimum_necessary_standard()

        print("✓ HIPAA Privacy Rule tests completed")

    def test_phi_identification(self):
        """Test PHI identification and protection"""
        print("Testing PHI identification...")

        # Define PHI fields
        phi_fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "ssn",
            "medical_record_number",
            "date_of_birth",
            "address",
            "insurance_id",
            "diagnosis",
            "treatment",
            "medication",
        ]

        # Check if PHI fields are properly identified and protected
        phi_protection_issues = 0

        # Test database encryption for PHI fields
        with connection.cursor() as cursor:
            for field in phi_fields:
                try:
                    cursor.execute(
                        f"""
                        SELECT table_name, column_name
                        FROM information_schema.columns
                        WHERE column_name LIKE '%{field}%'
                    """
                    )
                    results = cursor.fetchall()

                    for table_name, column_name in results:
                        # Check if column is encrypted
                        cursor.execute(
                            f"""
                            SELECT {column_name}
                            FROM {table_name}
                            LIMIT 1
                        """
                        )
                        sample_data = cursor.fetchone()

                        if sample_data and sample_data[0]:
                            stored_value = str(sample_data[0])

                            # Check for plaintext storage of sensitive PHI
                            if field in [
                                "ssn",
                                "medical_record_number",
                                "insurance_id",
                            ]:
                                if not self.is_phi_encrypted(stored_value):
                                    phi_protection_issues += 1
                                    print(
                                        f"⚠️  PHI field {column_name} in {table_name} may be stored in plaintext"
                                    )

                except Exception as e:
                    print(f"Error checking PHI field {field}: {e}")

        self.assertEqual(
            phi_protection_issues,
            0,
            f"Found {phi_protection_issues} PHI protection issues",
        )

    def is_phi_encrypted(self, value):
        """Check if PHI value appears to be encrypted"""
        if not value:
            return True

        value_str = str(value)

        # Check for encryption indicators
        encrypted_indicators = [
            len(value_str) > 100,  # Long encrypted strings
            value_str.startswith("g3v"),  # Django encrypted field format
            value_str.startswith("$2b$"),  # bcrypt
            value_str.startswith("pbkdf2_sha256$"),  # PBKDF2
            any(
                c
                not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._@ :/-"
                for c in value_str
            ),  # Non-standard characters
        ]

        return any(encrypted_indicators)

    def test_phi_use_disclosure(self):
        """Test PHI use and disclosure limitations"""
        print("Testing PHI use and disclosure limitations...")

        # Test role-based PHI access
        test_users = {
            "admin": self.create_test_user("admin", "admin@test.com", "admin"),
            "doctor": self.create_test_user("doctor", "doctor@test.com", "doctor"),
            "patient": self.create_test_user("patient", "patient@test.com", "patient"),
            "receptionist": self.create_test_user(
                "receptionist", "receptionist@test.com", "receptionist"
            ),
        }

        phi_endpoints = [
            "/api/patients/",
            "/api/medical-records/",
            "/api/appointments/",
            "/api/billing/",
            "/api/pharmacy/",
        ]

        disclosure_violations = 0

        for endpoint in phi_endpoints:
            for role, user in test_users.items():
                client = APIClient()
                client.force_authenticate(user=user)

                try:
                    response = client.get(endpoint)

                    # Check response for PHI exposure
                    if response.status_code == status.HTTP_200_OK:
                        response_data = response.json()

                        if isinstance(response_data, dict):
                            phi_in_response = self.contains_phi(response_data)
                            if phi_in_response and role in ["receptionist"]:
                                disclosure_violations += 1
                                print(
                                    f"⚠️  PHI disclosure violation: {role} accessed PHI via {endpoint}"
                                )

                        elif isinstance(response_data, list):
                            for item in response_data[:5]:  # Check first 5 items
                                if self.contains_phi(item):
                                    if role in ["receptionist"]:
                                        disclosure_violations += 1
                                        print(
                                            f"⚠️  PHI disclosure violation: {role} accessed PHI via {endpoint}"
                                        )

                except Exception as e:
                    print(f"Error testing PHI disclosure for {role} on {endpoint}: {e}")

        self.assertEqual(
            disclosure_violations,
            0,
            f"Found {disclosure_violations} PHI disclosure violations",
        )

    def contains_phi(self, data):
        """Check if data contains PHI"""
        phi_indicators = [
            "ssn",
            "social_security",
            "medical_record",
            "diagnosis",
            "treatment",
            "medication",
            "insurance",
            "date_of_birth",
        ]

        if isinstance(data, dict):
            for key, value in data.items():
                if any(indicator in key.lower() for indicator in phi_indicators):
                    return True
                if isinstance(value, (dict, list)):
                    if self.contains_phi(value):
                        return True

        elif isinstance(data, list):
            for item in data:
                if self.contains_phi(item):
                    return True

        return False

    def test_patient_rights(self):
        """Test patient rights implementation"""
        print("Testing patient rights...")

        # Test right to access
        self.test_right_to_access()

        # Test right to amend
        self.test_right_to_amend()

        # Test right to accounting of disclosures
        self.test_right_to_accounting()

        # Test right to restrict disclosure
        self.test_right_to_restrict()

    def test_right_to_access(self):
        """Test patient right to access medical records"""
        print("Testing patient right to access...")

        # Create test patient
        patient_data = HealthcareDataMixin.generate_anonymized_patient_data()
        patient = self.create_test_patient(patient_data)

        # Create patient user
        patient_user = User.objects.create_user(
            username="patient_access",
            password="SecurePass123!",
            email="patient_access@test.com",
            role="patient",
        )

        # Link patient to user (this would normally be done through user profile)
        client = APIClient()
        client.force_authenticate(user=patient_user)

        # Test access to own records
        try:
            response = client.get(f"/api/patients/{patient.id}/")

            if response.status_code == status.HTTP_200_OK:
                print("✓ Patient can access their own records")
            else:
                print("⚠️  Patient cannot access their own records")

        except Exception as e:
            print(f"Error testing patient access: {e}")

    def test_authorization_requirements(self):
        """Test authorization requirements for PHI disclosure"""
        print("Testing authorization requirements...")

        # Test that PHI disclosure requires proper authorization
        auth_required_scenarios = [
            ("medical_record_access", "/api/medical-records/"),
            ("patient_info_share", "/api/patients/share/"),
            ("billing_info_access", "/api/billing/"),
        ]

        authorization_issues = 0

        for scenario, endpoint in auth_required_scenarios:
            client = APIClient()  # Unauthenticated

            try:
                response = client.post(
                    endpoint, {"patient_id": 1, "disclosure_reason": "treatment"}
                )

                if response.status_code != status.HTTP_401_UNAUTHORIZED:
                    authorization_issues += 1
                    print(f"⚠️  Authorization not required for {scenario}")

            except Exception as e:
                print(f"Error testing authorization for {scenario}: {e}")

        self.assertEqual(
            authorization_issues,
            0,
            f"Found {authorization_issues} authorization issues",
        )

    @pytest.mark.compliance
    @pytest.mark.gdpr
    def test_gdpr_comprehensive_compliance(self):
        """Test GDPR comprehensive compliance"""
        print("\n=== Testing GDPR Compliance ===")

        # Test 1: Lawfulness, fairness, and transparency
        self.test_gdpr_lawfulness()

        # Test 2: Purpose limitation
        self.test_gdpr_purpose_limitation()

        # Test 3: Data minimization
        self.test_gdpr_data_minimization()

        # Test 4: Accuracy
        self.test_gdpr_accuracy()

        # Test 5: Storage limitation
        self.test_gdpr_storage_limitation()

        # Test 6: Integrity and confidentiality
        self.test_gdpr_integrity_confidentiality()

        # Test 7: Accountability
        self.test_gdpr_accountability()

        print("✓ GDPR Compliance tests completed")

    def test_gdpr_lawfulness(self):
        """Test GDPR lawfulness, fairness, and transparency"""
        print("Testing GDPR lawfulness...")

        # Test consent mechanisms
        consent_issues = 0

        # Check if consent is properly implemented
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE column_name LIKE '%consent%'
                OR column_name LIKE '%permission%'
                OR column_name LIKE '%agreement%'
            """
            )
            consent_columns = cursor.fetchall()

            if not consent_columns:
                consent_issues += 1
                print("⚠️  No consent management mechanisms found")

        # Test privacy policy
        try:
            response = requests.get(
                "http://localhost:8000/privacy-policy/", verify=False
            )
            if response.status_code != 200:
                consent_issues += 1
                print("⚠️  Privacy policy not accessible")
        except:
            consent_issues += 1
            print("⚠️  Unable to access privacy policy")

        self.assertEqual(consent_issues, 0, f"Found {consent_issues} lawfulness issues")

    def test_gdpr_data_minimization(self):
        """Test GDPR data minimization principle"""
        print("Testing GDPR data minimization...")

        # Check if only necessary data is collected
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name, COUNT(*) as column_count
                FROM information_schema.columns
                WHERE table_schema = 'public'
                GROUP BY table_name
                ORDER BY column_count DESC
            """
            )
            table_columns = cursor.fetchall()

        data_minimization_issues = 0

        for table_name, column_count in table_columns:
            if column_count > 50:  # Arbitrary threshold
                data_minimization_issues += 1
                print(
                    f"⚠️  Table {table_name} has {column_count} columns (potential data minimization issue)"
                )

        # Check for unnecessary data collection
        unnecessary_fields = [
            "middle_name",
            "maiden_name",
            "mother_maiden_name",
            "fathers_name",
            "mothers_name",
            "place_of_birth",
        ]

        for field in unnecessary_fields:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM information_schema.columns
                    WHERE column_name LIKE '%{field}%'
                """
                )
                count = cursor.fetchone()[0]

                if count > 0:
                    data_minimization_issues += 1
                    print(f"⚠️  Unnecessary field {field} found in {count} table(s)")

        print(f"Data minimization issues: {data_minimization_issues}")

    def test_gdpr_accuracy(self):
        """Test GDPR accuracy principle"""
        print("Testing GDPR accuracy...")

        # Test data validation mechanisms
        accuracy_issues = 0

        # Check for validation constraints
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.table_constraints
                WHERE constraint_type = 'CHECK'
            """
            )
            check_constraints = cursor.fetchone()[0]

            if check_constraints < 10:  # Should have some validation
                accuracy_issues += 1
                print(f"⚠️  Insufficient validation constraints: {check_constraints}")

        # Test data format validation
        validation_fields = ["email", "phone", "zip_code", "date_of_birth"]

        for field in validation_fields:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM information_schema.columns
                    WHERE column_name LIKE '%{field}%'
                """
                )
                count = cursor.fetchone()[0]

                if count > 0:
                    # Check if validation exists
                    cursor.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM information_schema.check_constraints
                        WHERE constraint_name LIKE '%{field}%'
                    """
                    )
                    validation_count = cursor.fetchone()[0]

                    if validation_count == 0:
                        accuracy_issues += 1
                        print(f"⚠️  No validation for {field} field")

        print(f"Accuracy issues: {accuracy_issues}")

    @pytest.mark.compliance
    @pytest.mark.pci_dss
    def test_pci_dss_comprehensive_compliance(self):
        """Test PCI DSS comprehensive compliance"""
        print("\n=== Testing PCI DSS Compliance ===")

        # Test 1: Build and maintain a secure network
        self.test_pci_dss_secure_network()

        # Test 2: Protect cardholder data
        self.test_pci_dss_cardholder_protection()

        # Test 3: Maintain a vulnerability management program
        self.test_pci_dss_vulnerability_management()

        # Test 4: Implement strong access control measures
        self.test_pci_dss_access_control()

        # Test 5: Regularly monitor and test networks
        self.test_pci_dss_monitoring()

        # Test 6: Maintain an information security policy
        self.test_pci_dss_security_policy()

        print("✓ PCI DSS Compliance tests completed")

    def test_pci_dss_secure_network(self):
        """Test PCI DSS secure network requirements"""
        print("Testing PCI DSS secure network...")

        # Test firewall configuration
        firewall_issues = 0

        # Check for open ports (simplified test)
        try:
            response = requests.get("http://localhost:8000/", verify=False)
            if response.status_code == 200:
                print("✓ Basic network connectivity confirmed")
        except:
            firewall_issues += 1
            print("⚠️  Network connectivity issues")

        # Test security headers
        security_headers = [
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Content-Security-Policy",
        ]

        try:
            response = requests.get("http://localhost:8000/", verify=False)
            missing_headers = []

            for header in security_headers:
                if header not in response.headers:
                    missing_headers.append(header)

            if missing_headers:
                firewall_issues += len(missing_headers)
                print(f"⚠️  Missing security headers: {missing_headers}")

        except:
            firewall_issues += 1
            print("⚠️  Unable to verify security headers")

        self.assertEqual(
            firewall_issues, 0, f"Found {firewall_issues} network security issues"
        )

    def test_pci_dss_cardholder_protection(self):
        """Test PCI DSS cardholder data protection"""
        print("Testing PCI DSS cardholder protection...")

        # Check for cardholder data storage
        cardholder_data_fields = [
            "card_number",
            "credit_card",
            "cc_number",
            "payment_card",
            "cvv",
            "cvc",
            "cvv2",
            "expiry",
            "expiration",
            "cardholder_name",
        ]

        cardholder_issues = 0

        with connection.cursor() as cursor:
            for field in cardholder_data_fields:
                cursor.execute(
                    f"""
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE column_name LIKE '%{field}%'
                """
                )
                results = cursor.fetchall()

                for table_name, column_name in results:
                    cardholder_issues += 1
                    print(
                        f"⚠️  Cardholder data field {column_name} found in {table_name}"
                    )

        self.assertEqual(
            cardholder_issues,
            0,
            f"Found {cardholder_issues} cardholder data storage issues",
        )

    @pytest.mark.compliance
    @pytest.mark.hitech
    def test_hitech_act_compliance(self):
        """Test HITECH Act compliance"""
        print("\n=== Testing HITECH Act Compliance ===")

        # Test 1: Electronic health records privacy
        self.test_hitech_ehr_privacy()

        # Test 2: Breach notification
        self.test_hitech_breach_notification()

        # Test 3: Meaningful use criteria
        self.test_hitech_meaningful_use()

        # Test 4: Business associate agreements
        self.test_hitech_business_associates()

        print("✓ HITECH Act Compliance tests completed")

    def test_hitech_ehr_privacy(self):
        """Test HITECH EHR privacy requirements"""
        print("Testing HITECH EHR privacy...")

        # Test electronic record privacy
        privacy_issues = 0

        # Check audit trail for EHR access
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_name LIKE '%audit%'
                OR table_name LIKE '%log%'
                OR table_name LIKE '%access%'
            """
            )
            audit_tables = cursor.fetchone()[0]

            if audit_tables < 3:
                privacy_issues += 1
                print(f"⚠️  Insufficient audit tables: {audit_tables}")

        # Test access logging
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE column_name LIKE '%access_time%'
                OR column_name LIKE '%login_time%'
                OR column_name LIKE '%action_time%'
            """
            )
            time_columns = cursor.fetchone()[0]

            if time_columns < 3:
                privacy_issues += 1
                print(f"⚠️  Insufficient access logging: {time_columns}")

        self.assertEqual(
            privacy_issues, 0, f"Found {privacy_issues} EHR privacy issues"
        )

    def test_hitech_breach_notification(self):
        """Test HITECH breach notification requirements"""
        print("Testing HITECH breach notification...")

        # Test breach detection mechanisms
        breach_issues = 0

        # Check for security monitoring
        monitoring_components = [
            "security_logs",
            "audit_trails",
            "incident_reports",
            "breach_detection",
            "anomaly_detection",
        ]

        monitoring_found = 0
        with connection.cursor() as cursor:
            for component in monitoring_components:
                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_name LIKE '%{component}%'
                """
                )
                count = cursor.fetchone()[0]

                if count > 0:
                    monitoring_found += 1

        if monitoring_found < 2:
            breach_issues += 1
            print(
                f"⚠️  Insufficient security monitoring: {monitoring_found}/{len(monitoring_components)}"
            )

        # Test notification procedures
        try:
            response = requests.get(
                "http://localhost:8000/api/security/incidents/", verify=False
            )
            if response.status_code != 200:
                breach_issues += 1
                print("⚠️  Incident reporting endpoint not accessible")
        except:
            breach_issues += 1
            print("⚠️  Unable to test incident reporting")

        self.assertEqual(
            breach_issues, 0, f"Found {breach_issues} breach notification issues"
        )

    @pytest.mark.compliance
    @pytest.mark.nist
    def test_nist_cybersecurity_framework(self):
        """Test NIST Cybersecurity Framework compliance"""
        print("\n=== Testing NIST Cybersecurity Framework ===")

        # Test 1: Identify
        self.test_nist_identify()

        # Test 2: Protect
        self.test_nist_protect()

        # Test 3: Detect
        self.test_nist_detect()

        # Test 4: Respond
        self.test_nist_respond()

        # Test 5: Recover
        self.test_nist_recover()

        print("✓ NIST Cybersecurity Framework tests completed")

    def test_nist_identify(self):
        """Test NIST Identify function"""
        print("Testing NIST Identify...")

        # Test asset management
        identify_issues = 0

        # Check for asset inventory
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_name LIKE '%asset%'
                OR table_name LIKE '%inventory%'
                OR table_name LIKE '%device%'
            """
            )
            asset_tables = cursor.fetchone()[0]

            if asset_tables == 0:
                identify_issues += 1
                print("⚠️  No asset inventory tables found")

        # Test risk assessment
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_name LIKE '%risk%'
                OR table_name LIKE '%assessment%'
            """
            )
            risk_tables = cursor.fetchone()[0]

            if risk_tables == 0:
                identify_issues += 1
                print("⚠️  No risk assessment tables found")

        print(f"Identify issues: {identify_issues}")

    @pytest.mark.compliance
    @pytest.mark.iso_27001
    def test_iso_27001_compliance(self):
        """Test ISO 27001 compliance"""
        print("\n=== Testing ISO 27001 Compliance ===")

        # Test information security management system
        self.test_iso_isms()

        # Test risk assessment and treatment
        self.test_iso_risk_treatment()

        # Test security controls
        self.test_iso_security_controls()

        print("✓ ISO 27001 Compliance tests completed")

    def test_iso_isms(self):
        """Test ISO 27001 Information Security Management System"""
        print("Testing ISO 27001 ISMS...")

        # Test security policy documentation
        isms_issues = 0

        # Check for security policy endpoints
        policy_endpoints = [
            "/api/security/policy/",
            "/api/compliance/policy/",
            "/security-policy",
        ]

        policy_accessible = 0
        for endpoint in policy_endpoints:
            try:
                response = requests.get(
                    f"http://localhost:8000{endpoint}", verify=False
                )
                if response.status_code == 200:
                    policy_accessible += 1
            except:
                pass

        if policy_accessible == 0:
            isms_issues += 1
            print("⚠️  No security policy accessible")

        # Test security roles and responsibilities
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_name LIKE '%role%'
                OR table_name LIKE '%permission%'
            """
            )
            role_tables = cursor.fetchone()[0]

            if role_tables < 2:
                isms_issues += 1
                print(f"⚠️  Insufficient role/permission tables: {role_tables}")

        print(f"ISMS issues: {isms_issues}")

    @pytest.mark.compliance
    @pytest.mark.performance
    def test_compliance_performance_impact(self):
        """Test performance impact of compliance measures"""
        print("\n=== Testing Compliance Performance Impact ===")

        # Test authentication performance
        self.test_compliance_authentication_performance()

        # Test encryption performance
        self.test_compliance_encryption_performance()

        # Test audit logging performance
        self.test_compliance_audit_performance()

        print("✓ Compliance Performance Impact tests completed")

    def test_compliance_authentication_performance(self):
        """Test authentication performance with compliance measures"""
        print("Testing compliance authentication performance...")

        import time

        # Test login performance
        login_times = []

        for i in range(5):
            start_time = time.time()

            client = Client()
            result = client.login(username="admin", password="securepassword123!")

            end_time = time.time()
            login_times.append(end_time - start_time)

        avg_login_time = sum(login_times) / len(login_times)

        print(f"Average compliance login time: {avg_login_time:.3f} seconds")

        # Login should be fast (< 3 seconds with compliance measures)
        self.assertLess(
            avg_login_time,
            3.0,
            f"Compliance authentication too slow: {avg_login_time:.3f}s",
        )

    def test_compliance_audit_performance(self):
        """Test audit logging performance"""
        print("Testing compliance audit performance...")

        import time

        # Test audit logging overhead
        test_actions = [
            "user_login",
            "patient_access",
            "medical_record_view",
            "appointment_create",
        ]

        audit_overhead_times = []

        for action in test_actions:
            start_time = time.time()

            # Simulate action with audit logging
            client = self.get_authenticated_client("admin")

            if action == "patient_access":
                response = client.get("/api/patients/")
            elif action == "medical_record_view":
                response = client.get("/api/medical-records/")
            elif action == "appointment_create":
                response = client.post(
                    "/api/appointments/",
                    {
                        "patient_id": 1,
                        "appointment_date": "2024-01-01T10:00:00Z",
                        "appointment_type": "GENERAL",
                    },
                )

            end_time = time.time()
            overhead_time = end_time - start_time
            audit_overhead_times.append(overhead_time)

        avg_audit_overhead = sum(audit_overhead_times) / len(audit_overhead_times)

        print(f"Average audit overhead: {avg_audit_overhead:.3f} seconds")

        # Audit overhead should be minimal (< 1 second)
        self.assertLess(
            avg_audit_overhead,
            1.0,
            f"Audit overhead too high: {avg_audit_overhead:.3f}s",
        )

    def generate_compliance_report(self):
        """Generate comprehensive compliance report"""
        print("\n=== Generating Comprehensive Compliance Report ===")

        # Run compliance assessment
        results = self.compliance_framework.run_comprehensive_compliance_assessment(
            self.target_url
        )

        # Generate detailed report
        report = self.compliance_framework.generate_compliance_report()

        # Add executive summary
        report["executive_summary"]["total_frameworks_tested"] = len(
            set(result.framework.value for result in results)
        )
        report["executive_summary"]["high_priority_actions"] = []

        # Identify high-priority actions
        critical_gaps = []
        for result in results:
            for gap in result.gaps:
                if gap["severity"] == "CRITICAL":
                    critical_gaps.append(
                        {
                            "framework": result.framework.value,
                            "requirement": result.requirement,
                            "gap": gap["gap"],
                            "recommendation": gap.get(
                                "recommendation", "Address critical compliance gap"
                            ),
                        }
                    )

        report["executive_summary"]["critical_gaps"] = critical_gaps
        report["executive_summary"]["immediate_actions_required"] = (
            len(critical_gaps) > 0
        )

        # Save detailed report
        with open("/tmp/hms_comprehensive_compliance_report.json", "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\n=== Compliance Summary ===")
        print(f"Overall Compliance Score: {report['overall_compliance_score']:.1f}%")
        print(
            f"Frameworks Tested: {report['executive_summary']['total_frameworks_tested']}"
        )
        print(f"Critical Gaps: {len(critical_gaps)}")
        print(
            f"Immediate Actions Required: {'Yes' if len(critical_gaps) > 0 else 'No'}"
        )

        if len(critical_gaps) > 0:
            print("\n⚠️  CRITICAL COMPLIANCE GAPS:")
            for gap in critical_gaps[:5]:  # Show first 5
                print(f"  - {gap['framework']}: {gap['gap']}")

        return report

    def get_authenticated_client(self, role):
        """Get authenticated client for specific role"""
        client = APIClient()

        try:
            if role == "admin":
                user = User.objects.get(username="admin")
            elif role == "doctor":
                user = User.objects.get(username="doctor")
            elif role == "patient":
                user = User.objects.get(username="patient")
            else:
                return client

            client.force_authenticate(user=user)
            return client

        except User.DoesNotExist:
            print(f"User {role} not found")
            return client

    def create_test_user(self, username, email, role):
        """Create test user"""
        return User.objects.create_user(
            username=username, password="SecurePass123!", email=email, role=role
        )

    def create_test_patient(self, patient_data):
        """Create test patient"""
        from backend.patients.models import Patient

        return Patient.objects.create(**patient_data)


# Pytest fixtures
@pytest.fixture
def compliance_test_suite():
    """Compliance test suite fixture"""
    return ComplianceComprehensiveTestSuite()


@pytest.fixture
def compliance_test_results():
    """Compliance test results fixture"""
    return []


@pytest.fixture
def compliance_frameworks():
    """Compliance frameworks fixture"""
    return list(ComplianceFramework)


@pytest.fixture
def compliance_categories():
    """Compliance categories fixture"""
    return list(ComplianceCategory)


if __name__ == "__main__":
    # Run comprehensive compliance testing
    test_suite = ComplianceComprehensiveTestSuite()
    test_suite.setUp()

    # Generate compliance report
    report = test_suite.generate_compliance_report()

    print("\n=== Compliance Testing Complete ===")
    print(f"Overall Score: {report['overall_compliance_score']:.1f}%")
    print(f"Critical Issues: {len(report['executive_summary']['critical_gaps'])}")

    if report["overall_compliance_score"] >= 90:
        print("🎉 Excellent compliance rating!")
    elif report["overall_compliance_score"] >= 80:
        print("✅ Good compliance rating")
    elif report["overall_compliance_score"] >= 70:
        print("⚠️  Compliance needs improvement")
    else:
        print("🚨 Compliance requires immediate attention")
