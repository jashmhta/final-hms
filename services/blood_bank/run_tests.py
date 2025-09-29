"""
run_tests module
"""

import subprocess
import sys


def run_command(command, cwd=None):
    try:
        if isinstance(command, str):
            result = subprocess.run(
                command, shell=False, capture_output=True, text=True, cwd=cwd
            )
        else:
            result = subprocess.run(
                command, shell=False, capture_output=True, text=True, cwd=cwd
            )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


print("Testing Blood Bank Service Implementation...")
required_files = [
    "Dockerfile",
    "requirements.txt",
    "models.py",
    "schemas.py",
    "crud.py",
    "main.py",
    "database.py",
    "tests/test_blood_bank.py",
    "alembic.ini",
    "docker-compose.yml",
    "k8s/deployment.yaml",
    "README.md",
]
all_files_exist = True
for file in required_files:
    success, stdout, stderr = run_command(f"test -f {file}")
    if not success:
        print(f"❌ Missing file: {file}")
        all_files_exist = False
    else:
        print(f"✅ File exists: {file}")
print(f"\nFile completeness: {'✅ Complete' if all_files_exist else '❌ Incomplete'}")
print("\nTesting Python syntax...")
syntax_files = ["models.py", "schemas.py", "crud.py", "main.py", "database.py"]
all_syntax_ok = True
for file in syntax_files:
    success, stdout, stderr = run_command(["python", "-m", "py_compile", file])
    if success:
        print(f"✅ Syntax OK: {file}")
    else:
        print(f"❌ Syntax error in {file}: {stderr}")
        all_syntax_ok = False
print(f"\nSyntax validation: {'✅ All good' if all_syntax_ok else '❌ Errors found'}")
print("\nRunning basic tests...")
success, stdout, stderr = run_command(
    ["python", "-m", "pytest", "test_blood_bank.py", "-v"], cwd="tests"
)
if success:
    print("✅ Tests passed")
    print(stdout)
else:
    print("❌ Tests failed")
    print(stderr)
print("\n" + "=" * 50)
print("ENTERPRISE-GRADE VALIDATION COMPLETE")
print("=" * 50)
