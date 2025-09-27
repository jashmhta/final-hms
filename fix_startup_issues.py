"""
fix_startup_issues module
"""

import os
import subprocess
import sys
from pathlib import Path


class StartupFixer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.issues_fixed = 0
    def check_python_version(self):
        print("🐍 Checking Python version...")
        version = sys.version_info
        if version >= (3, 8):
            print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
            return True
        else:
            print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Incompatible (requires 3.8+)")
            return False
    def create_requirements_file(self):
        print("📦 Creating requirements.txt...")
        requirements_content = 
        requirements_file = self.project_root / "requirements.txt"
        with open(requirements_file, 'w') as f:
            f.write(requirements_content)
        print(f"   ✅ Created requirements.txt")
        self.issues_fixed += 1
        return True
    def create_django_setup(self):
        print("🎯 Setting up Django...")
        settings_content = 
        self.backend_dir.mkdir(exist_ok=True)
        settings_file = self.backend_dir / "settings.py"
        with open(settings_file, 'w') as f:
            f.write(settings_content)
        urls_content = 
        urls_file = self.backend_dir / "urls.py"
        with open(urls_file, 'w') as f:
            f.write(urls_content)
        wsgi_content = 
        wsgi_file = self.backend_dir / "wsgi.py"
        with open(wsgi_file, 'w') as f:
            f.write(wsgi_content)
        manage_content = 
        manage_file = self.backend_dir / "manage.py"
        with open(manage_file, 'w') as f:
            f.write(manage_content)
        manage_file.chmod(0o755)
        init_file = self.backend_dir / "__init__.py"
        init_file.touch()
        print(f"   ✅ Created Django setup in {self.backend_dir}")
        self.issues_fixed += 1
        return True
    def create_docker_setup(self):
        print("🐳 Creating Docker setup...")
        dockerfile_content = 
        dockerfile = self.project_root / "Dockerfile"
        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content)
        compose_content = 
        compose_file = self.project_root / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            f.write(compose_content)
        env_content = 
        env_file = self.project_root / ".env"
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"   ✅ Created Docker setup files")
        self.issues_fixed += 1
        return True
    def create_startup_script(self):
        print("🚀 Creating startup script...")
        startup_script = 
        startup_file = self.project_root / "start_hms.sh"
        with open(startup_file, 'w') as f:
            f.write(startup_script)
        startup_file.chmod(0o755)
        print(f"   ✅ Created startup script: start_hms.sh")
        self.issues_fixed += 1
        return True
    def run_complete_fix(self):
        print("🚀 Starting complete startup issues fix...")
        steps = [
            self.check_python_version,
            self.create_requirements_file,
            self.create_django_setup,
            self.create_docker_setup,
            self.create_startup_script
        ]
        for step in steps:
            try:
                step()
            except Exception as e:
                print(f"   ❌ {step.__name__} failed: {e}")
        print(f"\n✅ Startup issues fixing completed!")
        print(f"   Issues fixed: {self.issues_fixed}")
        print(f"   Next steps: Run './start_hms.sh' to start the system")
        return True
if __name__ == "__main__":
    fixer = StartupFixer()
    fixer.run_complete_fix()