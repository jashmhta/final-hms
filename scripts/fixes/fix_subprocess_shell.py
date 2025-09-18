import ast
import os
import re
import shutil
from pathlib import Path
def fix_subprocess_shell(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()
        backup_path = filepath.with_suffix(".py.backup")
        shutil.copy2(filepath, backup_path)
        patterns = [
            r"subprocess\.call\(([^)]*)shell=True([^)]*)\)",
            r"subprocess\.check_call\(([^)]*)shell=True([^)]*)\)",
            r"subprocess\.check_output\(([^)]*)shell=True([^)]*)\)",
            r"subprocess\.Popen\(([^)]*)shell=True([^)]*)\)",
        ]
        fixed = False
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                cmd_part = match[0].strip()
                if "cmd=" not in cmd_part and not cmd_part.startswith("["):
                    new_cmd = f'subprocess.{match[0].split(".")[1].split("(")[0]}([{cmd_part}], shell=False)'
                    content = re.sub(pattern, new_cmd, content, count=1)
                    fixed = True
                    print(f"Fixed shell=True at {filepath}:{match}")
        if fixed:
            with open(filepath, "w") as f:
                f.write(content)
            print(f"Fixed subprocess shell=True in {filepath} (backup: {backup_path})")
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
root_dir = Path("/root/hms-enterprise-grade/backend")
backend_services = ["appointments", "billing", "patients", "lab", "radiology", "ehr"]
for service in backend_services:
    service_path = root_dir / service
    if service_path.exists():
        for py_file in service_path.rglob("*.py"):
            fix_subprocess_shell(py_file)
print("Subprocess shell fix complete")