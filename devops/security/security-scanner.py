#!/usr/bin/env python3
"""
HMS Enterprise-Grade Security Scanner
Comprehensive security scanning and vulnerability assessment for healthcare systems
"""

import os
import sys
import json
import yaml
import logging
import subprocess
import hashlib
import requests
import tempfile
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import boto3
from botocore.exceptions import ClientError
import docker
import kubernetes
from kubernetes import client, config

# Security scanning tools
import bandit
import semgrep
import safety
from trivy import Trivy

# Healthcare compliance
from hipaa_compliance import HIPAAComplianceChecker
from gdpr_compliance import GDPRComplianceChecker
from pci_dss_compliance import PCIDSSComplianceChecker

class SecurityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ScanType(Enum):
    SAST = "static_application_security_testing"
    DAST = "dynamic_application_security_testing"
    DEPENDENCY = "dependency_scanning"
    SECRETS = "secrets_scanning"
    CONTAINER = "container_scanning"
    COMPLIANCE = "compliance_scanning"
    INFRASTRUCTURE = "infrastructure_scanning"

@dataclass
class Vulnerability:
    id: str
    title: str
    description: str
    severity: SecurityLevel
    cvss_score: Optional[float]
    category: str
    scanner: str
    location: str
    remediation: str
    references: List[str]
    metadata: Dict[str, Any]

@dataclass
class SecurityScanResult:
    scan_type: ScanType
    scanner_name: str
    timestamp: datetime
    duration: float
    vulnerabilities: List[Vulnerability]
    metadata: Dict[str, Any]
    compliance_status: Dict[str, bool]

