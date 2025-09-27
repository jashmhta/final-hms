import subprocess
import sys

fixes = [
    "fix_exec_eval.py",
    "fix_subprocess_shell.py",
    "fix_insecure_crypto.py",
    "fix_ftp_usage.py",
    "fix_marshal_deserialization.py",
]
print("Running automated security fixes for HMS Enterprise...")
for fix in fixes:
    print(f"\n=== Running {fix} ===")
    try:
        result = subprocess.run([sys.executable, fix], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"SUCCESS: {fix} completed")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"ERROR in {fix}:")
            print(result.stderr)
    except Exception as e:
        print(f"Exception running {fix}: {e}")
print("\nAll automated fixes completed. Review backups and manual changes required.")
