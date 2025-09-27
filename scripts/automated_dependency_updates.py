"""
automated_dependency_updates module
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
class DependencyUpdater:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.base_dir = Path(__file__).parent.parent
        self.backup_dir = self.base_dir / 'backups' / 'dependencies'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.updates_log = []
    def backup_requirements_files(self) -> Dict[str, Path]:
        logger.info("Creating backup of requirements files")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f'backup_{timestamp}'
        backup_path.mkdir(parents=True, exist_ok=True)
        backups = {}
        requirements_files = [
            'requirements.txt',
            'backend/requirements.txt',
            'requirements_ai_ml.txt',
            'requirements_code_quality.txt',
            'requirements-minimal.txt'
        ]
        services_dir = self.base_dir / 'services'
        if services_dir.exists():
            for service_dir in services_dir.iterdir():
                if service_dir.is_dir():
                    req_file = service_dir / 'requirements.txt'
                    if req_file.exists():
                        requirements_files.append(str(req_file.relative_to(self.base_dir)))
        for req_file in requirements_files:
            source = self.base_dir / req_file
            if source.exists():
                dest = backup_path / req_file
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                backups[str(req_file)] = dest
        package_files = [
            'frontend/hms-frontend/package.json',
            'frontend/hms-frontend/package-lock.json'
        ]
        for pkg_file in package_files:
            source = self.base_dir / pkg_file
            if source.exists():
                dest = backup_path / pkg_file
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                backups[str(pkg_file)] = dest
        logger.info(f"Backup created at: {backup_path}")
        return backups
    def update_python_requirements(self, requirements_file: Path) -> bool:
        logger.info(f"Updating Python requirements: {requirements_file}")
        if not requirements_file.exists():
            logger.warning(f"Requirements file not found: {requirements_file}")
            return False
        try:
            with open(requirements_file, 'r') as f:
                content = f.read()
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            try:
                result = subprocess.run([
                    'pip-compile', '--upgrade', '--no-annotate',
                    '--output-file', str(temp_path), str(requirements_file)
                ], capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    if self.test_requirements(temp_path):
                        if not self.dry_run:
                            shutil.move(str(temp_path), str(requirements_file))
                            self.updates_log.append({
                                'file': str(requirements_file),
                                'type': 'python_requirements',
                                'status': 'updated',
                                'method': 'pip-compile'
                            })
                            return True
                        else:
                            logger.info(f"Dry run: Would update {requirements_file} using pip-compile")
                            return True
            except FileNotFoundError:
                logger.info("pip-compile not available, using manual update")
            lines = content.split('\n')
            updated_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('
                    updated_line = self.update_package_line(line)
                    updated_lines.append(updated_line)
                elif line:
                    updated_lines.append(line)
            with open(temp_path, 'w') as f:
                f.write('\n'.join(updated_lines))
            if self.test_requirements(temp_path):
                if not self.dry_run:
                    shutil.move(str(temp_path), str(requirements_file))
                    self.updates_log.append({
                        'file': str(requirements_file),
                        'type': 'python_requirements',
                        'status': 'updated',
                        'method': 'manual'
                    })
                    return True
                else:
                    logger.info(f"Dry run: Would update {requirements_file} manually")
                    return True
            else:
                logger.warning(f"Updated requirements failed testing: {requirements_file}")
                temp_path.unlink()
                return False
        except Exception as e:
            logger.error(f"Error updating {requirements_file}: {str(e)}")
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink()
            return False
    def update_package_line(self, line: str) -> str:
        try:
            if '==' in line:
                package, version = line.split('==', 1)
                latest = self.get_latest_package_version(package)
                if latest:
                    return f"{package}=={latest}"
            elif '>=' in line:
                package, version = line.split('>=', 1)
                return line
            elif '~=' in line:
                package, version = line.split('~=', 1)
                latest = self.get_latest_compatible_version(package, version)
                if latest:
                    return f"{package}~={latest}"
        except Exception as e:
            logger.debug(f"Could not update line '{line}': {str(e)}")
        return line
    def get_latest_package_version(self, package: str) -> Optional[str]:
        try:
            result = subprocess.run([
                'pip', 'index', 'versions', package
            ], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Latest:' in line:
                        return line.split('Latest:')[1].strip()
        except Exception as e:
            logger.debug(f"Could not get latest version for {package}: {str(e)}")
        return None
    def get_latest_compatible_version(self, package: str, current_version: str) -> Optional[str]:
        try:
            if '.' in current_version:
                major_minor = '.'.join(current_version.split('.')[:2])
                result = subprocess.run([
                    'pip', 'index', 'versions', package
                ], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if f'{major_minor}.' in line:
                            version = line.strip().split()[0]
                            if version.startswith(f'{major_minor}.'):
                                return version
        except Exception as e:
            logger.debug(f"Could not get compatible version for {package}: {str(e)}")
        return None
    def update_npm_packages(self, package_json: Path) -> bool:
        logger.info(f"Updating npm packages: {package_json}")
        if not package_json.exists():
            logger.warning(f"package.json not found: {package_json}")
            return False
        try:
            os.chdir(package_json.parent)
            backup_dir = Path('backup')
            backup_dir.mkdir(exist_ok=True)
            shutil.copy2('package.json', backup_dir / 'package.json')
            if Path('package-lock.json').exists():
                shutil.copy2('package-lock.json', backup_dir / 'package-lock.json')
            try:
                result = subprocess.run([
                    'ncu', '-u', '--target', 'latest'
                ], capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    if self.test_npm_packages():
                        if not self.dry_run:
                            self.updates_log.append({
                                'file': str(package_json),
                                'type': 'npm_packages',
                                'status': 'updated',
                                'method': 'npm-check-updates'
                            })
                            return True
                        else:
                            logger.info(f"Dry run: Would update npm packages in {package_json}")
                            return True
            except FileNotFoundError:
                logger.info("npm-check-updates not available, using npm outdated")
            result = subprocess.run([
                'npm', 'update'
            ], capture_output=True, text=True, timeout=180)
            if result.returncode == 0:
                if self.test_npm_packages():
                    if not self.dry_run:
                        self.updates_log.append({
                            'file': str(package_json),
                            'type': 'npm_packages',
                            'status': 'updated',
                            'method': 'npm_update'
                        })
                        return True
                    else:
                        logger.info(f"Dry run: Would update npm packages using npm update")
                        return True
            shutil.copy2(backup_dir / 'package.json', 'package.json')
            if (backup_dir / 'package-lock.json').exists():
                shutil.copy2(backup_dir / 'package-lock.json', 'package-lock.json')
            return False
        except Exception as e:
            logger.error(f"Error updating npm packages: {str(e)}")
            return False
    def test_requirements(self, requirements_file: Path) -> bool:
        logger.info(f"Testing requirements: {requirements_file}")
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                venv_path = temp_path / 'test_env'
                subprocess.run([
                    sys.executable, '-m', 'venv', str(venv_path)
                ], capture_output=True, timeout=60)
                pip_path = venv_path / 'bin' / 'pip'
                if os.name == 'nt':  
                    pip_path = venv_path / 'Scripts' / 'pip.exe'
                result = subprocess.run([
                    str(pip_path), 'install', '-r', str(requirements_file)
                ], capture_output=True, text=True, timeout=300)
                return result.returncode == 0
        except Exception as e:
            logger.error(f"Error testing requirements: {str(e)}")
            return False
    def test_npm_packages(self) -> bool:
        logger.info("Testing npm packages")
        try:
            result = subprocess.run([
                'npm', 'ci'
            ], capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                if Path('package.json').exists():
                    with open('package.json', 'r') as f:
                        package_data = json.load(f)
                        if 'scripts' in package_data and 'test' in package_data['scripts']:
                            test_result = subprocess.run([
                                'npm', 'test'
                            ], capture_output=True, text=True, timeout=180)
                            return test_result.returncode == 0
                return True
        except Exception as e:
            logger.error(f"Error testing npm packages: {str(e)}")
            return False
    def update_security_patches(self) -> bool:
        logger.info("Applying security patches")
        success = True
        requirements_files = [
            self.base_dir / 'requirements.txt',
            self.base_dir / 'backend' / 'requirements.txt',
            self.base_dir / 'requirements_ai_ml.txt'
        ]
        for req_file in requirements_files:
            if req_file.exists():
                if not self.apply_security_patches_python(req_file):
                    success = False
        package_json = self.base_dir / 'frontend' / 'hms-frontend' / 'package.json'
        if package_json.exists():
            if not self.apply_security_patches_npm(package_json):
                success = False
        return success
    def apply_security_patches_python(self, requirements_file: Path) -> bool:
        try:
            result = subprocess.run([
                'pip-audit', '-r', str(requirements_file), '-f', 'json'
            ], capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                audit_data = json.loads(result.stdout)
                vulnerable_packages = []
                for dep in audit_data.get('dependencies', []):
                    for vuln in dep.get('vulns', []):
                        if vuln.get('fix_versions'):
                            vulnerable_packages.append({
                                'name': dep['name'],
                                'current_version': dep['version'],
                                'fix_versions': vuln['fix_versions']
                            })
                if vulnerable_packages:
                    logger.info(f"Found {len(vulnerable_packages)} vulnerable packages")
                    return self.patch_vulnerable_packages(requirements_file, vulnerable_packages)
            return True
        except Exception as e:
            logger.error(f"Error applying security patches to {requirements_file}: {str(e)}")
            return False
    def apply_security_patches_npm(self, package_json: Path) -> bool:
        try:
            os.chdir(package_json.parent)
            result = subprocess.run([
                'npm', 'audit', 'fix'
            ], capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                if self.test_npm_packages():
                    self.updates_log.append({
                        'file': str(package_json),
                        'type': 'npm_security',
                        'status': 'patched',
                        'method': 'npm_audit_fix'
                    })
                    return True
            return False
        except Exception as e:
            logger.error(f"Error applying npm security patches: {str(e)}")
            return False
    def patch_vulnerable_packages(self, requirements_file: Path, vulnerable_packages: List[Dict]) -> bool:
        try:
            with open(requirements_file, 'r') as f:
                content = f.read()
            for package in vulnerable_packages:
                if package['fix_versions']:
                    fix_version = package['fix_versions'][0]
                    old_pattern = f"{package['name']}=={package['current_version']}"
                    new_pattern = f"{package['name']}=={fix_version}"
                    if old_pattern in content:
                        content = content.replace(old_pattern, new_pattern)
                        logger.info(f"Patched {package['name']} from {package['current_version']} to {fix_version}")
            if not self.dry_run:
                with open(requirements_file, 'w') as f:
                    f.write(content)
                if self.test_requirements(requirements_file):
                    self.updates_log.append({
                        'file': str(requirements_file),
                        'type': 'python_security',
                        'status': 'patched',
                        'method': 'manual_patch'
                    })
                    return True
                else:
                    logger.warning("Patched requirements failed testing")
                    return False
            else:
                logger.info("Dry run: Would apply security patches")
                return True
        except Exception as e:
            logger.error(f"Error patching vulnerable packages: {str(e)}")
            return False
    def run_updates(self, security_only: bool = False) -> bool:
        logger.info(f"Starting dependency updates (dry_run={self.dry_run}, security_only={security_only})")
        backups = self.backup_requirements_files()
        try:
            if security_only:
                success = self.update_security_patches()
            else:
                success = True
                requirements_files = [
                    self.base_dir / 'requirements.txt',
                    self.base_dir / 'backend' / 'requirements.txt',
                    self.base_dir / 'requirements_ai_ml.txt'
                ]
                for req_file in requirements_files:
                    if req_file.exists():
                        if not self.update_python_requirements(req_file):
                            success = False
                package_json = self.base_dir / 'frontend' / 'hms-frontend' / 'package.json'
                if package_json.exists():
                    if not self.update_npm_packages(package_json):
                        success = False
            self.generate_update_report()
            return success
        except Exception as e:
            logger.error(f"Error during updates: {str(e)}")
            return False
    def generate_update_report(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.base_dir / 'reports' / 'dependency_updates' / f'update_report_{timestamp}.json'
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'updates': self.updates_log,
            'summary': {
                'total_updates': len(self.updates_log),
                'successful_updates': len([u for u in self.updates_log if u['status'] == 'updated']),
                'failed_updates': len([u for u in self.updates_log if u['status'] == 'failed'])
            }
        }
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Update report saved to: {report_file}")
def main():
    parser = argparse.ArgumentParser(description='Automated Dependency Update System')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    parser.add_argument('--security-only', action='store_true', help='Only apply security patches')
    parser.add_argument('--requirements', type=str, help='Specific requirements file to update')
    parser.add_argument('--package-json', type=str, help='Specific package.json file to update')
    args = parser.parse_args()
    updater = DependencyUpdater(dry_run=args.dry_run)
    try:
        if args.requirements:
            requirements_file = Path(args.requirements)
            if requirements_file.exists():
                success = updater.update_python_requirements(requirements_file)
            else:
                logger.error(f"Requirements file not found: {requirements_file}")
                success = False
        elif args.package_json:
            package_json = Path(args.package_json)
            if package_json.exists():
                success = updater.update_npm_packages(package_json)
            else:
                logger.error(f"package.json not found: {package_json}")
                success = False
        else:
            success = updater.run_updates(security_only=args.security_only)
        if success:
            logger.info("✅ Dependency updates completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Dependency updates failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
if __name__ == "__main__":
    main()