import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests


class SecurityAuditor:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {},
        }

    def run_all_checks(self):
        print("🔒 Starting Enterprise Security Audit...")
        checks = [
            self.check_dependencies,
            self.check_secrets,
            self.check_permissions,
            self.check_ssl_tls,
            self.check_firewall_rules,
            self.check_container_security,
            self.check_database_security,
            self.check_api_security,
            self.check_authentication_security,
            self.check_authorization_security,
            self.check_data_encryption,
            self.check_audit_logging,
            self.check_rate_limiting,
            self.check_input_validation,
            self.check_error_handling,
            self.generate_report,
        ]
        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"❌ Error in {check.__name__}: {e}")
                self.results["checks"][check.__name__] = {
                    "status": "error",
                    "message": str(e),
                }
        self.generate_summary()
        return self.results

    def check_dependencies(self):
        print("📦 Checking dependencies...")
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                cwd=self.base_path / "backend",
            )
            vulnerabilities = json.loads(result.stdout) if result.stdout else []
            self.results["checks"]["dependencies"] = {
                "status": "pass" if not vulnerabilities else "fail",
                "vulnerabilities_found": len(vulnerabilities),
                "details": vulnerabilities[:10],
            }
        except FileNotFoundError:
            self.results["checks"]["dependencies"] = {
                "status": "warning",
                "message": "Safety tool not installed",
            }

    def check_secrets(self):
        print("🔑 Checking for exposed secrets...")
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
        ]
        findings = []
        for py_file in self.base_path.rglob("*.py"):
            try:
                with open(py_file, "r") as f:
                    content = f.read()
                for pattern in secret_patterns:
                    import re

                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        findings.append(
                            {
                                "file": str(py_file),
                                "pattern": pattern,
                                "matches": len(matches),
                            }
                        )
            except Exception:
                pass
        self.results["checks"]["secrets"] = {
            "status": "pass" if not findings else "fail",
            "findings": findings,
        }

    def check_permissions(self):
        print("🔒 Checking file permissions...")
        sensitive_files = ["settings.py", ".env", "secrets.json", "*.key", "*.pem"]
        issues = []
        for pattern in sensitive_files:
            for file_path in self.base_path.rglob(pattern):
                if file_path.exists():
                    stat = file_path.stat()
                    if stat.st_mode & 0o077:
                        issues.append(
                            {
                                "file": str(file_path),
                                "permissions": oct(stat.st_mode),
                                "issue": "World-readable sensitive file",
                            }
                        )
        self.results["checks"]["permissions"] = {
            "status": "pass" if not issues else "fail",
            "issues": issues,
        }

    def check_ssl_tls(self):
        print("🔐 Checking SSL/TLS configuration...")
        settings_file = self.base_path / "backend" / "hms" / "settings.py"
        ssl_configured = False
        if settings_file.exists():
            with open(settings_file, "r") as f:
                content = f.read()
                if "SECURE_SSL_REDIRECT" in content and "True" in content:
                    ssl_configured = True
        self.results["checks"]["ssl_tls"] = {
            "status": "pass" if ssl_configured else "fail",
            "ssl_redirect_enabled": ssl_configured,
        }

    def check_firewall_rules(self):
        print("🛡️ Checking firewall rules...")
        self.results["checks"]["firewall"] = {
            "status": "warning",
            "message": "Firewall check requires deployment-specific implementation",
        }

    def check_container_security(self):
        print("🐳 Checking container security...")
        dockerfile = self.base_path / "backend" / "Dockerfile"
        issues = []
        if dockerfile.exists():
            with open(dockerfile, "r") as f:
                content = f.read()
            if "USER root" in content or "user root" in content.lower():
                issues.append("Container runs as root user")
            if ":latest" in content:
                issues.append("Uses latest tag instead of specific version")
        self.results["checks"]["containers"] = {
            "status": "pass" if not issues else "fail",
            "issues": issues,
        }

    def check_database_security(self):
        print("🗄️ Checking database security...")
        settings_file = self.base_path / "backend" / "hms" / "settings.py"
        db_secure = True
        issues = []
        if settings_file.exists():
            with open(settings_file, "r") as f:
                content = f.read()
            if "PASSWORD" in content and not content.count("os.getenv"):
                issues.append("Database password may be hardcoded")
            if "sslmode" not in content:
                issues.append("SSL mode not configured for database")
        self.results["checks"]["database"] = {
            "status": "pass" if not issues else "fail",
            "issues": issues,
        }

    def check_api_security(self):
        print("🌐 Checking API security...")
        issues = []
        settings_file = self.base_path / "backend" / "hms" / "settings.py"
        if settings_file.exists():
            with open(settings_file, "r") as f:
                content = f.read()
            if "DEFAULT_AUTHENTICATION_CLASSES" not in content:
                issues.append("No default authentication classes configured")
            if "DEFAULT_PERMISSION_CLASSES" not in content:
                issues.append("No default permission classes configured")
        self.results["checks"]["api_security"] = {
            "status": "pass" if not issues else "fail",
            "issues": issues,
        }

    def check_authentication_security(self):
        print("🔐 Checking authentication security...")
        auth_features = []
        issues = []
        mfa_files = list(self.base_path.rglob("*mfa*"))
        if mfa_files:
            auth_features.append("MFA implemented")
        else:
            issues.append("MFA not implemented")
        if (self.base_path / "backend" / "authentication" / "models.py").exists():
            with open(self.base_path / "backend" / "authentication" / "models.py", "r") as f:
                content = f.read()
                if "PasswordPolicy" in content:
                    auth_features.append("Password policies implemented")
                else:
                    issues.append("Password policies not implemented")
        self.results["checks"]["authentication"] = {
            "status": "pass" if not issues else "warning",
            "features": auth_features,
            "issues": issues,
        }

    def check_authorization_security(self):
        print("🛡️ Checking authorization security...")
        issues = []
        permissions_file = self.base_path / "backend" / "core" / "permissions.py"
        if permissions_file.exists():
            with open(permissions_file, "r") as f:
                content = f.read()
                if "RolePermission" in content:
                    pass
                else:
                    issues.append("Role-based permissions not implemented")
        self.results["checks"]["authorization"] = {
            "status": "pass" if not issues else "fail",
            "issues": issues,
        }

    def check_data_encryption(self):
        print("🔒 Checking data encryption...")
        encryption_features = []
        if (self.base_path / "backend" / "libs" / "encrypted_model_fields").exists():
            encryption_features.append("Encrypted model fields available")
        if (self.base_path / "backend" / "core" / "encryption.py").exists():
            encryption_features.append("Encryption utilities implemented")
        self.results["checks"]["encryption"] = {
            "status": "pass" if encryption_features else "fail",
            "features": encryption_features,
        }

    def check_audit_logging(self):
        print("📝 Checking audit logging...")
        audit_features = []
        if (self.base_path / "backend" / "authentication" / "models.py").exists():
            with open(self.base_path / "backend" / "authentication" / "models.py", "r") as f:
                content = f.read()
                if "SecurityEvent" in content:
                    audit_features.append("Security event logging implemented")
        self.results["checks"]["audit_logging"] = {
            "status": "pass" if audit_features else "fail",
            "features": audit_features,
        }

    def check_rate_limiting(self):
        print("⏱️ Checking rate limiting...")
        rate_limiting_configured = False
        settings_file = self.base_path / "backend" / "hms" / "settings.py"
        if settings_file.exists():
            with open(settings_file, "r") as f:
                content = f.read()
                if "DEFAULT_THROTTLE" in content:
                    rate_limiting_configured = True
        self.results["checks"]["rate_limiting"] = {
            "status": "pass" if rate_limiting_configured else "fail",
            "configured": rate_limiting_configured,
        }

    def check_input_validation(self):
        print("✅ Checking input validation...")
        validation_features = []
        if (self.base_path / "backend" / "core" / "validators.py").exists():
            validation_features.append("Custom validators implemented")
        self.results["checks"]["input_validation"] = {
            "status": "pass" if validation_features else "warning",
            "features": validation_features,
        }

    def check_error_handling(self):
        print("🚨 Checking error handling...")
        error_handling_configured = False
        settings_file = self.base_path / "backend" / "hms" / "settings.py"
        if settings_file.exists():
            with open(settings_file, "r") as f:
                content = f.read()
                if "EXCEPTION_HANDLER" in content:
                    error_handling_configured = True
        self.results["checks"]["error_handling"] = {
            "status": "pass" if error_handling_configured else "warning",
            "configured": error_handling_configured,
        }

    def generate_summary(self):
        checks = self.results["checks"]
        total_checks = len(checks)
        passed = sum(1 for check in checks.values() if check.get("status") == "pass")
        failed = sum(1 for check in checks.values() if check.get("status") == "fail")
        warnings = sum(1 for check in checks.values() if check.get("status") == "warning")
        self.results["summary"] = {
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "pass_rate": (passed / total_checks * 100) if total_checks > 0 else 0,
            "overall_status": "pass" if failed == 0 else "fail",
        }

    def generate_report(self):
        print("📊 Generating security audit report...")
        report_file = self.base_path / "security_audit_report.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"✅ Security audit report saved to {report_file}")
        summary = self.results["summary"]
        print("\n📈 Audit Summary:")
        print(f"   Total Checks: {summary['total_checks']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Warnings: {summary['warnings']}")
        print(".1f")
        print(f"   Overall Status: {'✅ PASS' if summary['overall_status'] == 'pass' else '❌ FAIL'}")


def main():
    base_path = Path(__file__).parent.parent
    auditor = SecurityAuditor(str(base_path))
    results = auditor.run_all_checks()
    if results["summary"]["overall_status"] == "fail":
        sys.exit(1)


if __name__ == "__main__":
    main()