class HMSSecurityScanner:
    """Enterprise-grade security scanner for HMS healthcare system"""

    def __init__(self, config_path: str = "devops/security/security-config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.docker_client = docker.from_env()
        self._setup_kubernetes()

        # Initialize compliance checkers
        self.hipaa_checker = HIPAAComplianceChecker()
        self.gdpr_checker = GDPRComplianceChecker()
        self.pci_dss_checker = PCIDSSComplianceChecker()

        # AWS clients for cloud security
        self.ec2_client = boto3.client('ec2')
        self.s3_client = boto3.client('s3')
        self.iam_client = boto3.client('iam')
        self.security_hub_client = boto3.client('securityhub')

    def _load_config(self, config_path: str) -> Dict:
        """Load security scanner configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default security scanner configuration"""
        return {
            "scanners": {
                "sast": {
                    "enabled": True,
                    "tools": ["bandit", "semgrep", "codeql"],
                    "excludes": ["tests/*", "migrations/*"]
                },
                "dast": {
                    "enabled": True,
                    "tools": ["owasp_zap", "nuclei"],
                    "target_url": os.getenv("TARGET_URL", "http://localhost:8000")
                },
                "dependency": {
                    "enabled": True,
                    "tools": ["safety", "snyk", "npm_audit"],
                    "auto_update": True
                },
                "secrets": {
                    "enabled": True,
                    "tools": ["gitleaks", "trufflehog"],
                    "historical_scan": True
                },
                "container": {
                    "enabled": True,
                    "tools": ["trivy", "clair"],
                    "images": ["hms-backend", "hms-frontend"]
                },
                "compliance": {
                    "enabled": True,
                    "frameworks": ["HIPAA", "GDPR", "PCI_DSS"],
                    "strict_mode": True
                }
            },
            "thresholds": {
                "critical": 0,
                "high": 0,
                "medium": 5,
                "low": 10
            },
            "reporting": {
                "format": ["json", "html", "pdf"],
                "include_remediation": True,
                "executive_summary": True
            }
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for security scanner"""
        logger = logging.getLogger('hms_security_scanner')
        logger.setLevel(logging.INFO)

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)

        # File handler for security logs
        file_handler = logging.FileHandler('/var/log/hms/security-scanner.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def _setup_kubernetes(self):
        """Setup Kubernetes client for cluster security scanning"""
        try:
            config.load_kube_config()
            self.k8s_client = client.CoreV1Api()
            self.k8s_apps_client = client.AppsV1Api()
            self.k8s_networking_client = client.NetworkingV1Api()
        except Exception as e:
            self.logger.warning(f"Could not setup Kubernetes client: {e}")

    async def run_comprehensive_scan(self) -> List[SecurityScanResult]:
        """Run comprehensive security scan across all categories"""
        self.logger.info("Starting comprehensive security scan")

        scan_results = []
        tasks = []

        # SAST Scanning
        if self.config["scanners"]["sast"]["enabled"]:
            tasks.append(self.run_sast_scan())

        # DAST Scanning
        if self.config["scanners"]["dast"]["enabled"]:
            tasks.append(self.run_dast_scan())

        # Dependency Scanning
        if self.config["scanners"]["dependency"]["enabled"]:
            tasks.append(self.run_dependency_scan())

        # Secrets Scanning
        if self.config["scanners"]["secrets"]["enabled"]:
            tasks.append(self.run_secrets_scan())

        # Container Scanning
        if self.config["scanners"]["container"]["enabled"]:
            tasks.append(self.run_container_scan())

        # Compliance Scanning
        if self.config["scanners"]["compliance"]["enabled"]:
            tasks.append(self.run_compliance_scan())

        # Infrastructure Scanning
        tasks.append(self.run_infrastructure_scan())

        # Run all scans concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Scan failed: {result}")
            else:
                scan_results.append(result)

        return scan_results

    async def run_sast_scan(self) -> SecurityScanResult:
        """Run Static Application Security Testing"""
        self.logger.info("Starting SAST scan")
        start_time = datetime.now()
        vulnerabilities = []

        try:
            # Run Bandit
            bandit_results = await self._run_bandit_scan()
            vulnerabilities.extend(bandit_results)

            # Run Semgrep
            semgrep_results = await self._run_semgrep_scan()
            vulnerabilities.extend(semgrep_results)

            # Run CodeQL (if available)
            codeql_results = await self._run_codeql_scan()
            vulnerabilities.extend(codeql_results)

        except Exception as e:
            self.logger.error(f"SAST scan failed: {e}")

        duration = (datetime.now() - start_time).total_seconds()

        return SecurityScanResult(
            scan_type=ScanType.SAST,
            scanner_name="SAST Suite",
            timestamp=start_time,
            duration=duration,
            vulnerabilities=vulnerabilities,
            metadata={"tools_used": ["bandit", "semgrep", "codeql"]},
            compliance_status={}
        )

    async def _run_bandit_scan(self) -> List[Vulnerability]:
        """Run Bandit security scan"""
        vulnerabilities = []
        try:
            result = subprocess.run([
                'bandit', '-r', 'backend/', '-f', 'json', '-o', '/tmp/bandit-results.json'
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                with open('/tmp/bandit-results.json', 'r') as f:
                    bandit_data = json.load(f)

                for issue in bandit_data.get('results', []):
                    vuln = Vulnerability(
                        id=f"BANDIT-{issue['test_id']}",
                        title=issue['test_name'],
                        description=issue['issue_text'],
                        severity=self._map_bandit_severity(issue['issue_severity']),
                        cvss_score=None,
                        category="SAST",
                        scanner="Bandit",
                        location=f"{issue['filename']}:{issue['line_number']}",
                        remediation=issue.get('more_info', ''),
                        references=[issue.get('more_info', '')],
                        metadata={"code": issue.get('code', '')}
                    )
                    vulnerabilities.append(vuln)

        except Exception as e:
            self.logger.error(f"Bandit scan failed: {e}")

        return vulnerabilities

    async def _run_semgrep_scan(self) -> List[Vulnerability]:
        """Run Semgrep security scan"""
        vulnerabilities = []
        try:
            result = subprocess.run([
                'semgrep', '--config=auto', '--json', '--output=/tmp/semgrep-results.json', 'backend/'
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                with open('/tmp/semgrep-results.json', 'r') as f:
                    semgrep_data = json.load(f)

                for issue in semgrep_data.get('results', []):
                    vuln = Vulnerability(
                        id=f"SEMGREP-{issue['check_id'].replace('.', '-')}",
                        title=issue['message'],
                        description=issue['message'],
                        severity=self._map_semgrep_severity(issue.get('extra', {}).get('severity', 'ERROR')),
                        cvss_score=None,
                        category="SAST",
                        scanner="Semgrep",
                        location=f"{issue['path']}:{issue['start']['line']}",
                        remediation=issue.get('fix', ''),
                        references=[issue.get('documentation_url', '')],
                        metadata={"rule_id": issue['check_id']}
                    )
                    vulnerabilities.append(vuln)

        except Exception as e:
            self.logger.error(f"Semgrep scan failed: {e}")

        return vulnerabilities

    async def run_dast_scan(self) -> SecurityScanResult:
        """Run Dynamic Application Security Testing"""
        self.logger.info("Starting DAST scan")
        start_time = datetime.now()
        vulnerabilities = []

        try:
            # Run OWASP ZAP
            zap_results = await self._run_owasp_zap_scan()
            vulnerabilities.extend(zap_results)

            # Run Nuclei
            nuclei_results = await self._run_nuclei_scan()
            vulnerabilities.extend(nuclei_results)

        except Exception as e:
            self.logger.error(f"DAST scan failed: {e}")

        duration = (datetime.now() - start_time).total_seconds()

        return SecurityScanResult(
            scan_type=ScanType.DAST,
            scanner_name="DAST Suite",
            timestamp=start_time,
            duration=duration,
            vulnerabilities=vulnerabilities,
            metadata={"tools_used": ["owasp_zap", "nuclei"]},
            compliance_status={}
        )

    async def _run_owasp_zap_scan(self) -> List[Vulnerability]:
        """Run OWASP ZAP security scan"""
        vulnerabilities = []
        target_url = self.config["scanners"]["dast"]["target_url"]

        try:
            # Use Docker to run ZAP
            result = subprocess.run([
                'docker', 'run', '--rm',
                '-v', f'{os.getcwd()}:/zap/wrk/:rw',
                'owasp/zap2docker-stable',
                'zap-baseline.py',
                '-t', target_url,
                '-g', '/zap/wrk/gen.conf',
                '-r', '/tmp/zap-report.html',
                '-J', '/tmp/zap-report.json'
            ], capture_output=True, text=True, timeout=600)

            if os.path.exists('/tmp/zap-report.json'):
                with open('/tmp/zap-report.json', 'r') as f:
                    zap_data = json.load(f)

                for alert in zap_data.get('site', [{}])[0].get('alerts', []):
                    vuln = Vulnerability(
                        id=f"ZAP-{alert['alert']}",
                        title=alert['name'],
                        description=alert['description'],
                        severity=self._map_zap_risk(alert['risk']),
                        cvss_score=None,
                        category="DAST",
                        scanner="OWASP ZAP",
                        location=target_url,
                        remediation=alert.get('solution', ''),
                        references=alert.get('reference', []),
                        metadata={"instances": alert.get('instances', [])}
                    )
                    vulnerabilities.append(vuln)

        except Exception as e:
            self.logger.error(f"OWASP ZAP scan failed: {e}")

        return vulnerabilities

    async def run_dependency_scan(self) -> SecurityScanResult:
        """Run dependency vulnerability scanning"""
        self.logger.info("Starting dependency scan")
        start_time = datetime.now()
        vulnerabilities = []

        try:
            # Run Safety for Python dependencies
            safety_results = await self._run_safety_scan()
            vulnerabilities.extend(safety_results)

            # Run NPM audit for JavaScript dependencies
            npm_results = await self._run_npm_audit()
            vulnerabilities.extend(npm_results)

        except Exception as e:
            self.logger.error(f"Dependency scan failed: {e}")

        duration = (datetime.now() - start_time).total_seconds()

        return SecurityScanResult(
            scan_type=ScanType.DEPENDENCY,
            scanner_name="Dependency Suite",
            timestamp=start_time,
            duration=duration,
            vulnerabilities=vulnerabilities,
            metadata={"tools_used": ["safety", "npm_audit"]},
            compliance_status={}
        )

    async def _run_safety_scan(self) -> List[Vulnerability]:
        """Run Safety dependency check"""
        vulnerabilities = []
        try:
            result = subprocess.run([
                'safety', 'check', '--json', '--output=/tmp/safety-results.json'
            ], capture_output=True, text=True, timeout=180)

            if result.returncode == 0 and os.path.exists('/tmp/safety-results.json'):
                with open('/tmp/safety-results.json', 'r') as f:
                    safety_data = json.load(f)

                for issue in safety_data:
                    vuln = Vulnerability(
                        id=f"SAFETY-{issue['id']}",
                        title=f"Vulnerability in {issue['package']}",
                        description=issue['advisory'],
                        severity=self._map_safety_severity(issue['severity']),
                        cvss_score=issue.get('cvssv3'),
                        category="Dependency",
                        scanner="Safety",
                        location=f"Package: {issue['package']}=={issue['installed_version']}",
                        remediation=f"Update to {issue['fixed_version']}",
                        references=[issue.get('link', '')],
                        metadata={
                            "package": issue['package'],
                            "installed_version": issue['installed_version'],
                            "fixed_version": issue['fixed_version']
                        }
                    )
                    vulnerabilities.append(vuln)

        except Exception as e:
            self.logger.error(f"Safety scan failed: {e}")

        return vulnerabilities

    async def run_secrets_scan(self) -> SecurityScanResult:
        """Run secrets detection scan"""
        self.logger.info("Starting secrets scan")
        start_time = datetime.now()
        vulnerabilities = []

        try:
            # Run Gitleaks
            gitleaks_results = await self._run_gitleaks_scan()
            vulnerabilities.extend(gitleaks_results)

            # Run TruffleHog
            trufflehog_results = await self._run_trufflehog_scan()
            vulnerabilities.extend(trufflehog_results)

        except Exception as e:
            self.logger.error(f"Secrets scan failed: {e}")

        duration = (datetime.now() - start_time).total_seconds()

        return SecurityScanResult(
            scan_type=ScanType.SECRETS,
            scanner_name="Secrets Suite",
            timestamp=start_time,
            duration=duration,
            vulnerabilities=vulnerabilities,
            metadata={"tools_used": ["gitleaks", "trufflehog"]},
            compliance_status={}
        )

    async def run_container_scan(self) -> SecurityScanResult:
        """Run container security scanning"""
        self.logger.info("Starting container scan")
        start_time = datetime.now()
        vulnerabilities = []

        try:
            # Run Trivy for container scanning
            trivy_results = await self._run_trivy_scan()
            vulnerabilities.extend(trivy_results)

        except Exception as e:
            self.logger.error(f"Container scan failed: {e}")

        duration = (datetime.now() - start_time).total_seconds()

        return SecurityScanResult(
            scan_type=ScanType.CONTAINER,
            scanner_name="Container Suite",
            timestamp=start_time,
            duration=duration,
            vulnerabilities=vulnerabilities,
            metadata={"tools_used": ["trivy"]},
            compliance_status={}
        )

    async def run_compliance_scan(self) -> SecurityScanResult:
        """Run healthcare compliance scanning"""
        self.logger.info("Starting compliance scan")
        start_time = datetime.now()
        vulnerabilities = []
        compliance_status = {}

        try:
            # HIPAA Compliance
            hipaa_results = await self._run_hipaa_compliance_check()
            vulnerabilities.extend(hipaa_results["vulnerabilities"])
            compliance_status["HIPAA"] = hipaa_results["compliant"]

            # GDPR Compliance
            gdpr_results = await self._run_gdpr_compliance_check()
            vulnerabilities.extend(gdpr_results["vulnerabilities"])
            compliance_status["GDPR"] = gdpr_results["compliant"]

            # PCI-DSS Compliance
            pci_dss_results = await self._run_pci_dss_compliance_check()
            vulnerabilities.extend(pci_dss_results["vulnerabilities"])
            compliance_status["PCI_DSS"] = pci_dss_results["compliant"]

        except Exception as e:
            self.logger.error(f"Compliance scan failed: {e}")

        duration = (datetime.now() - start_time).total_seconds()

        return SecurityScanResult(
            scan_type=ScanType.COMPLIANCE,
            scanner_name="Compliance Suite",
            timestamp=start_time,
            duration=duration,
            vulnerabilities=vulnerabilities,
            metadata={"frameworks": ["HIPAA", "GDPR", "PCI_DSS"]},
            compliance_status=compliance_status
        )

    async def _run_hipaa_compliance_check(self) -> Dict:
        """Run HIPAA compliance check"""
        try:
            results = self.hipaa_checker.check_compliance()
            vulnerabilities = []

            for violation in results.get("violations", []):
                vuln = Vulnerability(
                    id=f"HIPAA-{violation['rule_id']}",
                    title=violation['title'],
                    description=violation['description'],
                    severity=SecurityLevel.HIGH if violation['critical'] else SecurityLevel.MEDIUM,
                    cvss_score=None,
                    category="HIPAA Compliance",
                    scanner="HIPAA Checker",
                    location=violation.get('location', ''),
                    remediation=violation.get('remediation', ''),
                    references=violation.get('references', []),
                    metadata={"rule_id": violation['rule_id'], "critical": violation['critical']}
                )
                vulnerabilities.append(vuln)

            return {
                "vulnerabilities": vulnerabilities,
                "compliant": len(violations) == 0
            }

        except Exception as e:
            self.logger.error(f"HIPAA compliance check failed: {e}")
            return {"vulnerabilities": [], "compliant": False}

    async def run_infrastructure_scan(self) -> SecurityScanResult:
        """Run infrastructure security scanning"""
        self.logger.info("Starting infrastructure scan")
        start_time = datetime.now()
        vulnerabilities = []

        try:
            # AWS Security scanning
            aws_results = await self._run_aws_security_scan()
            vulnerabilities.extend(aws_results)

            # Kubernetes security scanning
            if hasattr(self, 'k8s_client'):
                k8s_results = await self._run_kubernetes_security_scan()
                vulnerabilities.extend(k8s_results)

        except Exception as e:
            self.logger.error(f"Infrastructure scan failed: {e}")

        duration = (datetime.now() - start_time).total_seconds()

        return SecurityScanResult(
            scan_type=ScanType.INFRASTRUCTURE,
            scanner_name="Infrastructure Suite",
            timestamp=start_time,
            duration=duration,
            vulnerabilities=vulnerabilities,
            metadata={"tools_used": ["aws_scanner", "kubernetes_scanner"]},
            compliance_status={}
        )

    async def _run_aws_security_scan(self) -> List[Vulnerability]:
        """Run AWS security scanning"""
        vulnerabilities = []

        try:
            # Check for unencrypted S3 buckets
            buckets = self.s3_client.list_buckets()
            for bucket in buckets['Buckets']:
                try:
                    encryption = self.s3_client.get_bucket_encryption(Bucket=bucket['Name'])
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                        vuln = Vulnerability(
                            id=f"AWS-S3-UNENCRYPTED-{bucket['Name']}",
                            title=f"Unencrypted S3 Bucket: {bucket['Name']}",
                            description="S3 bucket is not encrypted",
                            severity=SecurityLevel.HIGH,
                            cvss_score=7.5,
                            category="AWS Security",
                            scanner="AWS Scanner",
                            location=f"S3 Bucket: {bucket['Name']}",
                            remediation="Enable default encryption for the S3 bucket",
                            references=["https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html"],
                            metadata={"bucket_name": bucket['Name']}
                        )
                        vulnerabilities.append(vuln)

            # Check for open security groups
            security_groups = self.ec2_client.describe_security_groups()
            for sg in security_groups['SecurityGroups']:
                for rule in sg['IpPermissions']:
                    if rule.get('IpRanges'):
                        for ip_range in rule['IpRanges']:
                            if ip_range['CidrIp'] == '0.0.0.0/0':
                                vuln = Vulnerability(
                                    id=f"AWS-SG-OPEN-{sg['GroupId']}",
                                    title=f"Open Security Group: {sg['GroupName']}",
                                    description=f"Security group allows inbound traffic from 0.0.0.0/0 on port {rule.get('FromPort', 'all')}",
                                    severity=SecurityLevel.HIGH,
                                    cvss_score=8.5,
                                    category="AWS Security",
                                    scanner="AWS Scanner",
                                    location=f"Security Group: {sg['GroupId']} ({sg['GroupName']})",
                                    remediation="Restrict inbound access to specific IP addresses",
                                    references=["https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules.html"],
                                    metadata={"security_group_id": sg['GroupId'], "port": rule.get('FromPort')}
                                )
                                vulnerabilities.append(vuln)

        except Exception as e:
            self.logger.error(f"AWS security scan failed: {e}")

        return vulnerabilities

    def generate_security_report(self, scan_results: List[SecurityScanResult]) -> Dict:
        """Generate comprehensive security report"""
        self.logger.info("Generating security report")

        # Aggregate all vulnerabilities
        all_vulnerabilities = []
        for result in scan_results:
            all_vulnerabilities.extend(result.vulnerabilities)

        # Calculate statistics
        total_vulnerabilities = len(all_vulnerabilities)
        severity_counts = {}
        for vuln in all_vulnerabilities:
            severity = vuln.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Check thresholds
        thresholds = self.config["thresholds"]
        critical_violations = severity_counts.get("critical", 0)
        high_violations = severity_counts.get("high", 0)
        medium_violations = severity_counts.get("medium", 0)

        security_gate_status = {
            "passed": True,
            "critical_threshold_met": critical_violations <= thresholds["critical"],
            "high_threshold_met": high_violations <= thresholds["high"],
            "medium_threshold_met": medium_violations <= thresholds["medium"],
            "recommendations": []
        }

        # Generate recommendations
        if critical_violations > 0:
            security_gate_status["recommendations"].append(
                f"🚨 {critical_violations} critical vulnerabilities must be fixed immediately"
            )

        if high_vulnerabilities > 0:
            security_gate_status["recommendations"].append(
                f"⚠️ {high_violations} high vulnerabilities should be prioritized"
            )

        if medium_violations > 0:
            security_gate_status["recommendations"].append(
                f"📋 {medium_violations} medium vulnerabilities should be addressed"
            )

        # Compliance summary
        compliance_summary = {}
        for result in scan_results:
            if result.compliance_status:
                compliance_summary.update(result.compliance_status)

        report = {
            "scan_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_scans": len(scan_results),
                "scan_duration_seconds": sum(r.duration for r in scan_results),
                "scanner_version": "HMS Enterprise Security Scanner v1.0"
            },
            "vulnerability_summary": {
                "total_vulnerabilities": total_vulnerabilities,
                "severity_breakdown": severity_counts,
                "top_vulnerabilities": self._get_top_vulnerabilities(all_vulnerabilities, 10)
            },
            "security_gate": security_gate_status,
            "compliance_summary": compliance_summary,
            "scan_results": [self._serialize_scan_result(result) for result in scan_results],
            "executive_summary": self._generate_executive_summary(
                total_vulnerabilities, severity_counts, compliance_summary
            )
        }

        return report

    def _get_top_vulnerabilities(self, vulnerabilities: List[Vulnerability], limit: int) -> List[Dict]:
        """Get top vulnerabilities by severity"""
        severity_order = {
            SecurityLevel.CRITICAL: 4,
            SecurityLevel.HIGH: 3,
            SecurityLevel.MEDIUM: 2,
            SecurityLevel.LOW: 1,
            SecurityLevel.INFO: 0
        }

        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda x: severity_order.get(x.severity, 0),
            reverse=True
        )

        return [asdict(vuln) for vuln in sorted_vulns[:limit]]

    def _generate_executive_summary(self, total_vulns: int, severity_counts: Dict, compliance_summary: Dict) -> str:
        """Generate executive summary of security posture"""
        summary_lines = []
        summary_lines.append("# 🛡️ HMS Security Scan Executive Summary")
        summary_lines.append(f"**Scan Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")

        # Overall risk assessment
        critical_count = severity_counts.get("critical", 0)
        high_count = severity_counts.get("high", 0)

        if critical_count > 0:
            risk_level = "🔴 CRITICAL"
        elif high_count > 0:
            risk_level = "🟠 HIGH"
        elif total_vulns > 0:
            risk_level = "🟡 MEDIUM"
        else:
            risk_level = "🟢 LOW"

        summary_lines.append(f"**Overall Risk Level:** {risk_level}")
        summary_lines.append("")

        # Vulnerability summary
        summary_lines.append("## 📊 Vulnerability Summary")
        summary_lines.append(f"- **Total Vulnerabilities:** {total_vulns}")
        summary_lines.append(f"- **Critical:** {critical_count}")
        summary_lines.append(f"- **High:** {high_count}")
        summary_lines.append(f"- **Medium:** {severity_counts.get('medium', 0)}")
        summary_lines.append(f"- **Low:** {severity_counts.get('low', 0)}")
        summary_lines.append("")

        # Compliance status
        summary_lines.append("## 📋 Compliance Status")
        for framework, status in compliance_summary.items():
            status_icon = "✅" if status else "❌"
            summary_lines.append(f"- **{framework}:** {status_icon} {'Compliant' if status else 'Non-compliant'}")
        summary_lines.append("")

        # Key findings
        summary_lines.append("## 🔍 Key Findings")
        if critical_count > 0:
            summary_lines.append(f"- {critical_count} critical vulnerabilities require immediate attention")
        if high_count > 0:
            summary_lines.append(f"- {high_count} high-severity issues should be prioritized")

        # Recommendations
        summary_lines.append("## 🎯 Recommendations")
        summary_lines.append("1. **Immediate Actions:** Fix all critical vulnerabilities")
        summary_lines.append("2. **Short-term:** Address high-severity issues within 30 days")
        summary_lines.append("3. **Medium-term:** Implement regular security scanning")
        summary_lines.append("4. **Long-term:** Establish security champions program")

        return "\n".join(summary_lines)

    def _serialize_scan_result(self, result: SecurityScanResult) -> Dict:
        """Serialize scan result for JSON output"""
        return {
            "scan_type": result.scan_type.value,
            "scanner_name": result.scanner_name,
            "timestamp": result.timestamp.isoformat(),
            "duration_seconds": result.duration,
            "vulnerability_count": len(result.vulnerabilities),
            "compliance_status": result.compliance_status,
            "metadata": result.metadata
        }

    def _map_bandit_severity(self, severity: str) -> SecurityLevel:
        """Map Bandit severity to SecurityLevel"""
        mapping = {
            "HIGH": SecurityLevel.HIGH,
            "MEDIUM": SecurityLevel.MEDIUM,
            "LOW": SecurityLevel.LOW
        }
        return mapping.get(severity.upper(), SecurityLevel.INFO)

    def _map_semgrep_severity(self, severity: str) -> SecurityLevel:
        """Map Semgrep severity to SecurityLevel"""
        mapping = {
            "ERROR": SecurityLevel.HIGH,
            "WARNING": SecurityLevel.MEDIUM,
            "INFO": SecurityLevel.INFO
        }
        return mapping.get(severity.upper(), SecurityLevel.INFO)

    def _map_zap_risk(self, risk: str) -> SecurityLevel:
        """Map ZAP risk to SecurityLevel"""
        mapping = {
            "High": SecurityLevel.HIGH,
            "Medium": SecurityLevel.MEDIUM,
            "Low": SecurityLevel.LOW,
            "Informational": SecurityLevel.INFO
        }
        return mapping.get(risk, SecurityLevel.INFO)

    def _map_safety_severity(self, severity: str) -> SecurityLevel:
        """Map Safety severity to SecurityLevel"""
        mapping = {
            "CRITICAL": SecurityLevel.CRITICAL,
            "HIGH": SecurityLevel.HIGH,
            "MEDIUM": SecurityLevel.MEDIUM,
            "LOW": SecurityLevel.LOW
        }
        return mapping.get(severity.upper(), SecurityLevel.INFO)

async def main():
    """Main function to run security scanner"""
    import argparse

    parser = argparse.ArgumentParser(description='HMS Enterprise Security Scanner')
    parser.add_argument('--config', '-c', default='devops/security/security-config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--output', '-o', default='security-report.json',
                       help='Output file for security report')
    parser.add_argument('--scan-type', choices=['comprehensive', 'sast', 'dast', 'compliance'],
                       default='comprehensive', help='Type of scan to run')
    parser.add_argument('--generate-report', action='store_true',
                       help='Generate detailed security report')

    args = parser.parse_args()

    # Initialize scanner
    scanner = HMSSecurityScanner(args.config)

    # Run scans
    if args.scan_type == 'comprehensive':
        results = await scanner.run_comprehensive_scan()
    elif args.scan_type == 'sast':
        results = [await scanner.run_sast_scan()]
    elif args.scan_type == 'dast':
        results = [await scanner.run_dast_scan()]
    elif args.scan_type == 'compliance':
        results = [await scanner.run_compliance_scan()]

    # Generate report
    report = scanner.generate_security_report(results)

    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"🛡️ Security scan completed. Report saved to {args.output}")

    # Print summary
    print(f"\n📊 Scan Summary:")
    print(f"Total vulnerabilities: {report['vulnerability_summary']['total_vulnerabilities']}")
    print(f"Critical: {report['vulnerability_summary']['severity_breakdown'].get('critical', 0)}")
    print(f"High: {report['vulnerability_summary']['severity_breakdown'].get('high', 0)}")
    print(f"Security Gate: {'✅ PASSED' if report['security_gate']['passed'] else '❌ FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())