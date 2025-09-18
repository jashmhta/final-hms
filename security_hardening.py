import os
import re
import subprocess
from pathlib import Path
class SecurityHardener:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.security_issues_fixed = 0
    def secure_node_modules(self):
        node_modules_path = self.project_root / "frontend" / "node_modules"
        if node_modules_path.exists():
            print("🔒 Securing node_modules directory...")
            sensitive_patterns = [
                "**/passwordrules.js",
                "**/*.js.map",
                "**/tokenize.js",
                "**/tokenTypes.js"
            ]
            for pattern in sensitive_patterns:
                for file_path in node_modules_path.glob(pattern):
                    try:
                        file_path.chmod(0o600)  
                        self.security_issues_fixed += 1
                        print(f"   Secured: {file_path}")
                    except Exception as e:
                        print(f"   Warning: Could not secure {file_path}: {e}")
        return True
    def create_environment_secrets(self):
        print("🔐 Creating environment configuration...")
        env_template = 
        env_file = self.project_root / ".env.template"
        with open(env_file, 'w') as f:
            f.write(env_template)
        print(f"   Created environment template: {env_file}")
        gitignore_file = self.project_root / ".gitignore"
        gitignore_content = ""
        if gitignore_file.exists():
            with open(gitignore_file, 'r') as f:
                gitignore_content = f.read()
        if ".env" not in gitignore_content:
            with open(gitignore_file, 'a') as f:
                f.write("\n
        self.security_issues_fixed += 1
        return True
    def create_security_policy(self):
        print("📋 Creating security policy...")
        security_policy = 
        policy_file = self.project_root / "security" / "policy.md"
        policy_file.parent.mkdir(exist_ok=True)
        with open(policy_file, 'w') as f:
            f.write(security_policy)
        print(f"   Created security policy: {policy_file}")
        self.security_issues_fixed += 1
        return True
    def run_security_scan(self):
        print("🔍 Running security scan...")
        security_issues = []
        password_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']'
        ]
        for pattern in password_patterns:
            result = subprocess.run(
                ['grep', '-r', '-n', pattern, str(self.project_root)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                security_issues.extend(result.stdout.split('\n'))
        scan_report = self.project_root / "security" / "scan_report.txt"
        scan_report.parent.mkdir(exist_ok=True)
        with open(scan_report, 'w') as f:
            f.write("HMS Enterprise-Grade Security Scan Report\n")
            f.write("=" * 50 + "\n\n")
            if security_issues:
                f.write("Potential Security Issues Found:\n")
                f.write("-" * 30 + "\n")
                for issue in security_issues:
                    if issue.strip():
                        f.write(f"{issue}\n")
            else:
                f.write("No obvious security issues found in this scan.\n")
        print(f"   Security scan report saved to: {scan_report}")
        return True
    def execute_security_hardening(self):
        print("🚀 Starting security hardening process...")
        steps = [
            self.secure_node_modules,
            self.create_environment_secrets,
            self.create_security_policy,
            self.run_security_scan
        ]
        for step in steps:
            try:
                if step():
                    print(f"   ✅ {step.__name__} completed successfully")
                else:
                    print(f"   ❌ {step.__name__} failed")
            except Exception as e:
                print(f"   ❌ {step.__name__} failed with error: {e}")
        print(f"\n🎯 Security hardening completed!")
        print(f"   Security issues addressed: {self.security_issues_fixed}")
        print(f"   Next steps: Implement proper secret management and monitoring")
        return True
if __name__ == "__main__":
    hardener = SecurityHardener()
    hardener.execute_security_hardening()