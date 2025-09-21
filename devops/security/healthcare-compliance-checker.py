#!/usr/bin/env python3
"""
HMS Enterprise-Grade Healthcare Compliance Checker
Specialized compliance validation for healthcare systems (HIPAA, GDPR, PCI-DSS)
"""

import os
import sys
import json
import re
import logging
import hashlib
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import ast
import pandas as pd
import numpy as np

class ComplianceFramework(Enum):
    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    FHIR = "fhir"

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_ASSESSED = "not_assessed"

class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ComplianceViolation:
    id: str
    framework: ComplianceFramework
    rule_id: str
    title: str
    description: str
    risk_level: RiskLevel
    location: str
    evidence: str
    remediation: str
    references: List[str]
    metadata: Dict[str, Any]

@dataclass
class ComplianceCheckResult:
    framework: ComplianceFramework
    overall_status: ComplianceStatus
    score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    violations: List[ComplianceViolation]
    metadata: Dict[str, Any]

class HealthcareComplianceChecker:
    """Enterprise-grade healthcare compliance checker"""

    def __init__(self, config_path: str = "devops/security/compliance-config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.violations = []

        # Initialize compliance rules
        self.hipaa_rules = self._load_hipaa_rules()
        self.gdpr_rules = self._load_gdpr_rules()
        self.pci_dss_rules = self._load_pci_dss_rules()
        self.fhir_rules = self._load_fhir_rules()

        # Code analysis patterns
        self.phi_patterns = self._load_phi_patterns()
        self.security_patterns = self._load_security_patterns()

    def _load_config(self, config_path: str) -> Dict:
        """Load compliance checker configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default compliance configuration"""
        return {
            "frameworks": {
                "hipaa": {"enabled": True, "strict_mode": True},
                "gdpr": {"enabled": True, "strict_mode": False},
                "pci_dss": {"enabled": True, "strict_mode": True},
                "fhir": {"enabled": True, "strict_mode": True}
            },
            "scan_targets": {
                "source_code": True,
                "configurations": True,
                "databases": True,
                "infrastructure": True
            },
            "reporting": {
                "detailed_report": True,
                "include_evidence": True,
                "include_remediation": True
            }
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for compliance checker"""
        logger = logging.getLogger('hms_compliance_checker')
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler('/var/log/hms/compliance-checker.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def _load_hipaa_rules(self) -> List[Dict]:
        """Load HIPAA compliance rules"""
        return [
            {
                "rule_id": "HIPAA-164.312(a)(1)",
                "title": "Access Control",
                "description": "Implement technical policies and procedures for electronic information systems that maintain electronic protected health information to allow access only to those persons or software programs that have been granted access rights.",
                "risk_level": RiskLevel.HIGH,
                "check_patterns": [
                    r"def\s+\w+.*authentication",
                    r"@login_required",
                    r"permission_classes",
                    r"has_perm"
                ],
                "file_patterns": ["*.py"],
                "remediation": "Implement proper authentication and authorization controls"
            },
            {
                "rule_id": "HIPAA-164.312(a)(2)(iv)",
                "title": "Encryption and Decryption",
                "description": "Implement mechanisms to encrypt and decrypt electronic protected health information.",
                "risk_level": RiskLevel.CRITICAL,
                "check_patterns": [
                    r"AES",
                    r"encrypt",
                    r"decrypt",
                    r"ssl_context",
                    r"TLS"
                ],
                "file_patterns": ["*.py"],
                "remediation": "Implement encryption for all PHI data at rest and in transit"
            },
            {
                "rule_id": "HIPAA-164.312(b)",
                "title": "Audit Controls",
                "description": "Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use electronic protected health information.",
                "risk_level": RiskLevel.HIGH,
                "check_patterns": [
                    r"audit_log",
                    r"logging",
                    r"LogEntry",
                    r"AuditTrail"
                ],
                "file_patterns": ["*.py"],
                "remediation": "Implement comprehensive audit logging for all PHI access"
            },
            {
                "rule_id": "HIPAA-164.312(e)(1)",
                "title": "Transmission Security",
                "description": "Implement technical security measures to guard against unauthorized access to electronic protected health information that is being transmitted over an electronic communications network.",
                "risk_level": RiskLevel.CRITICAL,
                "check_patterns": [
                    r"https://",
                    r"wss://",
                    r"SSL",
                    r"TLS"
                ],
                "file_patterns": ["*.py", "*.js", "*.jsx"],
                "remediation": "Ensure all data transmission uses secure protocols"
            }
        ]

    def _load_gdpr_rules(self) -> List[Dict]:
        """Load GDPR compliance rules"""
        return [
            {
                "rule_id": "GDPR-32",
                "title": "Security of Processing",
                "description": "Implement appropriate technical and organizational measures to ensure a level of security appropriate to the risk.",
                "risk_level": RiskLevel.HIGH,
                "check_patterns": [
                    r"security",
                    r"encryption",
                    r"access_control",
                    r"backup"
                ],
                "file_patterns": ["*.py"],
                "remediation": "Implement comprehensive security measures"
            },
            {
                "rule_id": "GDPR-17",
                "title": "Data Protection by Design and Default",
                "description": "Implement appropriate technical and organizational measures for data protection principles like data minimization.",
                "risk_level": RiskLevel.MEDIUM,
                "check_patterns": [
                    r"data_minimization",
                    r"privacy_by_design",
                    r"default_privacy"
                ],
                "file_patterns": ["*.py"],
                "remediation": "Implement privacy by design and default"
            }
        ]

    def _load_pci_dss_rules(self) -> List[Dict]:
        """Load PCI-DSS compliance rules"""
        return [
            {
                "rule_id": "PCI-3.1",
                "title": "Keep Cardholder Data to a Minimum",
                "description": "Keep cardholder data storage to a minimum.",
                "risk_level": RiskLevel.CRITICAL,
                "check_patterns": [
                    r"card_number",
                    r"cvv",
                    r"expiry",
                    r"credit_card"
                ],
                "file_patterns": ["*.py", "*.js", "*.jsx"],
                "remediation": "Minimize cardholder data storage and implement tokenization"
            },
            {
                "rule_id": "PCI-4.1",
                "title": "Use Strong Cryptography",
                "description": "Use strong cryptography and security protocols to safeguard sensitive cardholder data during transmission over open, public networks.",
                "risk_level": RiskLevel.CRITICAL,
                "check_patterns": [
                    r"AES-256",
                    r"TLS 1.2",
                    r"TLS 1.3",
                    r"HTTPS"
                ],
                "file_patterns": ["*.py"],
                "remediation": "Implement strong cryptography for all sensitive data"
            }
        ]

    def _load_fhir_rules(self) -> List[Dict]:
        """Load FHIR compliance rules"""
        return [
            {
                "rule_id": "FHIR-SEC-1",
                "title": "FHIR Security",
                "description": "Implement appropriate security measures for FHIR APIs and data access.",
                "risk_level": RiskLevel.HIGH,
                "check_patterns": [
                    r"@require_auth",
                    r"oauth2",
                    r"SMART",
                    r"FHIR"
                ],
                "file_patterns": ["*.py"],
                "remediation": "Implement FHIR security best practices"
            }
        ]

    def _load_phi_patterns(self) -> List[Dict]:
        """Load PHI detection patterns"""
        return [
            {
                "pattern": r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                "category": "identifier",
                "description": "Social Security Number"
            },
            {
                "pattern": r"\b[A-Za-z]\d{3}\d{2}\d{4}\b",  # Medical Record Number
                "category": "identifier",
                "description": "Medical Record Number"
            },
            {
                "pattern": r"\b\d{10}\b",  # Phone Number
                "category": "contact",
                "description": "Phone Number"
            },
            {
                "pattern": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit Card
                "category": "financial",
                "description": "Credit Card Number"
            },
            {
                "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
                "category": "contact",
                "description": "Email Address"
            }
        ]

    def _load_security_patterns(self) -> List[Dict]:
        """Load security vulnerability patterns"""
        return [
            {
                "pattern": r"password\s*=\s*['\"]\w+['\"]",
                "category": "hardcoded_credentials",
                "severity": RiskLevel.CRITICAL,
                "description": "Hardcoded password detected"
            },
            {
                "pattern": r"api_key\s*=\s*['\"]\w+['\"]",
                "category": "hardcoded_credentials",
                "severity": RiskLevel.CRITICAL,
                "description": "Hardcoded API key detected"
            },
            {
                "pattern": r"DEBUG\s*=\s*True",
                "category": "debug_mode",
                "severity": RiskLevel.HIGH,
                "description": "Debug mode enabled in production"
            }
        ]

    def run_comprehensive_check(self) -> Dict[str, ComplianceCheckResult]:
        """Run comprehensive compliance check across all frameworks"""
        self.logger.info("Starting comprehensive compliance check")

        results = {}

        if self.config["frameworks"]["hipaa"]["enabled"]:
            results["hipaa"] = self.check_hipaa_compliance()

        if self.config["frameworks"]["gdpr"]["enabled"]:
            results["gdpr"] = self.check_gdpr_compliance()

        if self.config["frameworks"]["pci_dss"]["enabled"]:
            results["pci_dss"] = self.check_pci_dss_compliance()

        if self.config["frameworks"]["fhir"]["enabled"]:
            results["fhir"] = self.check_fhir_compliance()

        return results

    def check_hipaa_compliance(self) -> ComplianceCheckResult:
        """Check HIPAA compliance"""
        self.logger.info("Starting HIPAA compliance check")
        violations = []
        passed_checks = 0
        total_checks = len(self.hipaa_rules)

        for rule in self.hipaa_rules:
            rule_violations = self._check_rule(rule, ComplianceFramework.HIPAA)
            violations.extend(rule_violations)

            if not rule_violations:
                passed_checks += 1

        # Additional PHI data scan
        phi_violations = self._scan_for_phi_data()
        violations.extend(phi_violations)
        total_checks += 1

        if not phi_violations:
            passed_checks += 1

        # Security pattern scan
        security_violations = self._scan_security_patterns()
        violations.extend(security_violations)
        total_checks += 1

        if not security_violations:
            passed_checks += 1

        score = (passed_checks / total_checks) * 100
        overall_status = self._determine_overall_status(score, violations)

        return ComplianceCheckResult(
            framework=ComplianceFramework.HIPAA,
            overall_status=overall_status,
            score=score,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            violations=violations,
            metadata={
                "strict_mode": self.config["frameworks"]["hipaa"]["strict_mode"],
                "scan_timestamp": datetime.now().isoformat()
            }
        )

    def check_gdpr_compliance(self) -> ComplianceCheckResult:
        """Check GDPR compliance"""
        self.logger.info("Starting GDPR compliance check")
        violations = []
        passed_checks = 0
        total_checks = len(self.gdpr_rules)

        for rule in self.gdpr_rules:
            rule_violations = self._check_rule(rule, ComplianceFramework.GDPR)
            violations.extend(rule_violations)

            if not rule_violations:
                passed_checks += 1

        # Additional GDPR-specific checks
        data_subject_rights_violations = self._check_data_subject_rights()
        violations.extend(data_subject_rights_violations)
        total_checks += 1

        if not data_subject_rights_violations:
            passed_checks += 1

        score = (passed_checks / total_checks) * 100
        overall_status = self._determine_overall_status(score, violations)

        return ComplianceCheckResult(
            framework=ComplianceFramework.GDPR,
            overall_status=overall_status,
            score=score,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            violations=violations,
            metadata={
                "strict_mode": self.config["frameworks"]["gdpr"]["strict_mode"],
                "scan_timestamp": datetime.now().isoformat()
            }
        )

    def check_pci_dss_compliance(self) -> ComplianceCheckResult:
        """Check PCI-DSS compliance"""
        self.logger.info("Starting PCI-DSS compliance check")
        violations = []
        passed_checks = 0
        total_checks = len(self.pci_dss_rules)

        for rule in self.pci_dss_rules:
            rule_violations = self._check_rule(rule, ComplianceFramework.PCI_DSS)
            violations.extend(rule_violations)

            if not rule_violations:
                passed_checks += 1

        # Additional PCI-DSS checks
        card_data_violations = self._scan_for_cardholder_data()
        violations.extend(card_data_violations)
        total_checks += 1

        if not card_data_violations:
            passed_checks += 1

        score = (passed_checks / total_checks) * 100
        overall_status = self._determine_overall_status(score, violations)

        return ComplianceCheckResult(
            framework=ComplianceFramework.PCI_DSS,
            overall_status=overall_status,
            score=score,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            violations=violations,
            metadata={
                "strict_mode": self.config["frameworks"]["pci_dss"]["strict_mode"],
                "scan_timestamp": datetime.now().isoformat()
            }
        )

    def check_fhir_compliance(self) -> ComplianceCheckResult:
        """Check FHIR compliance"""
        self.logger.info("Starting FHIR compliance check")
        violations = []
        passed_checks = 0
        total_checks = len(self.fhir_rules)

        for rule in self.fhir_rules:
            rule_violations = self._check_rule(rule, ComplianceFramework.FHIR)
            violations.extend(rule_violations)

            if not rule_violations:
                passed_checks += 1

        # Additional FHIR checks
        fhir_api_violations = self._check_fhir_api_security()
        violations.extend(fhir_api_violations)
        total_checks += 1

        if not fhir_api_violations:
            passed_checks += 1

        score = (passed_checks / total_checks) * 100
        overall_status = self._determine_overall_status(score, violations)

        return ComplianceCheckResult(
            framework=ComplianceFramework.FHIR,
            overall_status=overall_status,
            score=score,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            violations=violations,
            metadata={
                "strict_mode": self.config["frameworks"]["fhir"]["strict_mode"],
                "scan_timestamp": datetime.now().isoformat()
            }
        )

    def _check_rule(self, rule: Dict, framework: ComplianceFramework) -> List[ComplianceViolation]:
        """Check a specific compliance rule"""
        violations = []
        file_patterns = rule.get("file_patterns", ["*.py"])
        check_patterns = rule.get("check_patterns", [])

        for file_pattern in file_patterns:
            for file_path in Path(".").rglob(file_pattern):
                if file_path.is_file() and not self._should_skip_file(file_path):
                    file_violations = self._check_file_for_rule(
                        file_path, rule, framework, check_patterns
                    )
                    violations.extend(file_violations)

        return violations

    def _check_file_for_rule(self, file_path: Path, rule: Dict, framework: ComplianceFramework, patterns: List[str]) -> List[ComplianceViolation]:
        """Check a specific file for compliance rule violations"""
        violations = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    line_content = content.split('\n')[line_number - 1].strip()

                    violation = ComplianceViolation(
                        id=f"{framework.value}-{rule['rule_id']}-{hashlib.md5(f'{file_path}:{line_number}'.encode()).hexdigest()[:8]}",
                        framework=framework,
                        rule_id=rule['rule_id'],
                        title=rule['title'],
                        description=rule['description'],
                        risk_level=rule['risk_level'],
                        location=f"{file_path}:{line_number}",
                        evidence=line_content,
                        remediation=rule.get('remediation', 'Review and fix the compliance issue'),
                        references=rule.get('references', []),
                        metadata={
                            "file_path": str(file_path),
                            "line_number": line_number,
                            "pattern_matched": pattern,
                            "matched_text": match.group()
                        }
                    )
                    violations.append(violation)

        except Exception as e:
            self.logger.error(f"Error checking file {file_path}: {e}")

        return violations

    def _scan_for_phi_data(self) -> List[ComplianceViolation]:
        """Scan for potential PHI data in code"""
        violations = []
        phi_patterns = self._load_phi_patterns()

        for file_path in Path(".").rglob("*.py"):
            if file_path.is_file() and not self._should_skip_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for phi_pattern in phi_patterns:
                        matches = re.finditer(phi_pattern["pattern"], content)
                        for match in matches:
                            line_number = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_number - 1].strip()

                            violation = ComplianceViolation(
                                id=f"PHI-{hashlib.md5(f'{file_path}:{line_number}'.encode()).hexdigest()[:8]}",
                                framework=ComplianceFramework.HIPAA,
                                rule_id="HIPAA-PHI-DATA",
                                title=f"Potential PHI Data Found: {phi_pattern['description']}",
                                description=f"Detected potential {phi_pattern['description']} in source code",
                                risk_level=RiskLevel.CRITICAL,
                                location=f"{file_path}:{line_number}",
                                evidence=line_content,
                                remediation="Remove or properly anonymize PHI data from source code",
                                references=["HIPAA Privacy Rule"],
                                metadata={
                                    "file_path": str(file_path),
                                    "line_number": line_number,
                                    "phi_category": phi_pattern["category"],
                                    "matched_text": match.group()
                                }
                            )
                            violations.append(violation)

                except Exception as e:
                    self.logger.error(f"Error scanning file {file_path} for PHI: {e}")

        return violations

    def _scan_security_patterns(self) -> List[ComplianceViolation]:
        """Scan for security vulnerabilities"""
        violations = []
        security_patterns = self._load_security_patterns()

        for file_path in Path(".").rglob("*.py"):
            if file_path.is_file() and not self._should_skip_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for security_pattern in security_patterns:
                        matches = re.finditer(security_pattern["pattern"], content, re.IGNORECASE)
                        for match in matches:
                            line_number = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_number - 1].strip()

                            violation = ComplianceViolation(
                                id=f"SEC-{hashlib.md5(f'{file_path}:{line_number}'.encode()).hexdigest()[:8]}",
                                framework=ComplianceFramework.HIPAA,
                                rule_id="HIPAA-SECURITY",
                                title=f"Security Vulnerability: {security_pattern['description']}",
                                description=security_pattern['description'],
                                risk_level=security_pattern["severity"],
                                location=f"{file_path}:{line_number}",
                                evidence=line_content,
                                remediation="Fix the security vulnerability immediately",
                                references=["OWASP Top 10"],
                                metadata={
                                    "file_path": str(file_path),
                                    "line_number": line_number,
                                    "vulnerability_category": security_pattern["category"],
                                    "matched_text": match.group()
                                }
                            )
                            violations.append(violation)

                except Exception as e:
                    self.logger.error(f"Error scanning file {file_path} for security patterns: {e}")

        return violations

    def _check_data_subject_rights(self) -> List[ComplianceViolation]:
        """Check for GDPR data subject rights implementation"""
        violations = []

        # Check for data export functionality
        export_functions = [
            "export_data", "data_export", "download_data", "export_user_data"
        ]

        # Check for data deletion functionality
        deletion_functions = [
            "delete_account", "delete_data", "remove_user", "gdpr_delete"
        ]

        # Check for data access functionality
        access_functions = [
            "get_my_data", "access_data", "view_data", "data_access"
        ]

        # Scan for these functions
        all_functions = export_functions + deletion_functions + access_functions

        for file_path in Path(".").rglob("*.py"):
            if file_path.is_file() and not self._should_skip_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    tree = ast.parse(content)

                    # Check if functions are implemented
                    implemented_functions = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            implemented_functions.append(node.name)

                    missing_functions = set(all_functions) - set(implemented_functions)

                    if missing_functions:
                        violation = ComplianceViolation(
                            id=f"GDPR-DSR-{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}",
                            framework=ComplianceFramework.GDPR,
                            rule_id="GDPR-DSR",
                            title="Missing Data Subject Rights Implementation",
                            description=f"Missing data subject rights functions: {', '.join(missing_functions)}",
                            risk_level=RiskLevel.HIGH,
                            location=str(file_path),
                            evidence=f"Missing functions: {', '.join(missing_functions)}",
                            remediation="Implement all required data subject rights functions",
                            references=["GDPR Article 15-22"],
                            metadata={
                                "file_path": str(file_path),
                                "missing_functions": list(missing_functions)
                            }
                        )
                        violations.append(violation)

                except Exception as e:
                    self.logger.error(f"Error checking data subject rights in {file_path}: {e}")

        return violations

    def _scan_for_cardholder_data(self) -> List[ComplianceViolation]:
        """Scan for cardholder data (PCI-DSS)"""
        violations = []

        card_data_patterns = [
            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit Card
            r"\b\d{3}[ -]?\d{3}[ -]?\d{3}[ -]?\d{3}\b",  # Credit Card (alternative)
            r"\b\d{2}\/\d{2}\b",  # Expiry Date
            r"\b\d{3,4}\b",  # CVV (3-4 digits)
            r"card_number",
            r"credit_card",
            r"payment_method"
        ]

        for file_path in Path(".").rglob("*.py"):
            if file_path.is_file() and not self._should_skip_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in card_data_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_number = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_number - 1].strip()

                            violation = ComplianceViolation(
                                id=f"PCI-DATA-{hashlib.md5(f'{file_path}:{line_number}'.encode()).hexdigest()[:8]}",
                                framework=ComplianceFramework.PCI_DSS,
                                rule_id="PCI-DATA-STORAGE",
                                title="Potential Cardholder Data Found",
                                description="Potential cardholder data detected in source code",
                                risk_level=RiskLevel.CRITICAL,
                                location=f"{file_path}:{line_number}",
                                evidence=line_content,
                                remediation="Remove cardholder data or implement tokenization",
                                references=["PCI-DSS Requirement 3"],
                                metadata={
                                    "file_path": str(file_path),
                                    "line_number": line_number,
                                    "matched_text": match.group()
                                }
                            )
                            violations.append(violation)

                except Exception as e:
                    self.logger.error(f"Error scanning file {file_path} for cardholder data: {e}")

        return violations

    def _check_fhir_api_security(self) -> List[ComplianceViolation]:
        """Check FHIR API security implementation"""
        violations = []

        # Look for FHIR-related files
        fhir_files = list(Path(".").rglob("*fhir*.py")) + list(Path(".").rglob("api/*.py"))

        for file_path in fhir_files:
            if file_path.is_file() and not self._should_skip_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check for OAuth2/SMART on FHIR implementation
                    security_patterns = [
                        r"oauth2",
                        r"SMART",
                        r"@require_auth",
                        r"authentication",
                        r"authorization"
                    ]

                    security_implemented = any(re.search(pattern, content, re.IGNORECASE) for pattern in security_patterns)

                    if not security_implemented:
                        violation = ComplianceViolation(
                            id=f"FHIR-SEC-{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}",
                            framework=ComplianceFramework.FHIR,
                            rule_id="FHIR-SEC-1",
                            title="Missing FHIR Security Implementation",
                            description="FHIR API endpoints lack proper security implementation",
                            risk_level=RiskLevel.HIGH,
                            location=str(file_path),
                            evidence="No OAuth2/SMART on FHIR implementation found",
                            remediation="Implement OAuth2 and SMART on FHIR for FHIR APIs",
                            references=["FHIR Security Guidelines"],
                            metadata={
                                "file_path": str(file_path),
                                "security_patterns_found": security_implemented
                            }
                        )
                        violations.append(violation)

                except Exception as e:
                    self.logger.error(f"Error checking FHIR security in {file_path}: {e}")

        return violations

    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped during scanning"""
        skip_patterns = [
            "*/tests/*",
            "*/test_*",
            "*/migrations/*",
            "*/venv/*",
            "*/node_modules/*",
            "*/.git/*",
            "*/__pycache__/*",
            "*.pyc",
            "*/.*"
        ]

        file_str = str(file_path)
        return any(file_str.startswith(pattern.replace("*", "")) for pattern in skip_patterns)

    def _determine_overall_status(self, score: float, violations: List[ComplianceViolation]) -> ComplianceStatus:
        """Determine overall compliance status"""
        if score >= 90 and not any(v.risk_level == RiskLevel.CRITICAL for v in violations):
            return ComplianceStatus.COMPLIANT
        elif score >= 70:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            return ComplianceStatus.NON_COMPLIANT

    def generate_compliance_report(self, results: Dict[str, ComplianceCheckResult]) -> Dict:
        """Generate comprehensive compliance report"""
        self.logger.info("Generating compliance report")

        # Aggregate all violations
        all_violations = []
        framework_scores = {}

        for framework, result in results.items():
            all_violations.extend(result.violations)
            framework_scores[framework.value] = {
                "score": result.score,
                "status": result.overall_status.value,
                "violations_count": len(result.violations)
            }

        # Calculate overall score
        overall_score = sum(r.score for r in results.values()) / len(results) if results else 0

        # Determine overall status
        critical_violations = [v for v in all_violations if v.risk_level == RiskLevel.CRITICAL]
        high_violations = [v for v in all_violations if v.risk_level == RiskLevel.HIGH]

        if overall_score >= 90 and not critical_violations and not high_violations:
            overall_status = ComplianceStatus.COMPLIANT
        elif overall_score >= 70 and not critical_violations:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT

        # Generate recommendations
        recommendations = self._generate_compliance_recommendations(all_violations, results)

        report = {
            "report_metadata": {
                "timestamp": datetime.now().isoformat(),
                "overall_score": overall_score,
                "overall_status": overall_status.value,
                "total_violations": len(all_violations),
                "frameworks_checked": list(results.keys())
            },
            "framework_results": framework_scores,
            "violation_summary": {
                "by_framework": {framework.value: len(result.violations) for framework, result in results.items()},
                "by_risk_level": {
                    "critical": len([v for v in all_violations if v.risk_level == RiskLevel.CRITICAL]),
                    "high": len([v for v in all_violations if v.risk_level == RiskLevel.HIGH]),
                    "medium": len([v for v in all_violations if v.risk_level == RiskLevel.MEDIUM]),
                    "low": len([v for v in all_violations if v.risk_level == RiskLevel.LOW])
                },
                "by_category": self._categorize_violations(all_violations)
            },
            "top_violations": [asdict(v) for v in sorted(all_violations, key=lambda x: x.risk_level.value, reverse=True)[:10]],
            "recommendations": recommendations,
            "remediation_plan": self._generate_remediation_plan(all_violations)
        }

        return report

    def _categorize_violations(self, violations: List[ComplianceViolation]) -> Dict[str, int]:
        """Categorize violations by type"""
        categories = {}
        for violation in violations:
            category = violation.metadata.get("vulnerability_category", "other")
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _generate_compliance_recommendations(self, violations: List[ComplianceViolation], results: Dict[str, ComplianceCheckResult]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []

        # Critical issues first
        critical_violations = [v for v in violations if v.risk_level == RiskLevel.CRITICAL]
        if critical_violations:
            recommendations.append(f"🚨 Address {len(critical_violations)} critical violations immediately")

        # High-risk issues
        high_violations = [v for v in violations if v.risk_level == RiskLevel.HIGH]
        if high_violations:
            recommendations.append(f"⚠️ Prioritize {len(high_violations)} high-risk violations")

        # Framework-specific recommendations
        for framework, result in results.items():
            if result.score < 70:
                recommendations.append(f"📋 Improve {framework.value.upper()} compliance (current score: {result.score:.1f}%)")

        # Security recommendations
        security_violations = [v for v in violations if "security" in v.title.lower()]
        if security_violations:
            recommendations.append(f"🔒 Implement additional security controls for {len(security_violations)} security issues")

        return recommendations

    def _generate_remediation_plan(self, violations: List[ComplianceViolation]) -> Dict:
        """Generate remediation plan"""
        # Group violations by risk level
        critical_violations = [v for v in violations if v.risk_level == RiskLevel.CRITICAL]
        high_violations = [v for v in violations if v.risk_level == RiskLevel.HIGH]
        medium_violations = [v for v in violations if v.risk_level == RiskLevel.MEDIUM]
        low_violations = [v for v in violations if v.risk_level == RiskLevel.LOW]

        return {
            "immediate_actions": {
                "description": "Critical violations requiring immediate attention",
                "violations": [asdict(v) for v in critical_violations],
                "timeline": "24-48 hours",
                "priority": "Critical"
            },
            "short_term_actions": {
                "description": "High-risk violations to address within 30 days",
                "violations": [asdict(v) for v in high_violations],
                "timeline": "30 days",
                "priority": "High"
            },
            "medium_term_actions": {
                "description": "Medium-risk violations to address within 90 days",
                "violations": [asdict(v) for v in medium_violations],
                "timeline": "90 days",
                "priority": "Medium"
            },
            "long_term_actions": {
                "description": "Low-risk violations for continuous improvement",
                "violations": [asdict(v) for v in low_violations],
                "timeline": "180 days",
                "priority": "Low"
            }
        }

def main():
    """Main function for healthcare compliance checker"""
    import argparse

    parser = argparse.ArgumentParser(description='HMS Healthcare Compliance Checker')
    parser.add_argument('--config', '-c', default='devops/security/compliance-config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--framework', '-f', choices=['hipaa', 'gdpr', 'pci_dss', 'fhir', 'all'],
                       default='all', help='Compliance framework to check')
    parser.add_argument('--output', '-o', default='compliance-report.json',
                       help='Output file for compliance report')
    parser.add_argument('--detailed', '-d', action='store_true',
                       help='Generate detailed report with all violations')

    args = parser.parse_args()

    # Initialize compliance checker
    checker = HealthcareComplianceChecker(args.config)

    # Run compliance checks
    if args.framework == 'all':
        results = checker.run_comprehensive_check()
    else:
        framework_map = {
            'hipaa': checker.check_hipaa_compliance,
            'gdpr': checker.check_gdpr_compliance,
            'pci_dss': checker.check_pci_dss_compliance,
            'fhir': checker.check_fhir_compliance
        }
        results = {args.framework: framework_map[args.framework]()}

    # Generate report
    report = checker.generate_compliance_report(results)

    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"🏥 Compliance check completed. Report saved to {args.output}")

    # Print summary
    print(f"\n📊 Compliance Summary:")
    print(f"Overall Score: {report['report_metadata']['overall_score']:.1f}%")
    print(f"Overall Status: {report['report_metadata']['overall_status'].upper()}")
    print(f"Total Violations: {report['report_metadata']['total_violations']}")

    for framework, score_data in report['framework_results'].items():
        print(f"{framework.upper()}: {score_data['score']:.1f}% ({score_data['status']})")

if __name__ == "__main__":
    main()