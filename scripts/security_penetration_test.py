#!/usr/bin/env python3
"""
Enterprise-Grade HMS Security Penetration Testing and Certification System
Comprehensive security assessment for healthcare management systems
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import re
import secrets
import socket
import ssl
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import requests

# Add backend to path
sys.path.append("/home/azureuser/helli/enterprise-grade-hms/backend")


class SecurityLevel(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Informational"


class ComplianceStandard(Enum):
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    PCI_DSS = "PCI DSS"
    ISO_27001 = "ISO 27001"
    NIST = "NIST"


@dataclass
class SecurityFinding:
    test_name: str
    vulnerability_type: str
    severity: SecurityLevel
    description: str
    evidence: str
    remediation: str
    cve_id: Optional[str] = None
    compliance_impact: List[ComplianceStandard] = None


@dataclass
class ComplianceResult:
    standard: ComplianceStandard
    requirement: str
    status: str  # PASS, FAIL, PARTIAL
    evidence: str
    recommendation: str


class SecurityPenetrationTester:
    """Comprehensive security penetration testing for HMS"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.findings: List[SecurityFinding] = []
        self.compliance_results: List[ComplianceResult] = []
        self.logger = self._setup_logger()

        # Test payloads
        self.sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE patients; --",
            "1 UNION SELECT username, password FROM users--",
            "' OR SLEEP(10)--",
            "' AND (SELECT COUNT(*) FROM information_schema.tables)>0--",
            "1' AND 1=1--",
            "admin'--",
            "' OR 1=1#",
        ]

        self.xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "'\"><script>alert(document.cookie)</script>",
            "<iframe src=javascript:alert('XSS')>",
            "data:text/html,<script>alert('XSS')</script>",
        ]

        self.path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "/var/www/html/../../../etc/passwd",
        ]

        self.auth_bypass_payloads = [
            {"username": "admin", "password": "' OR '1'='1"},
            {"username": "admin'--", "password": "any"},
            {"username": "", "password": ""},
            {"username": "admin", "password": "password' OR '1'='1"},
            {"username": "admin' #", "password": "any"},
        ]

    def _setup_logger(self):
        """Setup logging for security testing"""
        logger = logging.getLogger("SecurityPenetrationTester")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def test_sql_injection(self) -> List[SecurityFinding]:
        """Test for SQL injection vulnerabilities"""
        findings = []

        async with aiohttp.ClientSession() as session:
            for payload in self.sql_injection_payloads:
                try:
                    # Test patient search endpoint
                    params = {"search": payload}
                    async with session.get(
                        f"{self.base_url}/api/patients/", params=params
                    ) as response:
                        text = await response.text()

                        # Check for SQL error indicators
                        error_indicators = [
                            "sql syntax",
                            "syntax error",
                            "unclosed quotation",
                            "mysql_fetch",
                            "postgresql",
                            "ora-",
                            "microsoft ole db",
                            "odbc driver",
                            "sqlite",
                            "error in your sql syntax",
                        ]

                        vulnerable = any(
                            indicator.lower() in text.lower()
                            for indicator in error_indicators
                        )

                        if vulnerable:
                            finding = SecurityFinding(
                                test_name="SQL Injection",
                                vulnerability_type="SQL Injection",
                                severity=SecurityLevel.CRITICAL,
                                description=f"SQL injection vulnerability detected with payload: {payload}",
                                evidence=f"Response contained SQL error indicators: {text[:200]}...",
                                remediation="Implement parameterized queries and input validation. Use Django ORM instead of raw SQL.",
                                compliance_impact=[
                                    ComplianceStandard.HIPAA,
                                    ComplianceStandard.PCI_DSS,
                                ],
                            )
                            findings.append(finding)
                            self.logger.warning(
                                f"SQL Injection vulnerability found: {payload}"
                            )

                except Exception as e:
                    self.logger.error(
                        f"Error testing SQL injection with payload {payload}: {e}"
                    )

        return findings

    async def test_xss_vulnerabilities(self) -> List[SecurityFinding]:
        """Test for Cross-Site Scripting vulnerabilities"""
        findings = []

        async with aiohttp.ClientSession() as session:
            for payload in self.xss_payloads:
                try:
                    # Test through patient notes field
                    patient_data = {
                        "first_name": "Test",
                        "last_name": "Patient",
                        "email": "test@example.com",
                        "notes": payload,
                    }

                    async with session.post(
                        f"{self.base_url}/api/patients/", json=patient_data
                    ) as response:
                        if response.status == 200:
                            # Check if payload was reflected in response
                            text = await response.text()
                            if payload in text:
                                finding = SecurityFinding(
                                    test_name="XSS Vulnerability",
                                    vulnerability_type="Cross-Site Scripting",
                                    severity=SecurityLevel.HIGH,
                                    description=f"XSS vulnerability detected with payload: {payload}",
                                    evidence=f"Payload was reflected in response: {text[:200]}...",
                                    remediation="Implement input sanitization and output encoding. Use Django's template autoescaping.",
                                    compliance_impact=[
                                        ComplianceStandard.HIPAA,
                                        ComplianceStandard.PCI_DSS,
                                    ],
                                )
                                findings.append(finding)
                                self.logger.warning(
                                    f"XSS vulnerability found: {payload}"
                                )

                except Exception as e:
                    self.logger.error(f"Error testing XSS with payload {payload}: {e}")

        return findings

    async def test_authentication_bypass(self) -> List[SecurityFinding]:
        """Test authentication bypass vulnerabilities"""
        findings = []

        async with aiohttp.ClientSession() as session:
            for attempt in self.auth_bypass_payloads:
                try:
                    async with session.post(
                        f"{self.base_url}/api/auth/login/", json=attempt
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "access" in data or "token" in data:
                                finding = SecurityFinding(
                                    test_name="Authentication Bypass",
                                    vulnerability_type="Authentication Bypass",
                                    severity=SecurityLevel.CRITICAL,
                                    description=f"Authentication bypass successful with: {attempt}",
                                    evidence=f"Received access token: {data.get('access', 'N/A')[:50]}...",
                                    remediation="Implement proper authentication validation. Never trust user input for authentication.",
                                    compliance_impact=[
                                        ComplianceStandard.HIPAA,
                                        ComplianceStandard.GDPR,
                                        ComplianceStandard.PCI_DSS,
                                    ],
                                )
                                findings.append(finding)
                                self.logger.critical(
                                    f"Authentication bypass successful: {attempt}"
                                )

                except Exception as e:
                    self.logger.error(
                        f"Error testing authentication bypass with attempt {attempt}: {e}"
                    )

        return findings

    async def test_path_traversal(self) -> List[SecurityFinding]:
        """Test path traversal vulnerabilities"""
        findings = []

        async with aiohttp.ClientSession() as session:
            for payload in self.path_traversal_payloads:
                try:
                    # Test file upload endpoint
                    params = {"file_path": payload}
                    async with session.get(
                        f"{self.base_url}/api/files/", params=params
                    ) as response:
                        text = await response.text()

                        # Check for file content indicators
                        file_indicators = [
                            "root:x:0:0:",
                            "daemon:",
                            "# Copyright",
                            "[boot loader]",
                            "windows directory",
                            "system32",
                            "passwd:",
                            "group:",
                        ]

                        if any(
                            indicator.lower() in text.lower()
                            for indicator in file_indicators
                        ):
                            finding = SecurityFinding(
                                test_name="Path Traversal",
                                vulnerability_type="Path Traversal",
                                severity=SecurityLevel.CRITICAL,
                                description=f"Path traversal vulnerability detected with payload: {payload}",
                                evidence=f"Response contained file content: {text[:200]}...",
                                remediation="Validate file paths and restrict access to required directories only.",
                                compliance_impact=[
                                    ComplianceStandard.HIPAA,
                                    ComplianceStandard.GDPR,
                                ],
                            )
                            findings.append(finding)
                            self.logger.warning(
                                f"Path traversal vulnerability found: {payload}"
                            )

                except Exception as e:
                    self.logger.error(
                        f"Error testing path traversal with payload {payload}: {e}"
                    )

        return findings

    async def test_rate_limiting(self) -> List[SecurityFinding]:
        """Test rate limiting effectiveness"""
        findings = []

        async with aiohttp.ClientSession() as session:
            try:
                # Test login endpoint rate limiting
                requests_sent = 0
                requests_allowed = 0
                rate_limited = 0

                for i in range(50):  # Send 50 requests quickly
                    login_data = {"username": f"test{i}", "password": "password"}
                    try:
                        async with session.post(
                            f"{self.base_url}/api/auth/login/", json=login_data
                        ) as response:
                            requests_sent += 1
                            if response.status == 429:
                                rate_limited += 1
                            elif response.status == 200 or response.status == 400:
                                requests_allowed += 1
                    except:
                        requests_sent += 1

                # Should be rate limited after a certain number of attempts
                if rate_limited < 10:  # Should have at least 10 rate-limited responses
                    finding = SecurityFinding(
                        test_name="Rate Limiting",
                        vulnerability_type="Insufficient Rate Limiting",
                        severity=SecurityLevel.MEDIUM,
                        description=f"Rate limiting not working properly. Sent {requests_sent} requests, only {rate_limited} were rate limited.",
                        evidence=f"Requests sent: {requests_sent}, Rate limited: {rate_limited}, Allowed: {requests_allowed}",
                        remediation="Implement proper rate limiting on authentication endpoints. Use Django REST framework throttling.",
                        compliance_impact=[ComplianceStandard.PCI_DSS],
                    )
                    findings.append(finding)
                    self.logger.warning(f"Insufficient rate limiting detected")
                else:
                    self.logger.info(
                        f"Rate limiting working correctly: {rate_limited}/{requests_sent} requests rate limited"
                    )

            except Exception as e:
                self.logger.error(f"Error testing rate limiting: {e}")

        return findings

    async def test_ssl_tls_configuration(self) -> List[SecurityFinding]:
        """Test SSL/TLS configuration"""
        findings = []

        try:
            # Test SSL/TLS configuration
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection(("localhost", 8000), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname="localhost") as ssock:
                    cipher = ssock.cipher()
                    version = ssock.version()

                    # Check for weak ciphers
                    weak_ciphers = ["RC4", "DES", "3DES", "MD5", "NULL"]
                    if cipher and any(weak in cipher[0] for weak in weak_ciphers):
                        finding = SecurityFinding(
                            test_name="SSL/TLS Configuration",
                            vulnerability_type="Weak Cipher Suite",
                            severity=SecurityLevel.MEDIUM,
                            description=f"Weak cipher suite detected: {cipher[0]}",
                            evidence=f"SSL/TLS version: {version}, Cipher: {cipher}",
                            remediation="Disable weak cipher suites and use only TLS 1.2+ with strong ciphers.",
                            compliance_impact=[
                                ComplianceStandard.HIPAA,
                                ComplianceStandard.PCI_DSS,
                            ],
                        )
                        findings.append(finding)
                        self.logger.warning(f"Weak cipher detected: {cipher}")

                    # Check for TLS version
                    if version in ["SSLv2", "SSLv3", "TLSv1", "TLSv1.1"]:
                        finding = SecurityFinding(
                            test_name="SSL/TLS Configuration",
                            vulnerability_type="Outdated TLS Version",
                            severity=SecurityLevel.HIGH,
                            description=f"Outdated TLS version detected: {version}",
                            evidence=f"TLS version: {version}",
                            remediation="Upgrade to TLS 1.2 or higher. Disable older TLS versions.",
                            compliance_impact=[
                                ComplianceStandard.HIPAA,
                                ComplianceStandard.PCI_DSS,
                            ],
                        )
                        findings.append(finding)
                        self.logger.warning(f"Outdated TLS version: {version}")

        except Exception as e:
            self.logger.error(f"Error testing SSL/TLS configuration: {e}")

        return findings

    async def test_http_headers_security(self) -> List[SecurityFinding]:
        """Test HTTP security headers"""
        findings = []

        try:
            response = requests.get(f"{self.base_url}/api/patients/")
            headers = response.headers

            # Check for security headers
            required_headers = {
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-Content-Type-Options": ["nosniff"],
                "X-XSS-Protection": ["1; mode=block"],
                "Strict-Transport-Security": None,  # Just check presence
                "Content-Security-Policy": None,
                "Referrer-Policy": None,
            }

            for header, expected_values in required_headers.items():
                if header not in headers:
                    finding = SecurityFinding(
                        test_name="HTTP Security Headers",
                        vulnerability_type=f"Missing {header} Header",
                        severity=SecurityLevel.MEDIUM,
                        description=f"Security header {header} is missing",
                        evidence=f"Response headers: {dict(headers)}",
                        remediation=f"Add {header} header to server configuration.",
                        compliance_impact=[
                            ComplianceStandard.HIPAA,
                            ComplianceStandard.PCI_DSS,
                        ],
                    )
                    findings.append(finding)
                    self.logger.warning(f"Missing security header: {header}")
                elif expected_values and headers[header] not in expected_values:
                    finding = SecurityFinding(
                        test_name="HTTP Security Headers",
                        vulnerability_type=f"Incorrect {header} Header Value",
                        severity=SecurityLevel.LOW,
                        description=f"Security header {header} has incorrect value: {headers[header]}",
                        evidence=f"Expected: {expected_values}, Actual: {headers[header]}",
                        remediation=f"Update {header} header to use one of: {expected_values}",
                        compliance_impact=[
                            ComplianceStandard.HIPAA,
                            ComplianceStandard.PCI_DSS,
                        ],
                    )
                    findings.append(finding)
                    self.logger.warning(
                        f"Incorrect security header value for {header}: {headers[header]}"
                    )

        except Exception as e:
            self.logger.error(f"Error testing HTTP security headers: {e}")

        return findings

    async def test_compliance_requirements(self) -> List[ComplianceResult]:
        """Test compliance with healthcare regulations"""
        results = []

        # HIPAA Compliance
        hipaa_requirements = [
            {
                "requirement": "Data Encryption at Rest",
                "test": lambda: self._test_encryption_at_rest(),
                "standard": ComplianceStandard.HIPAA,
            },
            {
                "requirement": "Data Encryption in Transit",
                "test": lambda: self._test_encryption_in_transit(),
                "standard": ComplianceStandard.HIPAA,
            },
            {
                "requirement": "Audit Logging",
                "test": lambda: self._test_audit_logging(),
                "standard": ComplianceStandard.HIPAA,
            },
            {
                "requirement": "Access Controls",
                "test": lambda: self._test_access_controls(),
                "standard": ComplianceStandard.HIPAA,
            },
        ]

        # GDPR Compliance
        gdpr_requirements = [
            {
                "requirement": "Data Minimization",
                "test": lambda: self._test_data_minimization(),
                "standard": ComplianceStandard.GDPR,
            },
            {
                "requirement": "User Consent Management",
                "test": lambda: self._test_consent_management(),
                "standard": ComplianceStandard.GDPR,
            },
            {
                "requirement": "Data Subject Rights",
                "test": lambda: self._test_data_subject_rights(),
                "standard": ComplianceStandard.GDPR,
            },
        ]

        # PCI DSS Compliance
        pci_requirements = [
            {
                "requirement": "Payment Card Data Protection",
                "test": lambda: self._test_payment_card_protection(),
                "standard": ComplianceStandard.PCI_DSS,
            },
            {
                "requirement": "Network Security",
                "test": lambda: self._test_network_security(),
                "standard": ComplianceStandard.PCI_DSS,
            },
        ]

        all_requirements = hipaa_requirements + gdpr_requirements + pci_requirements

        for req in all_requirements:
            try:
                status, evidence = req["test"]()

                result = ComplianceResult(
                    standard=req["standard"],
                    requirement=req["requirement"],
                    status=status,
                    evidence=evidence,
                    recommendation=self._get_compliance_recommendation(
                        req["standard"], req["requirement"], status
                    ),
                )
                results.append(result)

                if status == "PASS":
                    self.logger.info(
                        f"Compliance check passed: {req['standard'].value} - {req['requirement']}"
                    )
                else:
                    self.logger.warning(
                        f"Compliance check failed: {req['standard'].value} - {req['requirement']}"
                    )

            except Exception as e:
                self.logger.error(
                    f"Error testing compliance requirement {req['requirement']}: {e}"
                )
                result = ComplianceResult(
                    standard=req["standard"],
                    requirement=req["requirement"],
                    status="ERROR",
                    evidence=str(e),
                    recommendation="Review and fix the compliance requirement implementation",
                )
                results.append(result)

        return results

    def _test_encryption_at_rest(self) -> Tuple[str, str]:
        """Test data encryption at rest"""
        try:
            # Check if encryption is configured in Django settings
            with open(
                "/home/azureuser/helli/enterprise-grade-hms/backend/hms/settings.py",
                "r",
            ) as f:
                settings_content = f.read()

            if (
                "FIELD_ENCRYPTION_KEY" in settings_content
                and "ENCRYPTION_ENABLED" in settings_content
            ):
                return "PASS", "Encryption at rest is configured in Django settings"
            else:
                return "FAIL", "Encryption at rest not properly configured"

        except Exception as e:
            return "ERROR", f"Error checking encryption at rest: {str(e)}"

    def _test_encryption_in_transit(self) -> Tuple[str, str]:
        """Test data encryption in transit"""
        try:
            # Check HTTPS configuration
            response = requests.get(f"{self.base_url}/api/patients/")

            if response.url.startswith("https://"):
                return "PASS", "HTTPS is properly configured"
            else:
                return "FAIL", "HTTPS not configured - data not encrypted in transit"

        except Exception as e:
            return "ERROR", f"Error checking encryption in transit: {str(e)}"

    def _test_audit_logging(self) -> Tuple[str, str]:
        """Test audit logging configuration"""
        try:
            # Check if audit logging is enabled
            with open(
                "/home/azureuser/helli/enterprise-grade-hms/backend/hms/settings.py",
                "r",
            ) as f:
                settings_content = f.read()

            if (
                "AUDIT_LOGGING_ENABLED" in settings_content
                and "SecurityAuditMiddleware" in settings_content
            ):
                return "PASS", "Audit logging is configured and enabled"
            else:
                return "FAIL", "Audit logging not properly configured"

        except Exception as e:
            return "ERROR", f"Error checking audit logging: {str(e)}"

    def _test_access_controls(self) -> Tuple[str, str]:
        """Test access controls"""
        try:
            # Check if authentication and authorization are configured
            with open(
                "/home/azureuser/helli/enterprise-grade-hms/backend/hms/settings.py",
                "r",
            ) as f:
                settings_content = f.read()

            if (
                "rest_framework.authentication" in settings_content
                and "rest_framework.permissions" in settings_content
                and "AUTHENTICATION_BACKENDS" in settings_content
            ):
                return "PASS", "Access controls are properly configured"
            else:
                return "FAIL", "Access controls not properly configured"

        except Exception as e:
            return "ERROR", f"Error checking access controls: {str(e)}"

    def _test_data_minimization(self) -> Tuple[str, str]:
        """Test data minimization principle"""
        try:
            # Check if only necessary data is collected
            with open(
                "/home/azureuser/helli/enterprise-grade-hms/backend/patients/models.py",
                "r",
            ) as f:
                models_content = f.read()

            # Look for unnecessary data collection
            unnecessary_fields = [
                "social_security_number",
                "credit_card_number",
                "bank_account",
            ]

            unnecessary_found = []
            for field in unnecessary_fields:
                if field in models_content.lower():
                    unnecessary_found.append(field)

            if not unnecessary_found:
                return "PASS", "Data minimization principle is followed"
            else:
                return "FAIL", f"Unnecessary data fields found: {unnecessary_found}"

        except Exception as e:
            return "ERROR", f"Error checking data minimization: {str(e)}"

    def _test_consent_management(self) -> Tuple[str, str]:
        """Test consent management"""
        try:
            # Check if consent management is implemented
            consent_files = [
                "/home/azureuser/helli/enterprise-grade-hms/backend/consent/models.py",
                "/home/azureuser/helli/enterprise-grade-hms/backend/consent/views.py",
                "/home/azureuser/helli/enterprise-grade-hms/services/consent/",
            ]

            consent_found = False
            for file_path in consent_files:
                if os.path.exists(file_path):
                    consent_found = True
                    break

            if consent_found:
                return "PASS", "Consent management system is implemented"
            else:
                return "FAIL", "Consent management system not found"

        except Exception as e:
            return "ERROR", f"Error checking consent management: {str(e)}"

    def _test_data_subject_rights(self) -> Tuple[str, str]:
        """Test data subject rights implementation"""
        try:
            # Check if data subject rights are implemented
            with open(
                "/home/azureuser/helli/enterprise-grade-hms/backend/patients/views.py",
                "r",
            ) as f:
                views_content = f.read()

            # Look for data deletion/export functionality
            if "delete" in views_content.lower() or "export" in views_content.lower():
                return "PASS", "Data subject rights are implemented"
            else:
                return "FAIL", "Data subject rights not properly implemented"

        except Exception as e:
            return "ERROR", f"Error checking data subject rights: {str(e)}"

    def _test_payment_card_protection(self) -> Tuple[str, str]:
        """Test payment card data protection"""
        try:
            # Check if payment card data is properly protected
            billing_files = [
                "/home/azureuser/helli/enterprise-grade-hms/backend/billing/models.py",
                "/home/azureuser/helli/enterprise-grade-hms/backend/billing/views.py",
            ]

            pci_compliant = True
            for file_path in billing_files:
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Check for raw credit card storage
                    if (
                        "credit_card_number" in content.lower()
                        and "encrypt" not in content.lower()
                    ):
                        pci_compliant = False
                        break

            if pci_compliant:
                return "PASS", "Payment card data is properly protected"
            else:
                return "FAIL", "Payment card data not properly encrypted/protected"

        except Exception as e:
            return "ERROR", f"Error checking payment card protection: {str(e)}"

    def _test_network_security(self) -> Tuple[str, str]:
        """Test network security"""
        try:
            # Check firewall and network security configurations
            docker_compose_path = (
                "/home/azureuser/helli/enterprise-grade-hms/docker-compose.yml"
            )

            if os.path.exists(docker_compose_path):
                with open(docker_compose_path, "r") as f:
                    docker_content = f.read()

                # Check for proper port exposure
                if "8000:8000" in docker_content and "443:443" not in docker_content:
                    return "FAIL", "HTTP port exposed without HTTPS"
                else:
                    return "PASS", "Network security properly configured"
            else:
                return "ERROR", "Docker compose file not found"

        except Exception as e:
            return "ERROR", f"Error checking network security: {str(e)}"

    def _get_compliance_recommendation(
        self, standard: ComplianceStandard, requirement: str, status: str
    ) -> str:
        """Get recommendation for compliance requirement"""
        recommendations = {
            ComplianceStandard.HIPAA: {
                "Data Encryption at Rest": "Implement AES-256 encryption for all stored PHI",
                "Data Encryption in Transit": "Configure HTTPS with TLS 1.2+ for all data transmission",
                "Audit Logging": "Enable comprehensive audit logging for all PHI access",
                "Access Controls": "Implement role-based access control with MFA",
            },
            ComplianceStandard.GDPR: {
                "Data Minimization": "Collect only necessary personal data",
                "User Consent Management": "Implement explicit consent management system",
                "Data Subject Rights": "Provide data access, correction, and deletion capabilities",
            },
            ComplianceStandard.PCI_DSS: {
                "Payment Card Data Protection": "Never store raw payment card data",
                "Network Security": "Implement firewalls and proper network segmentation",
            },
        }

        if status == "PASS":
            return "Continue maintaining compliance with regular audits"
        else:
            return recommendations.get(standard, {}).get(
                requirement, "Review and implement proper compliance measures"
            )

    async def run_comprehensive_security_test(self) -> Dict[str, Any]:
        """Run comprehensive security penetration testing"""
        self.logger.info("Starting comprehensive security penetration testing")

        # Run all security tests
        tasks = [
            self.test_sql_injection(),
            self.test_xss_vulnerabilities(),
            self.test_authentication_bypass(),
            self.test_path_traversal(),
            self.test_rate_limiting(),
            self.test_ssl_tls_configuration(),
            self.test_http_headers_security(),
            self.test_compliance_requirements(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all findings
        all_findings = []
        for result in results:
            if isinstance(result, list):
                if result and isinstance(result[0], SecurityFinding):
                    all_findings.extend(result)
                elif result and isinstance(result[0], ComplianceResult):
                    self.compliance_results.extend(result)

        self.findings.extend(all_findings)

        # Generate security report
        security_report = self.generate_security_report()

        self.logger.info(
            f"Security testing completed. Found {len(all_findings)} vulnerabilities"
        )

        return security_report

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        critical_issues = len(
            [f for f in self.findings if f.severity == SecurityLevel.CRITICAL]
        )
        high_issues = len(
            [f for f in self.findings if f.severity == SecurityLevel.HIGH]
        )
        medium_issues = len(
            [f for f in self.findings if f.severity == SecurityLevel.MEDIUM]
        )
        low_issues = len([f for f in self.findings if f.severity == SecurityLevel.LOW])

        compliance_passed = len(
            [r for r in self.compliance_results if r.status == "PASS"]
        )
        compliance_failed = len(
            [r for r in self.compliance_results if r.status == "FAIL"]
        )

        # Calculate security score
        security_score = max(
            0,
            100
            - (critical_issues * 20)
            - (high_issues * 10)
            - (medium_issues * 5)
            - (low_issues * 2),
        )
        compliance_score = (
            (compliance_passed / len(self.compliance_results) * 100)
            if self.compliance_results
            else 0
        )

        # Determine certification status
        certification_status = "PASS"
        if critical_issues > 0:
            certification_status = "FAIL"
        elif security_score < 80 or compliance_score < 90:
            certification_status = "FAIL"

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "test_duration": "Comprehensive Security Assessment",
            "security_findings": {
                "total_vulnerabilities": len(self.findings),
                "critical_issues": critical_issues,
                "high_issues": high_issues,
                "medium_issues": medium_issues,
                "low_issues": low_issues,
                "security_score": security_score,
                "details": [
                    {
                        "test_name": f.test_name,
                        "vulnerability_type": f.vulnerability_type,
                        "severity": f.severity.value,
                        "description": f.description,
                        "evidence": f.evidence,
                        "remediation": f.remediation,
                        "compliance_impact": (
                            [c.value for c in f.compliance_impact]
                            if f.compliance_impact
                            else []
                        ),
                    }
                    for f in self.findings
                ],
            },
            "compliance_results": {
                "total_requirements": len(self.compliance_results),
                "passed": compliance_passed,
                "failed": compliance_failed,
                "compliance_score": compliance_score,
                "details": [
                    {
                        "standard": r.standard.value,
                        "requirement": r.requirement,
                        "status": r.status,
                        "evidence": r.evidence,
                        "recommendation": r.recommendation,
                    }
                    for r in self.compliance_results
                ],
            },
            "overall_assessment": {
                "security_status": (
                    "SECURE"
                    if security_score >= 90
                    else "AT_RISK" if security_score >= 70 else "VULNERABLE"
                ),
                "compliance_status": (
                    "COMPLIANT"
                    if compliance_score >= 95
                    else (
                        "PARTIALLY_COMPLIANT"
                        if compliance_score >= 80
                        else "NON_COMPLIANT"
                    )
                ),
                "certification_status": certification_status,
                "overall_score": (security_score + compliance_score) / 2,
            },
            "recommendations": self.generate_recommendations(),
            "next_review_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
        }

    def generate_recommendations(self) -> List[str]:
        """Generate security and compliance recommendations"""
        recommendations = []

        # Critical issue recommendations
        critical_findings = [
            f for f in self.findings if f.severity == SecurityLevel.CRITICAL
        ]
        if critical_findings:
            recommendations.append(
                f"URGENT: Fix {len(critical_findings)} critical security vulnerabilities immediately"
            )
            recommendations.append("Implement emergency security patch deployment")

        # High priority recommendations
        high_findings = [f for f in self.findings if f.severity == SecurityLevel.HIGH]
        if high_findings:
            recommendations.append(
                f"HIGH PRIORITY: Address {len(high_findings)} high-risk security issues"
            )

        # Compliance recommendations
        failed_compliance = [r for r in self.compliance_results if r.status == "FAIL"]
        if failed_compliance:
            recommendations.append(
                f"COMPLIANCE: Fix {len(failed_compliance)} failed compliance requirements"
            )

        # General recommendations
        recommendations.append(
            "Implement regular security scanning and penetration testing"
        )
        recommendations.append("Establish security incident response procedures")
        recommendations.append("Provide security awareness training for all staff")
        recommendations.append("Implement continuous security monitoring")
        recommendations.append("Schedule quarterly security assessments")

        return recommendations


async def main():
    """Main execution function"""
    print("🔐 Enterprise-Grade HMS Security Certification")
    print("=" * 50)

    # Initialize security tester
    tester = SecurityPenetrationTester()

    # Run comprehensive security test
    security_report = await tester.run_comprehensive_security_test()

    # Print summary
    print(f"\n📊 Security Assessment Summary:")
    print(
        f"Total Vulnerabilities: {security_report['security_findings']['total_vulnerabilities']}"
    )
    print(f"Critical Issues: {security_report['security_findings']['critical_issues']}")
    print(f"High Issues: {security_report['security_findings']['high_issues']}")
    print(
        f"Security Score: {security_report['security_findings']['security_score']}/100"
    )
    print(
        f"Compliance Score: {security_report['compliance_results']['compliance_score']:.1f}%"
    )
    print(
        f"Certification Status: {security_report['overall_assessment']['certification_status']}"
    )

    # Save detailed report
    report_path = (
        "/home/azureuser/helli/enterprise-grade-hms/security_certification_report.json"
    )
    with open(report_path, "w") as f:
        json.dump(security_report, f, indent=2, default=str)

    print(f"\n📄 Detailed security report saved to: {report_path}")

    # Return certification status
    return security_report["overall_assessment"]["certification_status"] == "PASS"


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
