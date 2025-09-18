import subprocess
import sys
def run_mutation_tests():
    modules = ['backend/users', 'backend/patients', 'backend/billing']
    for module in modules:
        result = subprocess.run(['mutmut', 'run', '--paths-to-mutate', module], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Mutation test failed for {module}")
            sys.exit(1)
    print("All mutation tests passed")
if __name__ == "__main__":
    run_mutation_tests()