import os
import re
import shutil
from pathlib import Path


def fix_marshal_to_pickle(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Backup
        backup_path = filepath.with_suffix(".py.backup")
        shutil.copy2(filepath, backup_path)

        # Replace marshal.loads/dumps with json (safer for most cases)
        patterns = [r"marshal\.loads\(", r"marshal\.dumps\("]

        fixed = False
        for pattern in patterns:
            if re.search(pattern, content):
                # Replace with json equivalent
                replacement = pattern.replace("marshal", "json")
                content = re.sub(pattern, replacement, content)
                fixed = True
                print(f"Replaced marshal with json in {filepath}")

        # Add json import if needed
        if "import json" not in content and fixed:
            content = "import json\n" + content

        if fixed:
            with open(filepath, "w") as f:
                f.write(content)
            print(
                f"Fixed marshal deserialization in {filepath} (backup: {backup_path})"
            )
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")


# Process files
root_dir = Path("/root/hms-enterprise-grade/backend")
backend_services = ["appointments", "billing", "patients", "lab", "radiology", "ehr"]

for service in backend_services:
    service_path = root_dir / service
    if service_path.exists():
        for py_file in service_path.rglob("*.py"):
            fix_marshal_to_pickle(py_file)

print("Marshal fix complete")
