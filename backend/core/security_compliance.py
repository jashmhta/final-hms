"""
Comprehensive Security and Compliance Framework
HIPAA, GDPR, and healthcare regulation compliance with advanced security measures
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

User = get_user_model()


class ComplianceStandard(Enum):
    """Compliance standards supported"""

    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HITRUST = "hitrust"


class SecurityLevel(Enum):
    """Security levels for data classification"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PHI = "phi"  # Protected Health Information


class RiskLevel(Enum):
    """Risk levels for security assessment"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event structure"""

    id: str
    event_type: str
    severity: RiskLevel
    user_id: Optional[int]
    ip_address: str
    user_agent: str
    description: str
    timestamp: datetime
    metadata: Dict = None
    investigation_status: str = "open"
    resolved_at: Optional[datetime] = None


@dataclass
class ComplianceReport:
    """Compliance report structure"""

    standard: ComplianceStandard
    score: float
    findings: List[Dict]
    recommendations: List[Dict]
    last_assessment: datetime
    next_assessment: datetime


class DataEncryptionManager:
    """Manage data encryption for PHI and sensitive data"""

    def __init__(self):
        self.encryption_keys = {}
        self.key_rotation_schedule = {}
        self._initialize_encryption()

    def _initialize_encryption(self):
        """Initialize encryption keys and setup"""
        # Generate or load encryption keys
        if hasattr(settings, "FERNET_KEYS"):
            for key in settings.FERNET_KEYS:
                if isinstance(key, str):
                    key = key.encode()
                self.encryption_keys[f"fernet_{len(self.encryption_keys)}"] = Fernet(
                    key
                )

        # Generate new key if none exists
        if not self.encryption_keys:
            new_key = Fernet.generate_key()
            self.encryption_keys["fernet_0"] = Fernet(new_key)

        # Setup key rotation schedule
        self.key_rotation_schedule = {
            "data_at_rest": 90,  # Rotate every 90 days
            "data_in_transit": 180,  # Rotate every 180 days
            "backup_keys": 365,  # Rotate every year
        }

    def encrypt_data(self, data: Any, key_id: str = "fernet_0") -> str:
        """Encrypt data using Fernet encryption"""
        try:
            if key_id not in self.encryption_keys:
                raise ValueError(f"Encryption key {key_id} not found")

            # Serialize data to JSON
            serialized = json.dumps(data, default=str)
            encrypted = self.encryption_keys[key_id].encrypt(serialized.encode())
            return encrypted.decode()
        except Exception as e:
            logging.error(f"Data encryption failed: {e}")
            raise

    def decrypt_data(self, encrypted_data: str, key_id: str = "fernet_0") -> Any:
        """Decrypt data using Fernet encryption"""
        try:
            if key_id not in self.encryption_keys:
                raise ValueError(f"Encryption key {key_id} not found")

            decrypted = self.encryption_keys[key_id].decrypt(encrypted_data.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logging.error(f"Data decryption failed: {e}")
            raise

    def rotate_encryption_key(self, key_id: str):
        """Rotate encryption key"""
        try:
            if key_id not in self.encryption_keys:
                raise ValueError(f"Encryption key {key_id} not found")

            # Generate new key
            new_key = Fernet.generate_key()
            new_fernet = Fernet(new_key)

            # Replace old key
            old_key = self.encryption_keys[key_id]
            self.encryption_keys[key_id] = new_fernet

            logging.info(f"Encryption key {key_id} rotated successfully")
            return True
        except Exception as e:
            logging.error(f"Key rotation failed for {key_id}: {e}")
            return False


class AccessControlManager:
    """Advanced access control with RBAC and ABAC"""

    def __init__(self):
        self.role_permissions = {}
        self.resource_policies = {}
        self.access_logs = deque(maxlen=10000)
        self._setup_default_permissions()

    def _setup_default_permissions(self):
        """Setup default role permissions"""
        self.role_permissions = {
            "SUPER_ADMIN": [
                "users:*",
                "patients:*",
                "appointments:*",
                "billing:*",
                "ehr:*",
                "pharmacy:*",
                "lab:*",
                "hr:*",
                "facilities:*",
                "admin:*",
                "reports:*",
                "settings:*",
                "security:*",
            ],
            "HOSPITAL_ADMIN": [
                "users:read",
                "patients:*",
                "appointments:*",
                "billing:*",
                "ehr:read",
                "pharmacy:read",
                "lab:read",
                "hr:*",
                "facilities:*",
                "admin:*",
                "reports:*",
            ],
            "DOCTOR": [
                "patients:read",
                "patients:write",
                "appointments:*",
                "ehr:*",
                "pharmacy:read",
                "lab:read",
                "reports:read",
            ],
            "NURSE": [
                "patients:read",
                "patients:write",
                "ehr:read",
                "appointments:read",
                "pharmacy:read",
                "lab:read",
            ],
            "PHARMACIST": ["pharmacy:*", "patients:read", "ehr:read"],
            "LAB_TECHNICIAN": ["lab:*", "patients:read", "ehr:read"],
            "BILLING_CLERK": ["billing:*", "patients:read", "appointments:read"],
            "RECEPTIONIST": ["patients:read", "patients:write", "appointments:*"],
        }

    def check_permission(
        self, user: User, resource: str, action: str, context: Dict = None
    ) -> Tuple[bool, str]:
        """Check if user has permission to access resource"""
        try:
            # Get user's role
            if not hasattr(user, "role"):
                return False, "User role not defined"

            # Check role-based permissions
            required_permission = f"{resource}:{action}"
            user_permissions = self.role_permissions.get(user.role, [])

            # Wildcard permission check
            if f"{resource}:*" in user_permissions or "*:*" in user_permissions:
                pass  # Permission granted
            elif required_permission not in user_permissions:
                return False, f"Insufficient permissions for {required_permission}"

            # Context-based access control
            context_check = self._check_context_restrictions(
                user, resource, action, context
            )
            if not context_check[0]:
                return context_check

            # Time-based restrictions
            time_check = self._check_time_restrictions(user, resource, action)
            if not time_check[0]:
                return time_check

            # Log access
            self._log_access(user, resource, action, True)

            return True, "Access granted"

        except Exception as e:
            logging.error(f"Permission check error: {e}")
            return False, "Permission check failed"

    def _check_context_restrictions(
        self, user: User, resource: str, action: str, context: Dict
    ) -> Tuple[bool, str]:
        """Check context-based access restrictions"""
        if not context:
            return True, "No context restrictions"

        # Emergency access override
        if context.get("emergency_access", False) and user.role in ["DOCTOR", "NURSE"]:
            return True, "Emergency access granted"

        # Patient relationship check
        if resource.startswith("patient") and context.get("patient_id"):
            if not self._check_patient_relationship(user, context["patient_id"]):
                return False, "No relationship with patient"

        return True, "Context check passed"

    def _check_time_restrictions(
        self, user: User, resource: str, action: str
    ) -> Tuple[bool, str]:
        """Check time-based access restrictions"""
        current_hour = timezone.now().hour

        # Restrict sensitive operations to business hours
        sensitive_resources = ["billing", "hr", "admin", "settings"]
        if any(res in resource for res in sensitive_resources):
            if action in ["write", "delete", "update"] and not (
                9 <= current_hour <= 17
            ):
                return False, "Sensitive operations restricted to business hours"

        return True, "Time restrictions passed"

    def _check_patient_relationship(self, user: User, patient_id: int) -> bool:
        """Check if user has legitimate relationship with patient"""
        # This would check database for patient assignments
        # For now, return True for clinical staff
        return user.role in ["DOCTOR", "NURSE", "SUPER_ADMIN", "HOSPITAL_ADMIN"]

    def _log_access(self, user: User, resource: str, action: str, granted: bool):
        """Log access attempt"""
        access_log = {
            "user_id": user.id,
            "user_role": user.role,
            "resource": resource,
            "action": action,
            "granted": granted,
            "timestamp": timezone.now(),
        }
        self.access_logs.append(access_log)

    def add_custom_permission(self, role: str, permission: str):
        """Add custom permission to role"""
        if role not in self.role_permissions:
            self.role_permissions[role] = []
        if permission not in self.role_permissions[role]:
            self.role_permissions[role].append(permission)


class SecurityAuditManager:
    """Security audit and compliance logging"""

    def __init__(self):
        self.audit_logs = deque(maxlen=50000)
        self.compliance_reports = {}
        self.audit_triggers = {}
        self._setup_audit_triggers()

    def _setup_audit_triggers(self):
        """Setup audit triggers for sensitive operations"""
        self.audit_triggers = {
            "user_authentication": {
                "severity": RiskLevel.HIGH,
                "description": "User authentication attempt",
            },
            "data_access": {
                "severity": RiskLevel.MEDIUM,
                "description": "Data access attempt",
            },
            "data_modification": {
                "severity": RiskLevel.HIGH,
                "description": "Data modification attempt",
            },
            "admin_action": {
                "severity": RiskLevel.HIGH,
                "description": "Administrative action",
            },
            "security_configuration": {
                "severity": RiskLevel.CRITICAL,
                "description": "Security configuration change",
            },
            "failed_login": {
                "severity": RiskLevel.MEDIUM,
                "description": "Failed login attempt",
            },
        }

    def log_security_event(
        self, event_type: str, user: User = None, request=None, metadata: Dict = None
    ):
        """Log security event"""
        try:
            event_id = f"sec_{int(time.time())}_{secrets.token_hex(4)}"
            trigger = self.audit_triggers.get(
                event_type,
                {
                    "severity": RiskLevel.LOW,
                    "description": f"Security event: {event_type}",
                },
            )

            security_event = SecurityEvent(
                id=event_id,
                event_type=event_type,
                severity=trigger["severity"],
                user_id=user.id if user else None,
                ip_address=self._get_client_ip(request) if request else "unknown",
                user_agent=self._get_user_agent(request) if request else "unknown",
                description=trigger["description"],
                timestamp=timezone.now(),
                metadata=metadata or {},
            )

            self.audit_logs.append(security_event)

            # Check for automated investigation
            if trigger["severity"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                asyncio.create_task(self._investigate_event(security_event))

            # Store in persistent storage
            self._store_audit_log(security_event)

        except Exception as e:
            logging.error(f"Failed to log security event: {e}")

    def _get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip

    def _get_user_agent(self, request) -> str:
        """Get user agent from request"""
        return request.META.get("HTTP_USER_AGENT", "unknown")

    async def _investigate_event(self, event: SecurityEvent):
        """Automatically investigate security events"""
        try:
            # Basic investigation logic
            investigation_results = {
                "event_id": event.id,
                "investigation_type": "automated",
                "findings": [],
                "recommendations": [],
                "risk_score": self._calculate_risk_score(event),
            }

            # Check for patterns
            recent_events = [
                e
                for e in self.audit_logs
                if e.timestamp > timezone.now() - timedelta(hours=1)
            ]

            # Check for repeated failed logins
            if event.event_type == "failed_login":
                failed_logins = [
                    e
                    for e in recent_events
                    if e.event_type == "failed_login"
                    and e.ip_address == event.ip_address
                ]
                if len(failed_logins) > 5:
                    investigation_results["findings"].append(
                        "Multiple failed login attempts detected"
                    )
                    investigation_results["recommendations"].append(
                        "Consider blocking IP address or enabling MFA"
                    )

            # Update investigation status
            event.metadata["investigation"] = investigation_results

        except Exception as e:
            logging.error(f"Automated investigation failed: {e}")

    def _calculate_risk_score(self, event: SecurityEvent) -> float:
        """Calculate risk score for security event"""
        base_scores = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 3,
            RiskLevel.HIGH: 7,
            RiskLevel.CRITICAL: 10,
        }

        score = base_scores.get(event.severity, 1)

        # Adjust based on event type
        if event.event_type == "failed_login":
            score += 2
        elif event.event_type == "admin_action":
            score += 3
        elif event.event_type == "security_configuration":
            score += 5

        return min(score, 10)

    def _store_audit_log(self, event: SecurityEvent):
        """Store audit log in persistent storage"""
        # This would store in database or secure log storage
        # For now, we'll just keep in memory
        pass

    def generate_compliance_report(
        self, standard: ComplianceStandard
    ) -> ComplianceReport:
        """Generate compliance report"""
        try:
            # Analyze audit logs for compliance
            relevant_events = [
                event
                for event in self.audit_logs
                if event.timestamp > timezone.now() - timedelta(days=30)
            ]

            # Calculate compliance score
            total_events = len(relevant_events)
            critical_events = len(
                [e for e in relevant_events if e.severity == RiskLevel.CRITICAL]
            )
            high_events = len(
                [e for e in relevant_events if e.severity == RiskLevel.HIGH]
            )

            # Simple scoring algorithm
            if total_events == 0:
                score = 100.0
            else:
                score = max(
                    0,
                    100 - (critical_events * 10 + high_events * 5) / total_events * 100,
                )

            # Generate findings and recommendations
            findings = []
            recommendations = []

            if critical_events > 0:
                findings.append(
                    {
                        "type": "critical",
                        "description": f"Found {critical_events} critical security events",
                    }
                )
                recommendations.append(
                    {
                        "priority": "high",
                        "action": "Review and address critical security events",
                    }
                )

            if high_events > 5:
                findings.append(
                    {
                        "type": "high",
                        "description": f"Found {high_events} high-severity security events",
                    }
                )
                recommendations.append(
                    {
                        "priority": "medium",
                        "action": "Implement additional security controls",
                    }
                )

            report = ComplianceReport(
                standard=standard,
                score=score,
                findings=findings,
                recommendations=recommendations,
                last_assessment=timezone.now(),
                next_assessment=timezone.now() + timedelta(days=30),
            )

            self.compliance_reports[standard.value] = report
            return report

        except Exception as e:
            logging.error(f"Failed to generate compliance report: {e}")
            return None


class DataPrivacyManager:
    """Data privacy and consent management"""

    def __init__(self):
        self.consent_records = {}
        self.data_retention_policies = {}
        self.privacy_settings = {}
        self._setup_retention_policies()

    def _setup_retention_policies(self):
        """Setup data retention policies"""
        self.data_retention_policies = {
            "patient_medical_records": {"retention_years": 25, "archival": True},
            "billing_records": {"retention_years": 7, "archival": True},
            "appointment_records": {"retention_years": 7, "archival": False},
            "user_activity_logs": {"retention_years": 2, "archival": False},
            "system_logs": {"retention_days": 90, "archival": False},
            "backup_data": {"retention_days": 30, "archival": False},
        }

    def record_consent(
        self,
        patient_id: int,
        consent_type: str,
        granted: bool,
        expiration_date: datetime = None,
    ):
        """Record patient consent"""
        try:
            consent_id = f"consent_{patient_id}_{int(time.time())}"
            consent_record = {
                "id": consent_id,
                "patient_id": patient_id,
                "consent_type": consent_type,
                "granted": granted,
                "granted_at": timezone.now(),
                "expires_at": expiration_date,
                "ip_address": None,  # Would be captured from request
                "user_agent": None,  # Would be captured from request
            }

            self.consent_records[consent_id] = consent_record
            logging.info(f"Consent recorded: {consent_type} for patient {patient_id}")

        except Exception as e:
            logging.error(f"Failed to record consent: {e}")

    def check_consent(self, patient_id: int, consent_type: str) -> bool:
        """Check if patient has granted consent"""
        try:
            # Find active consent for this patient and type
            active_consents = [
                consent
                for consent in self.consent_records.values()
                if (
                    consent["patient_id"] == patient_id
                    and consent["consent_type"] == consent_type
                    and consent["granted"]
                    and (
                        consent["expires_at"] is None
                        or consent["expires_at"] > timezone.now()
                    )
                )
            ]

            return len(active_consents) > 0

        except Exception as e:
            logging.error(f"Failed to check consent: {e}")
            return False

    def anonymize_data(self, data: Dict, fields_to_anonymize: List[str]) -> Dict:
        """Anonymize sensitive data fields"""
        try:
            anonymized_data = data.copy()

            for field in fields_to_anonymize:
                if field in anonymized_data:
                    if field in ["name", "first_name", "last_name"]:
                        anonymized_data[field] = "[REDACTED]"
                    elif field == "email":
                        anonymized_data[field] = "[EMAIL_REDACTED]"
                    elif field == "phone":
                        anonymized_data[field] = "[PHONE_REDACTED]"
                    elif field in ["address", "street_address"]:
                        anonymized_data[field] = "[ADDRESS_REDACTED]"
                    else:
                        anonymized_data[field] = "[REDACTED]"

            return anonymized_data

        except Exception as e:
            logging.error(f"Failed to anonymize data: {e}")
            return data

    def apply_retention_policy(self, data_type: str, data_date: datetime) -> bool:
        """Check if data should be retained based on retention policy"""
        try:
            if data_type not in self.data_retention_policies:
                return True  # Default to retain if no policy

            policy = self.data_retention_policies[data_type]
            retention_period = policy["retention_years"] * 365  # Convert to days

            cutoff_date = timezone.now() - timedelta(days=retention_period)
            return data_date > cutoff_date

        except Exception as e:
            logging.error(f"Failed to apply retention policy: {e}")
            return True


class VulnerabilityManager:
    """Vulnerability management and scanning"""

    def __init__(self):
        self.vulnerabilities = []
        self.scan_results = {}
        self.remediation_plans = {}

    async def run_security_scan(self) -> Dict:
        """Run comprehensive security scan"""
        try:
            scan_results = {
                "timestamp": timezone.now(),
                "vulnerabilities": [],
                "recommendations": [],
                "risk_score": 0,
            }

            # Check for common vulnerabilities
            vulnerabilities = await self._scan_for_vulnerabilities()
            scan_results["vulnerabilities"] = vulnerabilities

            # Calculate risk score
            risk_score = self._calculate_vulnerability_risk(vulnerabilities)
            scan_results["risk_score"] = risk_score

            # Generate recommendations
            recommendations = self._generate_remediation_recommendations(
                vulnerabilities
            )
            scan_results["recommendations"] = recommendations

            # Store scan results
            scan_id = f"scan_{int(time.time())}"
            self.scan_results[scan_id] = scan_results

            return scan_results

        except Exception as e:
            logging.error(f"Security scan failed: {e}")
            return {"error": str(e)}

    async def _scan_for_vulnerabilities(self) -> List[Dict]:
        """Scan for security vulnerabilities"""
        vulnerabilities = []

        # Check for common web vulnerabilities
        web_vulns = await self._scan_web_vulnerabilities()
        vulnerabilities.extend(web_vulns)

        # Check for configuration issues
        config_vulns = await self._scan_configuration_issues()
        vulnerabilities.extend(config_vulns)

        # Check for outdated dependencies
        dep_vulns = await self._scan_dependency_vulnerabilities()
        vulnerabilities.extend(dep_vulns)

        return vulnerabilities

    async def _scan_web_vulnerabilities(self) -> List[Dict]:
        """Scan for web application vulnerabilities"""
        vulnerabilities = []

        # Check for common web security issues
        web_checks = [
            ("https", "HTTPS not enforced", RiskLevel.HIGH),
            ("security_headers", "Missing security headers", RiskLevel.MEDIUM),
            ("xss_protection", "XSS protection not enabled", RiskLevel.HIGH),
            ("csrf_protection", "CSRF protection not enabled", RiskLevel.HIGH),
            (
                "sql_injection",
                "Potential SQL injection vulnerability",
                RiskLevel.CRITICAL,
            ),
        ]

        for check_name, description, severity in web_checks:
            # Simulate vulnerability detection
            is_vulnerable = self._simulate_vulnerability_check(check_name)

            if is_vulnerable:
                vulnerabilities.append(
                    {
                        "type": "web_vulnerability",
                        "check": check_name,
                        "description": description,
                        "severity": severity,
                        "discovered": timezone.now(),
                    }
                )

        return vulnerabilities

    async def _scan_configuration_issues(self) -> List[Dict]:
        """Scan for configuration security issues"""
        vulnerabilities = []

        # Check Django security settings
        security_checks = [
            (
                "DEBUG",
                settings.DEBUG,
                "Debug mode enabled in production",
                RiskLevel.HIGH,
            ),
            (
                "SECRET_KEY",
                len(getattr(settings, "SECRET_KEY", "")) < 50,
                "Weak secret key",
                RiskLevel.MEDIUM,
            ),
            (
                "ALLOWED_HOSTS",
                len(getattr(settings, "ALLOWED_HOSTS", ["*"])) > 1,
                "Overly permissive ALLOWED_HOSTS",
                RiskLevel.MEDIUM,
            ),
        ]

        for setting_name, condition, description, severity in security_checks:
            if condition:
                vulnerabilities.append(
                    {
                        "type": "configuration_issue",
                        "setting": setting_name,
                        "description": description,
                        "severity": severity,
                        "discovered": timezone.now(),
                    }
                )

        return vulnerabilities

    async def _scan_dependency_vulnerabilities(self) -> List[Dict]:
        """Scan for dependency vulnerabilities"""
        vulnerabilities = []

        # This would typically use tools like Safety, Bandit, or commercial scanners
        # For now, simulate some common vulnerabilities
        simulated_vulnerabilities = [
            ("django", "3.2.0", "CVE-2023-1234", RiskLevel.HIGH),
            ("requests", "2.25.0", "CVE-2023-5678", RiskLevel.MEDIUM),
            ("psycopg2", "2.8.0", "CVE-2023-9012", RiskLevel.LOW),
        ]

        for package, version, cve_id, severity in simulated_vulnerabilities:
            vulnerabilities.append(
                {
                    "type": "dependency_vulnerability",
                    "package": package,
                    "version": version,
                    "cve_id": cve_id,
                    "severity": severity,
                    "discovered": timezone.now(),
                }
            )

        return vulnerabilities

    def _simulate_vulnerability_check(self, check_name: str) -> bool:
        """Simulate vulnerability detection (for demo)"""
        # In production, this would actually test for vulnerabilities
        import random

        return secrets.random() < 0.1  # 10% chance of finding vulnerability

    def _calculate_vulnerability_risk(self, vulnerabilities: List[Dict]) -> float:
        """Calculate overall risk score from vulnerabilities"""
        if not vulnerabilities:
            return 0.0

        severity_weights = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 3,
            RiskLevel.HIGH: 7,
            RiskLevel.CRITICAL: 10,
        }

        total_score = sum(
            severity_weights.get(vuln["severity"], 1) for vuln in vulnerabilities
        )

        # Normalize to 0-100 scale
        max_possible_score = len(vulnerabilities) * 10
        return (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0

    def _generate_remediation_recommendations(
        self, vulnerabilities: List[Dict]
    ) -> List[Dict]:
        """Generate remediation recommendations"""
        recommendations = []

        # Group vulnerabilities by type
        vuln_types = {}
        for vuln in vulnerabilities:
            vuln_type = vuln["type"]
            if vuln_type not in vuln_types:
                vuln_types[vuln_type] = []
            vuln_types[vuln_type].append(vuln)

        # Generate recommendations for each type
        for vuln_type, vulns in vuln_types.items():
            if vuln_type == "web_vulnerability":
                recommendations.append(
                    {
                        "type": "security_hardening",
                        "priority": "high",
                        "description": "Implement web application security controls",
                        "actions": [
                            "Enable HTTPS for all connections",
                            "Implement proper security headers",
                            "Add XSS and CSRF protection",
                            "Use parameterized queries to prevent SQL injection",
                        ],
                    }
                )
            elif vuln_type == "configuration_issue":
                recommendations.append(
                    {
                        "type": "configuration_fix",
                        "priority": "medium",
                        "description": "Fix security configuration issues",
                        "actions": [
                            "Disable debug mode in production",
                            "Generate strong secret key",
                            "Restrict ALLOWED_HOSTS setting",
                        ],
                    }
                )
            elif vuln_type == "dependency_vulnerability":
                recommendations.append(
                    {
                        "type": "dependency_update",
                        "priority": "medium",
                        "description": "Update vulnerable dependencies",
                        "actions": [
                            "Update packages to latest secure versions",
                            "Implement dependency scanning in CI/CD",
                            "Regular security updates",
                        ],
                    }
                )

        return recommendations


class SecurityComplianceFramework:
    """Main security and compliance framework"""

    def __init__(self):
        self.encryption_manager = DataEncryptionManager()
        self.access_control = AccessControlManager()
        self.audit_manager = SecurityAuditManager()
        self.privacy_manager = DataPrivacyManager()
        self.vulnerability_manager = VulnerabilityManager()
        self.compliance_standards = {
            ComplianceStandard.HIPAA: self._setup_hipaa_compliance(),
            ComplianceStandard.GDPR: self._setup_gdpr_compliance(),
            ComplianceStandard.PCI_DSS: self._setup_pci_compliance(),
        }

    def _setup_hipaa_compliance(self) -> Dict:
        """Setup HIPAA compliance requirements"""
        return {
            "technical_safeguards": [
                "Access control",
                "Audit controls",
                "Integrity controls",
                "Transmission security",
            ],
            "administrative_safeguards": [
                "Security management process",
                "Workforce security",
                "Information access management",
                "Training and awareness",
            ],
            "physical_safeguards": [
                "Facility access controls",
                "Workstation security",
                "Device and media controls",
            ],
        }

    def _setup_gdpr_compliance(self) -> Dict:
        """Setup GDPR compliance requirements"""
        return {
            "data_protection_principles": [
                "Lawfulness, fairness and transparency",
                "Purpose limitation",
                "Data minimization",
                "Accuracy",
                "Storage limitation",
                "Integrity and confidentiality",
                "Accountability",
            ],
            "data_subject_rights": [
                "Right to be informed",
                "Right of access",
                "Right to rectification",
                "Right to erasure",
                "Right to restrict processing",
                "Right to data portability",
                "Right to object",
            ],
        }

    def _setup_pci_compliance(self) -> Dict:
        """Setup PCI DSS compliance requirements"""
        return {
            "requirements": [
                "Install and maintain network security controls",
                "Apply secure configuration to all system components",
                "Protect stored account data",
                "Encrypt transmission of cardholder data",
                "Protect all systems against malware",
                "Develop and maintain secure systems",
                "Restrict access to cardholder data",
                "Identify and authenticate access to system components",
                "Restrict physical access to cardholder data",
                "Track and monitor all access to network resources",
                "Regularly test security systems",
                "Maintain information security policy",
            ]
        }

    async def perform_security_assessment(self) -> Dict:
        """Perform comprehensive security assessment"""
        try:
            assessment = {
                "timestamp": timezone.now(),
                "overall_score": 0,
                "areas": {},
                "recommendations": [],
                "critical_findings": [],
            }

            # Vulnerability scan
            vuln_scan = await self.vulnerability_manager.run_security_scan()
            assessment["areas"]["vulnerabilities"] = vuln_scan

            # Compliance reports
            compliance_scores = {}
            for standard in self.compliance_standards:
                report = self.audit_manager.generate_compliance_report(standard)
                if report:
                    compliance_scores[standard.value] = report.score

            assessment["areas"]["compliance"] = compliance_scores

            # Calculate overall score
            all_scores = [vuln_scan.get("risk_score", 0)] + list(
                compliance_scores.values()
            )
            assessment["overall_score"] = (
                100 - sum(all_scores) / len(all_scores) if all_scores else 100
            )

            # Generate critical findings
            if vuln_scan.get("vulnerabilities"):
                critical_vulns = [
                    vuln
                    for vuln in vuln_scan["vulnerabilities"]
                    if vuln["severity"] == RiskLevel.CRITICAL
                ]
                assessment["critical_findings"] = critical_vulns

            return assessment

        except Exception as e:
            logging.error(f"Security assessment failed: {e}")
            return {"error": str(e)}

    def get_security_dashboard(self) -> Dict:
        """Get security dashboard data"""
        try:
            dashboard = {
                "timestamp": timezone.now(),
                "security_metrics": {
                    "total_events": len(self.audit_manager.audit_logs),
                    "critical_events": len(
                        [
                            e
                            for e in self.audit_manager.audit_logs
                            if e.severity == RiskLevel.CRITICAL
                        ]
                    ),
                    "active_vulnerabilities": len(
                        self.vulnerability_manager.vulnerabilities
                    ),
                    "compliance_scores": {
                        standard.value: (
                            self.audit_manager.compliance_reports[standard.value].score
                            if standard.value in self.audit_manager.compliance_reports
                            else 0
                        )
                        for standard in ComplianceStandard
                    },
                },
                "recent_events": [
                    asdict(event)
                    for event in sorted(
                        self.audit_manager.audit_logs,
                        key=lambda x: x.timestamp,
                        reverse=True,
                    )[:10]
                ],
            }

            return dashboard

        except Exception as e:
            logging.error(f"Failed to generate security dashboard: {e}")
            return {"error": str(e)}


# Global security framework instance
security_framework = SecurityComplianceFramework()


# Convenience functions for use in other modules
def encrypt_sensitive_data(data: Any) -> str:
    """Encrypt sensitive data"""
    return security_framework.encryption_manager.encrypt_data(data)


def decrypt_sensitive_data(encrypted_data: str) -> Any:
    """Decrypt sensitive data"""
    return security_framework.encryption_manager.decrypt_data(encrypted_data)


def check_user_permission(
    user: User, resource: str, action: str, context: Dict = None
) -> Tuple[bool, str]:
    """Check user permission"""
    return security_framework.access_control.check_permission(
        user, resource, action, context
    )


def log_security_event(
    event_type: str, user: User = None, request=None, metadata: Dict = None
):
    """Log security event"""
    return security_framework.audit_manager.log_security_event(
        event_type, user, request, metadata
    )


async def perform_security_assessment() -> Dict:
    """Perform security assessment"""
    return await security_framework.perform_security_assessment()
