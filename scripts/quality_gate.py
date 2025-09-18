import subprocess
import sys
def quality_gate():
    checks = [
        ['python', 'manage.py', 'test', '--coverage', '--cov-fail-under=100'],
        ['flake8', '.'],
        ['mypy', '.'],
        ['bandit', '-r', '.'],
        ['safety', 'check']
    ]
    for check in checks:
        result = subprocess.run(check, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Quality gate failed: {' '.join(check)}")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)
    print("All quality gates passed")
if __name__ == "__main__":
    quality_gate()