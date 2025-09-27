"""
hipaa_compliance_check module
"""

import ast
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Set

import pandas as pd


class HIPAAComplianceChecker:
    def __init__(self):
        self.violations = []
        self.checks_passed = 0
        self.checks_failed = 0
        self.phi_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",
            r"\b\d{3}-\d{3}-\d{4}\b",
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            r"\b\d{2}/\d{2}/\d{4}\b",
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\b\d{9}\b",
            r"\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b",
            r"\b[A-Z]{2}\d{6}\d?[A-Z\d]?\b",
        ]

    def check_file_permissions(self) -> List[Dict]:
        violations = []
        for root, dirs, files in os.walk("."):
            if ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    stat_info = os.stat(file_path)
                    mode = stat_info.st_mode
                    if mode & 0o002:
                        violations.append(
                            {
                                "type": "file_permissions",
                                "severity": "high",
                                "file": file_path,
                                "issue": "File is world-writable",
                                "recommendation": "Remove world-write permissions: chmod o-w",
                            }
                        )
                    if mode & 0o004 and any(
                        sensitive in file.lower()
                        for sensitive in [
                            "config",
                            "secret",
                            "key",
                            "password",
                            "credential",
                        ]
                    ):
                        violations.append(
                            {
                                "type": "file_permissions",
                                "severity": "high",
                                "file": file_path,
                                "issue": "Sensitive file is world-readable",
                                "recommendation": "Remove world-read permissions: chmod o-r",
                            }
                        )
                except (OSError, PermissionError):
                    continue
        return violations

    def check_encryption_usage(self) -> List[Dict]:
        violations = []
        encryption_keywords = [
            "encrypt",
            "decrypt",
            "cipher",
            "aes",
            "rsa",
            "ssl",
            "tls",
        ]
        for root, dirs, files in os.walk("."):
            skip_dirs = [".git", "venv", "__pycache__", "node_modules", ".pytest_cache"]
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith((".py", ".js", ".ts")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                        credential_patterns = [
                            r'password\s*=\s*[\'"][^\'"]{8,}[\'"]',
                            r'api_key\s*=\s*[\'"][^\'"]{16,}[\'"]',
                            r'secret\s*=\s*[\'"][^\'"]{16,}[\'"]',
                            r'token\s*=\s*[\'"][^\'"]{16,}[\'"]',
                        ]
                        for pattern in credential_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                violations.append(
                                    {
                                        "type": "hardcoded_credentials",
                                        "severity": "critical",
                                        "file": file_path,
                                        "issue": "Potential hardcoded credential found",
                                        "recommendation": "Use environment variables or secret management",
                                    }
                                )
                        if any(
                            keyword in content.lower()
                            for keyword in encryption_keywords
                        ):
                            if (
                                "key" not in content.lower()
                                or "generate" not in content.lower()
                            ):
                                violations.append(
                                    {
                                        "type": "encryption_implementation",
                                        "severity": "high",
                                        "file": file_path,
                                        "issue": "Encryption used without proper key management",
                                        "recommendation": "Implement proper key management and key rotation",
                                    }
                                )
                    except (UnicodeDecodeError, PermissionError):
                        continue
        return violations

    def check_phi_detection(self) -> List[Dict]:
        violations = []
        for root, dirs, files in os.walk("."):
            skip_dirs = [".git", "venv", "__pycache__", "node_modules", ".pytest_cache"]
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".html", ".md", ".txt")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                            lines = content.split("\n")
                            for line_num, line in enumerate(lines, 1):
                                for pattern in self.phi_patterns:
                                    matches = re.finditer(pattern, line)
                                    for match in matches:
                                        violations.append(
                                            {
                                                "type": "phi_detection",
                                                "severity": "high",
                                                "file": file_path,
                                                "line": line_num,
                                                "issue": f"Potential PHI found: {match.group()}",
                                                "recommendation": "Remove or mask PHI from code",
                                            }
                                        )
                    except (UnicodeDecodeError, PermissionError):
                        continue
        return violations

    def check_audit_logging(self) -> List[Dict]:
        violations = []
        audit_log_patterns = ["audit.log", "security.log", "access.log", "hipaa.log"]
        found_audit_logs = False
        for root, dirs, files in os.walk("."):
            for file in files:
                if any(pattern in file.lower() for pattern in audit_log_patterns):
                    found_audit_logs = True
                    break
        if not found_audit_logs:
            violations.append(
                {
                    "type": "audit_logging",
                    "severity": "high",
                    "file": "N/A",
                    "issue": "No audit log files found",
                    "recommendation": "Implement audit logging for all PHI access",
                }
            )
        logging_found = False
        for root, dirs, files in os.walk("."):
            skip_dirs = [".git", "venv", "__pycache__", "node_modules", ".pytest_cache"]
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                            if (
                                "import logging" in content
                                or "from logging import" in content
                            ) and any(
                                keyword in content.lower()
                                for keyword in ["audit", "security", "access"]
                            ):
                                logging_found = True
                                break
                    except (UnicodeDecodeError, PermissionError):
                        continue
        if not logging_found:
            violations.append(
                {
                    "type": "audit_logging",
                    "severity": "medium",
                    "file": "N/A",
                    "issue": "Audit logging not implemented in code",
                    "recommendation": "Add audit logging for PHI access and modifications",
                }
            )
        return violations

    def check_access_controls(self) -> List[Dict]:
        violations = []
        auth_patterns = [
            "@login_required",
            "@authentication_required",
            "auth_middleware",
            "authenticate",
            "authorization",
        ]
        auth_found = False
        for root, dirs, files in os.walk("."):
            skip_dirs = [".git", "venv", "__pycache__", "node_modules", ".pytest_cache"]
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                            if any(pattern in content for pattern in auth_patterns):
                                auth_found = True
                                break
                    except (UnicodeDecodeError, PermissionError):
                        continue
        if not auth_found:
            violations.append(
                {
                    "type": "access_controls",
                    "severity": "high",
                    "file": "N/A",
                    "issue": "Authentication/authorization controls not found",
                    "recommendation": "Implement proper authentication and authorization",
                }
            )
        return violations

    def check_data_retention(self) -> List[Dict]:
        violations = []
        retention_keywords = [
            "data retention",
            "retention policy",
            "record retention",
            "data disposal",
            "data deletion",
        ]
        retention_found = False
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.lower().endswith((".md", ".txt", ".doc", ".docx")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                            if any(
                                keyword in content.lower()
                                for keyword in retention_keywords
                            ):
                                retention_found = True
                                break
                    except (UnicodeDecodeError, PermissionError):
                        continue
        if not retention_found:
            violations.append(
                {
                    "type": "data_retention",
                    "severity": "medium",
                    "file": "N/A",
                    "issue": "Data retention policy not documented",
                    "recommendation": "Document and implement data retention policies",
                }
            )
        return violations

    def check_incident_response(self) -> List[Dict]:
        violations = []
        incident_keywords = [
            "incident response",
            "security incident",
            "breach notification",
            "incident management",
            "security breach",
        ]
        incident_found = False
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.lower().endswith((".md", ".txt", ".doc", ".docx")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                            if any(
                                keyword in content.lower()
                                for keyword in incident_keywords
                            ):
                                incident_found = True
                                break
                    except (UnicodeDecodeError, PermissionError):
                        continue
        if not incident_found:
            violations.append(
                {
                    "type": "incident_response",
                    "severity": "medium",
                    "file": "N/A",
                    "issue": "Incident response procedures not documented",
                    "recommendation": "Document incident response procedures",
                }
            )
        return violations

    def generate_compliance_report(self) -> Dict[str, Any]:
        print("Running HIPAA compliance checks...")
        check_functions = [
            self.check_file_permissions,
            self.check_encryption_usage,
            self.check_phi_detection,
            self.check_audit_logging,
            self.check_access_controls,
            self.check_data_retention,
            self.check_incident_response,
        ]
        all_violations = []
        for check_func in check_functions:
            violations = check_func()
            all_violations.extend(violations)
        total_checks = len(check_functions)
        passed_checks = total_checks - len(set([v["type"] for v in all_violations]))
        failed_checks = len(set([v["type"] for v in all_violations]))
        violations_by_severity = {}
        for violation in all_violations:
            severity = violation["severity"]
            if severity not in violations_by_severity:
                violations_by_severity[severity] = []
            violations_by_severity[severity].append(violation)
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_violations": len(all_violations),
            "compliance_score": (passed_checks / total_checks) * 100,
            "checks_passed": passed_checks,
            "checks_failed": failed_checks,
            "violations_by_severity": violations_by_severity,
            "all_violations": all_violations,
            "recommendations": self.generate_recommendations(all_violations),
        }
        return report

    def generate_recommendations(self, violations: List[Dict]) -> List[str]:
        recommendations = []
        critical_issues = [v for v in violations if v["severity"] == "critical"]
        if critical_issues:
            recommendations.append(
                "🔴 CRITICAL: Address all critical severity violations immediately"
            )
        high_issues = [v for v in violations if v["severity"] == "high"]
        if high_issues:
            recommendations.append(
                "🟠 HIGH: Address high severity violations within 30 days"
            )
        medium_issues = [v for v in violations if v["severity"] == "medium"]
        if medium_issues:
            recommendations.append(
                "🟡 MEDIUM: Address medium severity violations within 90 days"
            )
        violation_types = set([v["type"] for v in violations])
        if "hardcoded_credentials" in violation_types:
            recommendations.append(
                "🔑 Implement proper secret management and remove hardcoded credentials"
            )
        if "phi_detection" in violation_types:
            recommendations.append(
                "🏥 Remove or properly mask all PHI from code and documentation"
            )
        if "audit_logging" in violation_types:
            recommendations.append(
                "📋 Implement comprehensive audit logging for all PHI access"
            )
        if "access_controls" in violation_types:
            recommendations.append(
                "🔒 Implement proper authentication and authorization controls"
            )
        if "encryption_implementation" in violation_types:
            recommendations.append("🔐 Implement proper encryption with key management")
        return recommendations

    def generate_html_report(self, report: Dict[str, Any]) -> str:
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>HIPAA Compliance Report</title>
        </head>
        <body>
            <h1>HIPAA Compliance Report</h1>
            <div>{violation_rows}</div>
            <ul>{recommendation_items}</ul>
        </body>
        </html>
        """
        violation_rows = ""
        for violation in report["all_violations"]:
            row_html = f"<p>{violation}</p>"
            violation_rows += row_html
        recommendation_items = ""
        for rec in report["recommendations"]:
            recommendation_items += f"<li>{rec}</li>"
        critical_count = len(report["violations_by_severity"].get("critical", []))
        high_count = len(report["violations_by_severity"].get("high", []))
        medium_count = len(report["violations_by_severity"].get("medium", []))
        low_count = len(report["violations_by_severity"].get("low", []))
        total_checks = report["checks_passed"] + report["checks_failed"]
        return html_template.format(
            timestamp=report["timestamp"],
            compliance_score=report["compliance_score"],
            checks_passed=report["checks_passed"],
            total_checks=total_checks,
            total_violations=report["total_violations"],
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            violation_rows=violation_rows,
            recommendation_items=recommendation_items,
        )

    def run_compliance_check(self):
        print("Starting HIPAA compliance validation...")
        report = self.generate_compliance_report()
        html_content = self.generate_html_report(report)
        with open("hipaa-compliance-report.html", "w") as f:
            f.write(html_content)
        with open("hipaa-compliance-report.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"HIPAA compliance report generated:")
        print(f"- HTML Report: hipaa-compliance-report.html")
        print(f"- JSON Report: hipaa-compliance-report.json")
        print(f"- Compliance Score: {report['compliance_score']:.1f}%")
        print(f"- Total Violations: {report['total_violations']}")
        if report["violations_by_severity"].get("critical"):
            print("🔴 Critical HIPAA violations found - immediate action required")
            exit(1)
        elif report["violations_by_severity"].get("high"):
            print("🟠 High severity violations found - attention required")
            exit(1)
        else:
            print("✅ No critical or high severity violations found")
            exit(0)


def main():
    checker = HIPAAComplianceChecker()
    checker.run_compliance_check()


if __name__ == "__main__":
    main()
