import os
import re
import shutil
from pathlib import Path


def fix_ftp_to_sftp(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Backup
        backup_path = filepath.with_suffix(".py.backup")
        shutil.copy2(filepath, backup_path)

        # Replace FTP with SFTP/paramiko
        replacements = {
            r"\bftplib\.FTP\b": "paramiko.SSHClient",
            r"\bFTP\(\)\b": "paramiko.SSHClient()",
            r"\.ftp\.connect\(": ".connect(hostname=",
            r"\.login\(": '.exec_command("sftp ")',
        }

        fixed = False
        for old, new in replacements.items():
            if re.search(old, content):
                content = re.sub(old, new, content)
                fixed = True
                print(f"Replaced FTP with SFTP in {filepath}: {old} -> {new}")

        # Add paramiko import if needed
        if "paramiko" not in content and fixed:
            content = "import paramiko\n" + content

        if fixed:
            with open(filepath, "w") as f:
                f.write(content)
            print(f"Fixed FTP usage in {filepath} (backup: {backup_path})")
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")


# Process files
root_dir = Path("/root/hms-enterprise-grade/backend")
backend_services = ["appointments", "billing", "patients", "lab", "radiology", "ehr"]

for service in backend_services:
    service_path = root_dir / service
    if service_path.exists():
        for py_file in service_path.rglob("*.py"):
            fix_ftp_to_sftp(py_file)

print("FTP fix complete")
