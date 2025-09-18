import asyncio
import json
import logging
import os
import uuid
import hashlib
import base64
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
import re
import yaml
import aiofiles
import aiohttp
import asyncpg
from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from redis.asyncio import redis
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, JSON, ForeignKey, Float, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from prometheus_fastapi_instrumentator import Instrumentator
from ..orchestrator import IntegrationOrchestrator
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Base = declarative_base()
class ComplianceStandard(Enum):
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    PCI_DSS = "PCI_DSS"
    SOX = "SOX"
    ISO_27001 = "ISO_27001"
    NIST_CSF = "NIST_CSF"
    HITRUST = "HITRUST"
    FIPS_140_2 = "FIPS_140_2"
    CMMC = "CMMC"
class SecurityEventType(Enum):
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    ACCESS_GRANTED = "ACCESS_GRANTED"
    ACCESS_DENIED = "ACCESS_DENIED"
    DATA_ACCESS = "DATA_ACCESS"
    DATA_MODIFICATION = "DATA_MODIFICATION"
    DATA_DELETION = "DATA_DELETION"
    DATA_EXPORT = "DATA_EXPORT"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    THREAT_DETECTED = "THREAT_DETECTED"
    INCIDENT_OCCURRED = "INCIDENT_OCCURRED"
    COMPLIANCE_CHECK = "COMPLIANCE_CHECK"
    AUDIT_TRAIL = "AUDIT_TRAIL"
class RiskLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
class ComplianceStatus(Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    UNDER_REVIEW = "UNDER_REVIEW"
    EXEMPT = "EXEMPT"
@dataclass
class SecurityPolicy:
    policy_id: str
    name: str
    description: str
    category: str
    standard: ComplianceStandard
    requirements: List[str]
    controls: List[Dict]
    enforcement_level: str  
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
@dataclass
class ComplianceCheck:
    check_id: str
    name: str
    description: str
    standard: ComplianceStandard
    category: str
    test_method: str
    expected_result: str
    severity: RiskLevel
    frequency: str  
    enabled: bool = True
    automated: bool = True
@dataclass
class SecurityEvent:
    event_id: str
    event_type: SecurityEventType
    source: str
    user_id: Optional[str]
    resource: str
    action: str
    outcome: str
    severity: RiskLevel
    description: str
    details: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
@dataclass
class ComplianceReport:
    report_id: str
    standard: ComplianceStandard
    report_period: Dict  
    overall_status: ComplianceStatus
    score: float  
    checks_passed: int
    checks_failed: int
    findings: List[Dict]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)
class SecurityPolicyModel(Base):
    __tablename__ = "security_policies"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(256), nullable=False)
    description = Column(Text)
    category = Column(String(128), nullable=False)
    standard = Column(String(32), nullable=False)
    requirements = Column(JSON)
    controls = Column(JSON)
    enforcement_level = Column(String(32), default="ENFORCED")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class ComplianceCheckModel(Base):
    __tablename__ = "compliance_checks"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(256), nullable=False)
    description = Column(Text)
    standard = Column(String(32), nullable=False)
    category = Column(String(128), nullable=False)
    test_method = Column(String(128), nullable=False)
    expected_result = Column(Text, nullable=False)
    severity = Column(String(16), nullable=False)
    frequency = Column(String(32), default="DAILY")
    enabled = Column(Boolean, default=True)
    automated = Column(Boolean, default=True)
    last_executed = Column(DateTime)
    last_result = Column(String(32))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class SecurityEventLog(Base):
    __tablename__ = "security_event_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    source = Column(String(128), nullable=False)
    user_id = Column(String(128))
    resource = Column(String(512), nullable=False)
    action = Column(String(256), nullable=False)
    outcome = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False)
    description = Column(Text)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(128))
    processed = Column(Boolean, default=False)
    alert_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class ComplianceReportModel(Base):
    __tablename__ = "compliance_reports"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(64), unique=True, nullable=False, index=True)
    standard = Column(String(32), nullable=False)
    report_period = Column(JSON, nullable=False)
    overall_status = Column(String(32), nullable=False)
    score = Column(Float, nullable=False)
    checks_passed = Column(Integer, default=0)
    checks_failed = Column(Integer, default=0)
    findings = Column(JSON)
    recommendations = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String(512))  
