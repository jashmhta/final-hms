#!/usr/bin/env python3
"""
Security Fixes Priority Script for HMS Enterprise
Identifies and prioritizes security vulnerabilities across the codebase.
"""

import ast
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class SecurityVulnerabilityScanner:
    def __init__(self):
        self.vulnerabilities = []
        self.critical_patterns = {
            "hardcoded_passwords": [
                r'password\s*=\s*["\'][^"\']{1,10}["\']',
                r'secret\s*=\s*["\'][^"\']{1,10}["\']',
                r'api_key\s*=\s*["\'][^"\']{1,10}["\']',
            ],
            "default_credentials": [
                r"POSTGRES_PASSWORD\s*=\s*password",
                r"DB_PASSWORD\s*=\s*hms",
                r"ROOT_PASSWORD\s*=\s*root",
            ],
            "debug_mode": [
                r"DEBUG\s*=\s*True",
                r"--debug",
            ],
            "insecure_ciphers": [
                r"MD5",
                r"SHA1",
                r"DES",
            ],
            "sql_injection": [
                r"\.execute\([^)]*\%\s*[^)]*\)",
                r"\.raw\(",
            ],
            "xss_vulnerable": [
                r"mark_safe",
                r"|safe",
            ],
        }

    def scan_file(self, file_path: Path) -> List[Dict]:
        """Scan a single file for security vulnerabilities."""
        vulnerabilities = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
        except (UnicodeDecodeError, PermissionError):
            return vulnerabilities

        for vuln_type, patterns in self.critical_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    line_num = content[: match.start()].count("\n") + 1
                    line_content = lines[line_num - 1].strip()

                    severity = self._determine_severity(vuln_type, line_content)

                    vulnerabilities.append(
                        {
                            "file": str(file_path),
                            "line": line_num,
                            "type": vuln_type,
                            "severity": severity,
                            "content": line_content,
                            "pattern": pattern,
                            "recommendation": self._get_recommendation(vuln_type),
                        }
                    )

        return vulnerabilities

    def _determine_severity(self, vuln_type: str, content: str) -> str:
        """Determine severity based on vulnerability type and content."""
        critical_types = ["hardcoded_passwords", "default_credentials"]
        high_types = ["debug_mode", "insecure_ciphers"]
        medium_types = ["sql_injection", "xss_vulnerable"]

        if vuln_type in critical_types:
            return "CRITICAL"
        elif vuln_type in high_types:
            return "HIGH"
        elif vuln_type in medium_types:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_recommendation(self, vuln_type: str) -> str:
        """Get recommendation for vulnerability type."""
        recommendations = {
            "hardcoded_passwords": "Use environment variables or secret management",
            "default_credentials": "Change default passwords immediately",
            "debug_mode": "Disable DEBUG mode in production",
            "insecure_ciphers": "Use secure encryption algorithms (AES-256, SHA-256)",
            "sql_injection": "Use parameterized queries or ORM",
            "xss_vulnerable": "Use proper output encoding and CSP headers",
        }
        return recommendations.get(vuln_type, "Review security implications")

    def scan_directory(self, directory: str) -> List[Dict]:
        """Scan entire directory for vulnerabilities."""
        vulnerabilities = []

        skip_patterns = [
            ".git",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            "migrations",
            "static",
            "media",
            "venv",
            "env",
        ]

        for root, dirs, files in os.walk(directory):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if not any(skip in d for skip in skip_patterns)]

            for file in files:
                if file.endswith(
                    (".py", ".yml", ".yaml", ".json", ".env", ".js", ".ts")
                ):
                    file_path = Path(root) / file
                    vulnerabilities.extend(self.scan_file(file_path))

        return vulnerabilities

    def check_dependencies(self) -> List[Dict]:
        """Check for vulnerable dependencies."""
        vulnerabilities = []

        try:
            # Check if safety is available
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                try:
                    safety_report = json.loads(result.stdout)
                    for vuln in safety_report:
                        vulnerabilities.append(
                            {
                                "type": "vulnerable_dependency",
                                "severity": "HIGH",
                                "package": vuln.get("package", "unknown"),
                                "vulnerable_version": vuln.get(
                                    "installed_version", "unknown"
                                ),
                                "fixed_version": vuln.get("fixed_version", "unknown"),
                                "cve_id": vuln.get("id", "unknown"),
                                "recommendation": f'Update {vuln.get("package")} to {vuln.get("fixed_version")}',
                            }
                        )
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Safety not installed, skip dependency check
            pass

        return vulnerabilities

    def prioritize_fixes(self, vulnerabilities: List[Dict]) -> Dict:
        """Prioritize vulnerabilities for fixing."""
        prioritized = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        # Group by severity
        for vuln in vulnerabilities:
            prioritized[vuln["severity"].lower()].append(vuln)

        # Sort critical by impact (hardcoded credentials first)
        prioritized["critical"].sort(
            key=lambda x: (
                0 if "password" in x["content"].lower() else 1,
                0 if "secret" in x["content"].lower() else 1,
                x["file"],
            )
        )

        return prioritized

    def generate_fix_commands(self, vulnerabilities: List[Dict]) -> List[str]:
        """Generate commands to fix vulnerabilities."""
        commands = []

        for vuln in vulnerabilities:
            if vuln["type"] == "hardcoded_passwords":
                commands.append(
                    f"sed -i 's/{vuln['content']}/${{ENV_VAR}}/g' {vuln['file']}"
                )
            elif vuln["type"] == "default_credentials":
                commands.append(f"# Fix default credentials in {vuln['file']}")
                commands.append(f"# Line {vuln['line']}: {vuln['content']}")
            elif vuln["type"] == "debug_mode":
                commands.append(
                    f"sed -i 's/DEBUG = True/DEBUG = False/g' {vuln['file']}"
                )

        return commands

    def run_scan(self, output_file: str = None):
        """Run complete security scan."""
        print("🔍 Starting security vulnerability scan...")

        # Scan codebase
        vulnerabilities = self.scan_directory(".")

        # Check dependencies
        vulnerabilities.extend(self.check_dependencies())

        # Prioritize fixes
        prioritized = self.prioritize_fixes(vulnerabilities)

        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_vulnerabilities": len(vulnerabilities),
            "summary": {
                "critical": len(prioritized["critical"]),
                "high": len(prioritized["high"]),
                "medium": len(prioritized["medium"]),
                "low": len(prioritized["low"]),
            },
            "prioritized_vulnerabilities": prioritized,
            "fix_commands": self.generate_fixes(
                prioritized["critical"] + prioritized["high"]
            ),
        }

        # Print summary
        print("\n📊 Security Scan Summary:")
        print(f"   Critical: {report['summary']['critical']}")
        print(f"   High: {report['summary']['high']}")
        print(f"   Medium: {report['summary']['medium']}")
        print(f"   Low: {report['summary']['low']}")
        print(f"   Total: {report['total_vulnerabilities']}")

        if report["summary"]["critical"] > 0:
            print("\n🚨 CRITICAL VULNERABILITIES FOUND:")
            for vuln in prioritized["critical"][:5]:  # Show first 5
                print(f"   - {vuln['file']}:{vuln['line']} - {vuln['content']}")

        # Save report
        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Detailed report saved to: {output_file}")

        return report

    def generate_fixes(self, vulnerabilities: List[Dict]) -> List[str]:
        """Generate fix commands for vulnerabilities."""
        fixes = []

        for vuln in vulnerabilities[:10]:  # Top 10 fixes
            fixes.append(f"# Fix: {vuln['type']} in {vuln['file']}")
            if vuln["type"] == "hardcoded_passwords":
                fixes.append(
                    f"sed -i 's/{vuln['content'].split('=')[1]}/${{SECRET_NAME}}/g' {vuln['file']}"
                )
            elif vuln["type"] == "default_credentials":
                fixes.append(f"# Replace default credential at line {vuln['line']}")

        return fixes


def main():
    """Main function to run security scan."""
    scanner = SecurityVulnerabilityScanner()

    # Run scan
    report = scanner.run_scan("security-scan-report.json")

    # Generate priority fix list
    if report["summary"]["critical"] > 0 or report["summary"]["high"] > 0:
        print("\n🔧 PRIORITY FIXES:")
        for i, fix in enumerate(report["fix_commands"][:5], 1):
            print(f"{i}. {fix}")

        print("\n💡 Next Steps:")
        print("1. Review critical vulnerabilities immediately")
        print("2. Apply fixes in order of priority")
        print("3. Run scan again after fixes")
        print("4. Implement continuous security scanning")
    else:
        print("\n✅ No critical or high severity vulnerabilities found!")


if __name__ == "__main__":
    main()
