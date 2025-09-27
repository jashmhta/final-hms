"""
fix_insecure_crypto module
"""

import os
import re
import shutil
from pathlib import Path


def fix_crypto_algorithms(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()
        backup_path = filepath.with_suffix(".py.backup")
        shutil.copy2(filepath, backup_path)
        replacements = {
            r"\bMD5\b": "SHA256",
            r"\bmd5\b": "sha256",
            r"\bSHA1\b": "SHA256",
            r"\bsha1\b": "sha256",
            r"\bDES\b": "AES",
            r"\b3DES\b": "AES",
            r"RC4": "AES",
        }
        fixed = False
        for old, new in replacements.items():
            if re.search(old, content):
                content = re.sub(old, new, content)
                fixed = True
                print(f"Replaced {old} with {new} in {filepath}")
        crypto_imports = [
            r"from hashlib import md5",
            r"from Crypto.Cipher import DES",
            r"from Crypto.Cipher import _raw_des",
        ]
        for import_pattern in crypto_imports:
            if re.search(import_pattern, content):
                content = re.sub(
                    import_pattern,
                    f"
                    content,
                )
                fixed = True
                print(f"Marked insecure import for manual review: {import_pattern}")
        if fixed:
            with open(filepath, "w") as f:
                f.write(content)
            print(f"Fixed crypto in {filepath} (backup: {backup_path})")
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
root_dir = Path("/root/hms-enterprise-grade/backend")
backend_services = ["appointments", "billing", "patients", "lab", "radiology", "ehr"]
for service in backend_services:
    service_path = root_dir / service
    if service_path.exists():
        for py_file in service_path.rglob("*.py"):
            fix_crypto_algorithms(py_file)
print("Crypto fix complete")