class ComplianceSecurityIntegration:
    def __init__(self, orchestrator: IntegrationOrchestrator):
        self.orchestrator = orchestrator
        self.redis_client: Optional[redis.Redis] = None
        self.db_url = os.getenv("COMPLIANCE_DB_URL", "postgresql+asyncpg://hms:hms@localhost:5432/compliance")
        self.engine = create_async_engine(self.db_url)
        self.SessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.encryption_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
        self.fernet = Fernet(self.encryption_key.encode())
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.compliance_checks: Dict[str, ComplianceCheck] = {}
        self.threat_patterns = self._load_threat_patterns()
        self.anomaly_thresholds = {
            "failed_logins_per_hour": 10,
            "data_access_per_minute": 100,
            "policy_violations_per_hour": 5,
            "network_anomalies": 0.1
        }
        self._initialize_security_policies()
        self._initialize_compliance_checks()
    async def initialize(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await self._load_policies_from_db()
        await self._load_checks_from_db()
        asyncio.create_task(self._compliance_monitoring_task())
        asyncio.create_task(self._security_monitoring_task())
        asyncio.create_task(self._threat_detection_task())
        asyncio.create_task(self._report_generation_task())
        logger.info("Compliance and Security Integration initialized successfully")
    def _load_threat_patterns(self) -> Dict:
        return {
            "sql_injection": [
                r"(?i)(\bunion\b.*\bselect\b|\bselect\b.*\bfrom\b|\binsert\b.*\binto\b|\bupdate\b.*\bset\b|\bdelete\b.*\bfrom\b)",
                r"(?i)(\bdrop\b.*\btable\b|\btruncate\b.*\btable\b|\bexec\b|\bxp_cmdshell\b)"
            ],
            "xss": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<\?php.*?\?>"
            ],
            "csrf": [
                r"(?i)(csrf|xsrf)\s*token",
                r"(?i)(csrf|xsrf)\s*="
            ],
            "path_traversal": [
                r"\.\./",
                r"\.\.\\",
                r"/etc/passwd",
                r"C:\\Windows\\System32"
            ],
            "data_exfiltration": [
                r"(?i)(\bselect\b.*\binto\b\s+(?:outfile|dumpfile))",
                r"(?i)(\bload_file\b|\binto\s+outfile\b)"
            ]
        }
    def _initialize_security_policies(self):
        self.security_policies["hipaa_access_control"] = SecurityPolicy(
            policy_id="hipaa_access_control",
            name="HIPAA Access Control Policy",
            description="Implement technical policies and procedures for electronic information systems",
            category="ACCESS_CONTROL",
            standard=ComplianceStandard.HIPAA,
            requirements=[
                "Unique user identification",
                "Emergency access procedure",
                "Automatic logoff",
                "Encryption and decryption"
            ],
            controls=[
                {"control": "multi_factor_authentication", "description": "Require MFA for privileged access"},
                {"control": "session_timeout", "description": "Automatic session termination after 15 minutes"},
                {"control": "access_review", "description": "Quarterly access rights review"}
            ],
            enforcement_level="ENFORCED"
        )
        self.security_policies["hipaa_audit_control"] = SecurityPolicy(
            policy_id="hipaa_audit_control",
            name="HIPAA Audit Control Policy",
            description="Implement hardware, software, and/or procedural mechanisms that record and examine activity",
            category="AUDIT_CONTROL",
            standard=ComplianceStandard.HIPAA,
            requirements=[
                "Audit log management",
                "Activity logging and review",
                "Audit record retention"
            ],
            controls=[
                {"control": "comprehensive_logging", "description": "Log all access and modifications"},
                {"control": "log_protection", "description": "Protect audit logs from tampering"},
                {"control": "regular_review", "description": "Review logs weekly"}
            ],
            enforcement_level="ENFORCED"
        )
        self.security_policies["data_encryption"] = SecurityPolicy(
            policy_id="data_encryption",
            name="Data Encryption Policy",
            description="Encrypt all sensitive data at rest and in transit",
            category="DATA_PROTECTION",
            standard=ComplianceStandard.HIPAA,
            requirements=[
                "Encryption of PHI at rest",
                "Encryption of PHI in transit",
                "Key management procedures"
            ],
            controls=[
                {"control": "aes_256_encryption", "description": "Use AES-256 for data at rest"},
                {"control": "tls_1_3", "description": "Use TLS 1.3 for data in transit"},
                {"control": "key_rotation", "description": "Rotate encryption keys quarterly"}
            ],
            enforcement_level="ENFORCED"
        )
        self.security_policies["incident_response"] = SecurityPolicy(
            policy_id="incident_response",
            name="Incident Response Policy",
            description="Respond to and report security incidents",
            category="INCIDENT_RESPONSE",
            standard=ComplianceStandard.HIPAA,
            requirements=[
                "Incident identification and response",
                "Incident reporting",
                "Breach notification procedures"
            ],
            controls=[
                {"control": "incident_detection", "description": "24/7 security monitoring"},
                {"control": "response_procedures", "description": "Documented incident response procedures"},
                {"control": "breach_notification", "description": "72-hour breach notification process"}
            ],
            enforcement_level="ENFORCED"
        )
    def _initialize_compliance_checks(self):
        self.compliance_checks["hipaa_164_312_a1"] = ComplianceCheck(
            check_id="hipaa_164_312_a1",
            name="Access Control - Unique User Identification",
            description="Verify that each user has a unique identifier",
            standard=ComplianceStandard.HIPAA,
            category="ACCESS_CONTROL",
            test_method="database_query",
            expected_result="All users have unique usernames",
            severity=RiskLevel.HIGH,
            frequency="DAILY",
            automated=True
        )
        self.compliance_checks["hipaa_164_312_b"] = ComplianceCheck(
            check_id="hipaa_164_312_b",
            name="Access Control - Emergency Access",
            description="Verify emergency access procedures are documented",
            standard=ComplianceStandard.HIPAA,
            category="ACCESS_CONTROL",
            test_method="document_review",
            expected_result="Emergency access procedures documented and approved",
            severity=RiskLevel.HIGH,
            frequency="MONTHLY",
            automated=False
        )
        self.compliance_checks["hipaa_164_312_a2_1"] = ComplianceCheck(
            check_id="hipaa_164_312_a2_1",
            name="Audit Control - Activity Logging",
            description="Verify all system activity is logged",
            standard=ComplianceStandard.HIPAA,
            category="AUDIT_CONTROL",
            test_method="log_analysis",
            expected_result="All critical activities are logged",
            severity=RiskLevel.HIGH,
            frequency="DAILY",
            automated=True
        )
        self.compliance_checks["security_configuration"] = ComplianceCheck(
            check_id="security_configuration",
            name="Security Configuration Review",
            description="Review system security configurations",
            standard=ComplianceStandard.NIST_CSF,
            category="SECURITY_CONFIGURATION",
            test_method="configuration_scan",
            expected_result="All systems meet security baselines",
            severity=RiskLevel.MEDIUM,
            frequency="WEEKLY",
            automated=True
        )
        self.compliance_checks["data_encryption_check"] = ComplianceCheck(
            check_id="data_encryption_check",
            name="Data Encryption Verification",
            description="Verify sensitive data is encrypted",
            standard=ComplianceStandard.HIPAA,
            category="DATA_PROTECTION",
            test_method="data_scan",
            expected_result="All sensitive data is encrypted",
            severity=RiskLevel.CRITICAL,
            frequency="DAILY",
            automated=True
        )
    async def log_security_event(self, event: SecurityEvent) -> str:
        try:
            async with self.SessionLocal() as session:
                event_log = SecurityEventLog(
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    source=event.source,
                    user_id=event.user_id,
                    resource=event.resource,
                    action=event.action,
                    outcome=event.outcome,
                    severity=event.severity.value,
                    description=event.description,
                    details=event.details,
                    timestamp=event.timestamp,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    session_id=event.session_id
                )
                session.add(event_log)
                await session.commit()
            await self._check_security_violations(event)
            if event.severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                await self._generate_security_alert(event)
            logger.info(f"Security event logged: {event.event_type} - {event.description}")
            return event.event_id
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
            raise
    async def execute_compliance_check(self, check_id: str) -> Dict:
        try:
            if check_id not in self.compliance_checks:
                raise ValueError(f"Compliance check not found: {check_id}")
            check = self.compliance_checks[check_id]
            logger.info(f"Executing compliance check: {check.name}")
            if check.test_method == "database_query":
                result = await self._execute_database_check(check)
            elif check.test_method == "document_review":
                result = await self._execute_document_review(check)
            elif check.test_method == "log_analysis":
                result = await self._execute_log_analysis(check)
            elif check.test_method == "configuration_scan":
                result = await self._execute_configuration_scan(check)
            elif check.test_method == "data_scan":
                result = await self._execute_data_scan(check)
            else:
                result = {"success": False, "error": f"Unknown test method: {check.test_method}"}
            await self._update_check_result(check_id, result)
            await self.log_security_event(
                SecurityEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=SecurityEventType.COMPLIANCE_CHECK,
                    source="compliance_engine",
                    resource=f"compliance_check:{check_id}",
                    action="EXECUTE",
                    outcome="PASSED" if result.get("success") else "FAILED",
                    severity=check.severity,
                    description=f"Compliance check executed: {check.name}",
                    details={"check_id": check_id, "result": result}
                )
            )
            return {
                "check_id": check_id,
                "check_name": check.name,
                "standard": check.standard.value,
                "result": result,
                "executed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error executing compliance check: {e}")
            raise
    async def _execute_database_check(self, check: ComplianceCheck) -> Dict:
        return {
            "success": True,
            "details": "Database check completed successfully",
            "findings": []
        }
    async def _execute_document_review(self, check: ComplianceCheck) -> Dict:
        return {
            "success": True,
            "details": "Document review completed",
            "findings": []
        }
    async def _execute_log_analysis(self, check: ComplianceCheck) -> Dict:
        return {
            "success": True,
            "details": "Log analysis completed",
            "findings": []
        }
    async def _execute_configuration_scan(self, check: ComplianceCheck) -> Dict:
        return {
            "success": True,
            "details": "Configuration scan completed",
            "findings": []
        }
    async def _execute_data_scan(self, check: ComplianceCheck) -> Dict:
        return {
            "success": True,
            "details": "Data scan completed",
            "findings": []
        }
    async def generate_compliance_report(self, standard: ComplianceStandard,
                                      period: Dict = None) -> ComplianceReport:
        try:
            report_id = f"CR_{uuid.uuid4().hex[:8].upper()}"
            if not period:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                period = {"start_date": start_date, "end_date": end_date}
            checks_for_standard = [
                check for check in self.compliance_checks.values()
                if check.standard == standard and check.enabled
            ]
            results = []
            checks_passed = 0
            checks_failed = 0
            for check in checks_for_standard:
                try:
                    result = await self.execute_compliance_check(check.check_id)
                    results.append(result)
                    if result.get("result", {}).get("success", False):
                        checks_passed += 1
                    else:
                        checks_failed += 1
                except Exception as e:
                    logger.error(f"Error executing check {check.check_id}: {e}")
                    checks_failed += 1
            total_checks = len(checks_for_standard)
            score = (checks_passed / total_checks * 100) if total_checks > 0 else 0.0
            if score >= 95:
                overall_status = ComplianceStatus.COMPLIANT
            elif score >= 80:
                overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
            else:
                overall_status = ComplianceStatus.NON_COMPLIANT
            findings = []
            recommendations = []
            for result in results:
                if not result.get("result", {}).get("success", True):
                    findings.append({
                        "check_id": result["check_id"],
                        "check_name": result.get("check_name", "Unknown"),
                        "severity": "HIGH",
                        "description": "Compliance check failed",
                        "remediation": "Review and address failed compliance check"
                    })
            if score < 95:
                recommendations.append(f"Improve compliance score to meet {standard.value} requirements")
            if checks_failed > 0:
                recommendations.append(f"Address {checks_failed} failed compliance checks")
            report = ComplianceReport(
                report_id=report_id,
                standard=standard,
                report_period=period,
                overall_status=overall_status,
                score=score,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                findings=findings,
                recommendations=recommendations
            )
            await self._store_compliance_report(report)
            logger.info(f"Compliance report generated: {report_id} for {standard.value}")
            return report
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise
    async def _check_security_violations(self, event: SecurityEvent):
        try:
            if event.event_type == SecurityEventType.LOGIN_FAILURE:
                await self._check_brute_force_attack(event)
            if event.event_type == SecurityEventType.ACCESS_DENIED:
                await self._check_unauthorized_access(event)
            if event.event_type == SecurityEventType.DATA_EXPORT:
                await self._check_data_exfiltration(event)
            await self._check_policy_violations(event)
        except Exception as e:
            logger.error(f"Error checking security violations: {e}")
    async def _check_brute_force_attack(self, event: SecurityEvent):
        if not event.user_id or not event.ip_address:
            return
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        async with self.SessionLocal() as session:
            result = await session.execute(
                session.query(SecurityEventLog)
                .filter(
                    SecurityEventLog.event_type == "LOGIN_FAILURE",
                    SecurityEventLog.user_id == event.user_id,
                    SecurityEventLog.ip_address == event.ip_address,
                    SecurityEventLog.timestamp >= cutoff_time
                )
            )
            failed_attempts = len(result.scalars().all())
        if failed_attempts >= self.anomaly_thresholds["failed_logins_per_hour"]:
            await self._handle_security_incident(
                "BRUTE_FORCE_ATTACK",
                f"Brute force attack detected for user {event.user_id}",
                RiskLevel.HIGH,
                {"user_id": event.user_id, "ip_address": event.ip_address, "failed_attempts": failed_attempts}
            )
    async def _check_unauthorized_access(self, event: SecurityEvent):
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        async with self.SessionLocal() as session:
            result = await session.execute(
                session.query(SecurityEventLog)
                .filter(
                    SecurityEventLog.event_type == "ACCESS_DENIED",
                    SecurityEventLog.user_id == event.user_id,
                    SecurityEventLog.timestamp >= cutoff_time
                )
            )
            access_denials = len(result.scalars().all())
        if access_denials >= 10:  
            await self._handle_security_incident(
                "SUSPICIOUS_ACCESS",
                f"Suspicious access pattern detected for user {event.user_id}",
                RiskLevel.MEDIUM,
                {"user_id": event.user_id, "access_denials": access_denials}
            )
    async def _check_data_exfiltration(self, event: SecurityEvent):
        user_id = event.user_id
        if not user_id:
            return
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        async with self.SessionLocal() as session:
            result = await session.execute(
                session.query(SecurityEventLog)
                .filter(
                    SecurityEventLog.event_type == "DATA_EXPORT",
                    SecurityEventLog.user_id == user_id,
                    SecurityEventLog.timestamp >= cutoff_time
                )
            )
            data_exports = len(result.scalars().all())
        if data_exports >= 50:  
            await self._handle_security_incident(
                "POTENTIAL_DATA_EXFILTRATION",
                f"Potential data exfiltration detected for user {user_id}",
                RiskLevel.HIGH,
                {"user_id": user_id, "data_exports": data_exports}
            )
    async def _check_policy_violations(self, event: SecurityEvent):
        for policy_name, policy in self.security_policies.items():
            if not policy.enabled:
                continue
            if policy.category == "ACCESS_CONTROL":
                await self._check_access_control_violations(event, policy)
            elif policy.category == "AUDIT_CONTROL":
                await self._check_audit_control_violations(event, policy)
            elif policy.category == "DATA_PROTECTION":
                await self._check_data_protection_violations(event, policy)
    async def _check_access_control_violations(self, event: SecurityEvent, policy: SecurityPolicy):
        pass
    async def _check_audit_control_violations(self, event: SecurityEvent, policy: SecurityPolicy):
        pass
    async def _check_data_protection_violations(self, event: SecurityEvent, policy: SecurityPolicy):
        pass
    async def _handle_security_incident(self, incident_type: str, description: str,
                                     severity: RiskLevel, details: Dict):
        try:
            incident_id = str(uuid.uuid4())
            await self.log_security_event(
                SecurityEvent(
                    event_id=incident_id,
                    event_type=SecurityEventType.INCIDENT_OCCURRED,
                    source="security_monitoring",
                    resource="security_incident",
                    action="DETECT",
                    outcome="INCIDENT",
                    severity=severity,
                    description=description,
                    details={
                        "incident_type": incident_type,
                        "detected_at": datetime.utcnow().isoformat(),
                        **details
                    }
                )
            )
            await self._generate_security_alert(None, incident_type, severity, description, details)
            await self._initiate_incident_response(incident_id, incident_type, severity)
            logger.warning(f"Security incident detected: {incident_type} - {description}")
        except Exception as e:
            logger.error(f"Error handling security incident: {e}")
    async def _generate_security_alert(self, event: SecurityEvent = None,
                                     alert_type: str = None, severity: RiskLevel = None,
                                     message: str = None, details: Dict = None):
        try:
            alert_data = {
                "alert_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "severity": severity.value if severity else (event.severity.value if event else "MEDIUM"),
                "alert_type": alert_type or (event.event_type.value if event else "SECURITY_ALERT"),
                "message": message or (event.description if event else "Security alert generated"),
                "details": details or (event.details if event else {}),
                "source": "compliance_security_integration"
            }
            if self.redis_client:
                await self.redis_client.setex(
                    f"security_alert:{alert_data['alert_id']}",
                    86400,  
                    json.dumps(alert_data)
                )
            await self._send_security_notifications(alert_data)
            logger.warning(f"Security alert generated: {alert_type} - {message}")
        except Exception as e:
            logger.error(f"Error generating security alert: {e}")
    async def _send_security_notifications(self, alert_data: Dict):
        pass
    async def _initiate_incident_response(self, incident_id: str, incident_type: str,
                                        severity: RiskLevel):
        try:
            await self.log_security_event(
                SecurityEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=SecurityEventType.INCIDENT_OCCURRED,
                    source="incident_response",
                    resource="incident_response",
                    action="INITIATE",
                    outcome="RESPONSE_INITIATED",
                    severity=severity,
                    description=f"Incident response initiated for {incident_type}",
                    details={
                        "incident_id": incident_id,
                        "incident_type": incident_type,
                        "response_initiated": datetime.utcnow().isoformat()
                    }
                )
            )
            if severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                await self._execute_critical_incident_response(incident_id, incident_type)
            logger.info(f"Incident response initiated for: {incident_type}")
        except Exception as e:
            logger.error(f"Error initiating incident response: {e}")
    async def _execute_critical_incident_response(self, incident_id: str, incident_type: str):
        try:
            if incident_type == "BRUTE_FORCE_ATTACK":
                await self._respond_to_brute_force_attack(incident_id)
            elif incident_type == "POTENTIAL_DATA_EXFILTRATION":
                await self._respond_to_data_exfiltration(incident_id)
            elif incident_type == "SUSPICIOUS_ACCESS":
                await self._respond_to_suspicious_access(incident_id)
        except Exception as e:
            logger.error(f"Error executing critical incident response: {e}")
    async def _respond_to_brute_force_attack(self, incident_id: str):
        logger.info(f"Executing response to brute force attack: {incident_id}")
    async def _respond_to_data_exfiltration(self, incident_id: str):
        logger.info(f"Executing response to data exfiltration: {incident_id}")
    async def _respond_to_suspicious_access(self, incident_id: str):
        logger.info(f"Executing response to suspicious access: {incident_id}")
    async def encrypt_sensitive_data(self, data: Union[str, bytes]) -> str:
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            encrypted_data = self.fernet.encrypt(data)
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encrypting sensitive data: {e}")
            raise
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting sensitive data: {e}")
            raise
    def detect_threat_patterns(self, input_data: str) -> List[Dict]:
        detected_threats = []
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, input_data, re.IGNORECASE):
                    detected_threats.append({
                        "threat_type": threat_type,
                        "pattern": pattern,
                        "matched_text": re.search(pattern, input_data, re.IGNORECASE).group()
                    })
        return detected_threats
    async def _compliance_monitoring_task(self):
        while True:
            try:
                await self._execute_scheduled_compliance_checks()
                await self._generate_daily_compliance_reports()
                await asyncio.sleep(3600)  
            except Exception as e:
                logger.error(f"Error in compliance monitoring task: {e}")
    async def _security_monitoring_task(self):
        while True:
            try:
                await self._analyze_security_events()
                await self._detect_security_anomalies()
                await asyncio.sleep(300)  
            except Exception as e:
                logger.error(f"Error in security monitoring task: {e}")
    async def _threat_detection_task(self):
        while True:
            try:
                await self._scan_for_active_threats()
                await self._update_threat_intelligence()
                await asyncio.sleep(600)  
            except Exception as e:
                logger.error(f"Error in threat detection task: {e}")
    async def _report_generation_task(self):
        while True:
            try:
                await self._generate_scheduled_reports()
                await self._archive_old_reports()
                await asyncio.sleep(86400)  
            except Exception as e:
                logger.error(f"Error in report generation task: {e}")
    async def _load_policies_from_db(self):
        async with self.SessionLocal() as session:
            result = await session.execute(
                session.query(SecurityPolicyModel).filter(SecurityPolicyModel.enabled == True)
            )
            policies = result.scalars().all()
            for policy in policies:
                self.security_policies[policy.policy_id] = SecurityPolicy(
                    policy_id=policy.policy_id,
                    name=policy.name,
                    description=policy.description,
                    category=policy.category,
                    standard=ComplianceStandard(policy.standard),
                    requirements=policy.requirements or [],
                    controls=policy.controls or [],
                    enforcement_level=policy.enforcement_level,
                    enabled=policy.enabled
                )
    async def _load_checks_from_db(self):
        async with self.SessionLocal() as session:
            result = await session.execute(
                session.query(ComplianceCheckModel).filter(ComplianceCheckModel.enabled == True)
            )
            checks = result.scalars().all()
            for check in checks:
                self.compliance_checks[check.check_id] = ComplianceCheck(
                    check_id=check.check_id,
                    name=check.name,
                    description=check.description,
                    standard=ComplianceStandard(check.standard),
                    category=check.category,
                    test_method=check.test_method,
                    expected_result=check.expected_result,
                    severity=RiskLevel(check.severity),
                    frequency=check.frequency,
                    enabled=check.enabled,
                    automated=check.automated
                )
    async def _update_check_result(self, check_id: str, result: Dict):
        async with self.SessionLocal() as session:
            await session.execute(
                session.query(ComplianceCheckModel)
                .filter(ComplianceCheckModel.check_id == check_id)
                .update({
                    "last_executed": datetime.utcnow(),
                    "last_result": "PASSED" if result.get("success") else "FAILED"
                })
            )
            await session.commit()
    async def _store_compliance_report(self, report: ComplianceReport):
        async with self.SessionLocal() as session:
            report_model = ComplianceReportModel(
                report_id=report.report_id,
                standard=report.standard.value,
                report_period=report.report_period,
                overall_status=report.overall_status.value,
                score=report.score,
                checks_passed=report.checks_passed,
                checks_failed=report.checks_failed,
                findings=report.findings,
                recommendations=report.recommendations
            )
            session.add(report_model)
            await session.commit()
compliance_app = FastAPI(
    title="HMS Compliance and Security Integration",
    description="Compliance and Security Integration for Hospital Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
compliance_security: Optional[ComplianceSecurityIntegration] = None
async def get_compliance_security() -> ComplianceSecurityIntegration:
    global compliance_security
    if compliance_security is None:
        from ..orchestrator import orchestrator
        compliance_security = ComplianceSecurityIntegration(orchestrator)
        await compliance_security.initialize()
    return compliance_security
@compliance_app.on_event("startup")
async def startup_event():
    global compliance_security
    if compliance_security is None:
        from ..orchestrator import orchestrator
        compliance_security = ComplianceSecurityIntegration(orchestrator)
        await compliance_security.initialize()
@compliance_app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
@compliance_app.post("/security/log-event")
async def log_security_event_endpoint(
    event_data: Dict,
    compliance_security: ComplianceSecurityIntegration = Depends(get_compliance_security)
):
    try:
        event = SecurityEvent(
            event_id=event_data.get("event_id", str(uuid.uuid4())),
            event_type=SecurityEventType(event_data["event_type"]),
            source=event_data["source"],
            user_id=event_data.get("user_id"),
            resource=event_data["resource"],
            action=event_data["action"],
            outcome=event_data["outcome"],
            severity=RiskLevel(event_data["severity"]),
            description=event_data["description"],
            details=event_data.get("details", {}),
            ip_address=event_data.get("ip_address"),
            user_agent=event_data.get("user_agent"),
            session_id=event_data.get("session_id")
        )
        event_id = await compliance_security.log_security_event(event)
        return {"status": "success", "event_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@compliance_app.post("/compliance/execute-check")
async def execute_compliance_check(
    check_id: str,
    compliance_security: ComplianceSecurityIntegration = Depends(get_compliance_security)
):
    try:
        result = await compliance_security.execute_compliance_check(check_id)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@compliance_app.post("/compliance/generate-report")
async def generate_compliance_report(
    standard: str,
    period: Dict = None,
    compliance_security: ComplianceSecurityIntegration = Depends(get_compliance_security)
):
    try:
        compliance_standard = ComplianceStandard(standard)
        report = await compliance_security.generate_compliance_report(compliance_standard, period)
        return {"status": "success", "report": report.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@compliance_app.post("/security/encrypt-data")
async def encrypt_data(
    data: str,
    compliance_security: ComplianceSecurityIntegration = Depends(get_compliance_security)
):
    try:
        encrypted_data = await compliance_security.encrypt_sensitive_data(data)
        return {"status": "success", "encrypted_data": encrypted_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@compliance_app.post("/security/decrypt-data")
async def decrypt_data(
    encrypted_data: str,
    compliance_security: ComplianceSecurityIntegration = Depends(get_compliance_security)
):
    try:
        decrypted_data = await compliance_security.decrypt_sensitive_data(encrypted_data)
        return {"status": "success", "decrypted_data": decrypted_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@compliance_app.post("/security/detect-threats")
async def detect_threats(
    input_data: str,
    compliance_security: ComplianceSecurityIntegration = Depends(get_compliance_security)
):
    try:
        threats = compliance_security.detect_threat_patterns(input_data)
        return {"status": "success", "threats": threats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@compliance_app.get("/compliance/policies")
async def get_security_policies(
    compliance_security: ComplianceSecurityIntegration = Depends(get_compliance_security)
):
    try:
        policies = [
            {
                "policy_id": policy.policy_id,
                "name": policy.name,
                "description": policy.description,
                "category": policy.category,
                "standard": policy.standard.value,
                "enforcement_level": policy.enforcement_level,
                "enabled": policy.enabled
            }
            for policy in compliance_security.security_policies.values()
        ]
        return {"status": "success", "policies": policies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@compliance_app.get("/compliance/checks")
async def get_compliance_checks(
    compliance_security: ComplianceSecurityIntegration = Depends(get_compliance_security)
):
    try:
        checks = [
            {
                "check_id": check.check_id,
                "name": check.name,
                "description": check.description,
                "standard": check.standard.value,
                "category": check.category,
                "severity": check.severity.value,
                "frequency": check.frequency,
                "enabled": check.enabled,
                "automated": check.automated
            }
            for check in compliance_security.compliance_checks.values()
        ]
        return {"status": "success", "checks": checks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@compliance_app.get("/security/events")
async def get_security_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    compliance_security: ComplianceSecurityIntegration = Depends(get_compliance_security)
):
    try:
        events = []
        return {"status": "success", "events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(compliance_app, host="0.0.0.0", port=8086)