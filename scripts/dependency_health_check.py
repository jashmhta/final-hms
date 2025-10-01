"""
dependency_health_check module
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dependency_health.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
class DependencyHealthChecker:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.findings = []
        self.critical_threshold = 7  
        self.warning_threshold = 30  
    def check_python_requirements(self, requirements_file: Path) -> Dict:
        logger.info(f"Checking Python requirements: {requirements_file}")
        if not requirements_file.exists():
            logger.warning(f"Requirements file not found: {requirements_file}")
            return {}
        try:
            result = subprocess.run(
                ['pip-audit', '-r', str(requirements_file), '-f', 'json'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                audit_data = json.loads(result.stdout)
                vulnerabilities = []
                for dep in audit_data.get('dependencies', []):
                    for vuln in dep.get('vulns', []):
                        vulnerabilities.append({
                            'package': dep['name'],
                            'version': dep['version'],
                            'vulnerability_id': vuln['id'],
                            'aliases': vuln.get('aliases', []),
                            'description': vuln['description'],
                            'fix_versions': vuln.get('fix_versions', []),
                            'severity': self._assess_severity(vuln)
                        })
                return {
                    'vulnerabilities': vulnerabilities,
                    'total_packages': len(audit_data.get('dependencies', [])),
                    'critical_count': len([v for v in vulnerabilities if v['severity'] == 'critical'])
                }
            else:
                logger.error(f"pip-audit failed for {requirements_file}: {result.stderr}")
                return {}
        except Exception as e:
            logger.error(f"Error checking {requirements_file}: {str(e)}")
            return {}
    def check_outdated_packages(self, requirements_file: Path) -> List[Dict]:
        logger.info(f"Checking for outdated packages in: {requirements_file}")
        try:
            result = subprocess.run(
                ['pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                return [
                    {
                        'package': pkg['name'],
                        'current_version': pkg['version'],
                        'latest_version': pkg['latest_version'],
                        'latest_filetype': pkg['latest_filetype'],
                        'upgrade_type': self._determine_upgrade_type(pkg['version'], pkg['latest_version'])
                    }
                    for pkg in outdated
                ]
            else:
                logger.error(f"Failed to check outdated packages: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"Error checking outdated packages: {str(e)}")
            return []
    def check_npm_dependencies(self, package_json: Path) -> Dict:
        logger.info(f"Checking npm dependencies: {package_json}")
        if not package_json.exists():
            logger.warning(f"package.json not found: {package_json}")
            return {}
        try:
            os.chdir(package_json.parent)
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                capture_output=True,
                text=True,
                timeout=120
            )
            audit_data = json.loads(result.stdout)
            outdated_result = subprocess.run(
                ['npm', 'outdated', '--json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            outdated_data = json.loads(outdated_result.stdout) if outdated_result.returncode == 0 else {}
            return {
                'vulnerabilities': audit_data.get('vulnerabilities', {}),
                'advisories': audit_data.get('advisories', {}),
                'outdated_packages': outdated_data,
                'metadata': audit_data.get('metadata', {})
            }
        except Exception as e:
            logger.error(f"Error checking npm dependencies: {str(e)}")
            return {}
    def check_license_compliance(self, requirements_file: Path) -> List[Dict]:
        logger.info(f"Checking license compliance: {requirements_file}")
        try:
            result = subprocess.run(
                ['pip-licenses', '--format=json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                licenses = json.loads(result.stdout)
                return [
                    {
                        'package': pkg['name'],
                        'version': pkg['version'],
                        'license': pkg['license'],
                        'license_classifier': pkg.get('license_classifier', []),
                        'compliant': self._is_license_compliant(pkg['license'])
                    }
                    for pkg in licenses
                ]
            else:
                logger.error(f"License check failed: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"Error checking license compliance: {str(e)}")
            return []
    def _assess_severity(self, vulnerability: Dict) -> str:
        vuln_id = vulnerability.get('id', '').upper()
        description = vulnerability.get('description', '').lower()
        if any(keyword in description for keyword in ['critical', 'remote code execution', 'sql injection']):
            return 'critical'
        elif any(keyword in description for keyword in ['high', 'xss', 'csrf', 'authentication']):
            return 'high'
        elif any(keyword in description for keyword in ['medium', 'denial of service']):
            return 'medium'
        else:
            return 'low'
    def _determine_upgrade_type(self, current: str, latest: str) -> str:
        try:
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            if latest_parts[0] > current_parts[0]:
                return 'major'
            elif latest_parts[1] > current_parts[1]:
                return 'minor'
            elif latest_parts[2] > current_parts[2]:
                return 'patch'
            else:
                return 'none'
        except:
            return 'unknown'
    def _is_license_compliant(self, license_str: str) -> bool:
        compliant_licenses = [
            'MIT', 'Apache 2.0', 'BSD', 'GPL', 'LGPL', 'MPL', 'EPL', 'CDDL',
            'Apache License 2.0', 'BSD License', 'GNU General Public License'
        ]
        return any(lic.lower() in license_str.lower() for lic in compliant_licenses)
    def generate_report(self) -> Dict:
        logger.info("Generating dependency health report")
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files_checked': 0,
                'total_vulnerabilities': 0,
                'critical_vulnerabilities': 0,
                'outdated_packages': 0,
                'license_violations': 0
            },
            'findings': []
        }
        requirements_files = [
            self.base_dir / 'requirements.txt',
            self.base_dir / 'backend' / 'requirements.txt',
            self.base_dir / 'requirements_ai_ml.txt',
        ]
        for req_file in requirements_files:
            if req_file.exists():
                report['summary']['total_files_checked'] += 1
                vuln_data = self.check_python_requirements(req_file)
                if vuln_data:
                    report['summary']['total_vulnerabilities'] += len(vuln_data['vulnerabilities'])
                    report['summary']['critical_vulnerabilities'] += vuln_data['critical_count']
                    for vuln in vuln_data['vulnerabilities']:
                        report['findings'].append({
                            'type': 'vulnerability',
                            'file': str(req_file),
                            'severity': vuln['severity'],
                            'package': vuln['package'],
                            'details': vuln
                        })
                outdated = self.check_outdated_packages(req_file)
                report['summary']['outdated_packages'] += len(outdated)
                for pkg in outdated:
                    report['findings'].append({
                        'type': 'outdated',
                        'file': str(req_file),
                        'package': pkg['package'],
                        'upgrade_type': pkg['upgrade_type'],
                        'details': pkg
                    })
                licenses = self.check_license_compliance(req_file)
                violations = [lic for lic in licenses if not lic['compliant']]
                report['summary']['license_violations'] += len(violations)
                for violation in violations:
                    report['findings'].append({
                        'type': 'license_violation',
                        'file': str(req_file),
                        'package': violation['package'],
                        'license': violation['license'],
                        'details': violation
                    })
        package_json = self.base_dir / 'frontend' / 'hms-frontend' / 'package.json'
        if package_json.exists():
            report['summary']['total_files_checked'] += 1
            npm_data = self.check_npm_dependencies(package_json)
            if npm_data:
                npm_vulns = npm_data.get('vulnerabilities', {})
                report['summary']['total_vulnerabilities'] += len(npm_vulns)
                for vuln_id, vuln in npm_vulns.items():
                    severity = vuln.get('severity', 'low')
                    if severity == 'critical':
                        report['summary']['critical_vulnerabilities'] += 1
                    report['findings'].append({
                        'type': 'npm_vulnerability',
                        'file': str(package_json),
                        'severity': severity,
                        'package': vuln.get('module_name', 'unknown'),
                        'details': vuln
                    })
                outdated = npm_data.get('outdated_packages', {})
                report['summary']['outdated_packages'] += len(outdated)
                for pkg_name, pkg_data in outdated.items():
                    report['findings'].append({
                        'type': 'npm_outdated',
                        'file': str(package_json),
                        'package': pkg_name,
                        'upgrade_type': self._determine_upgrade_type(
                            pkg_data.get('current', '0.0.0'),
                            pkg_data.get('latest', '0.0.0')
                        ),
                        'details': pkg_data
                    })
        return report
    def generate_alerts(self, report: Dict) -> List[Dict]:
        alerts = []
        critical_findings = [
            f for f in report['findings']
            if f.get('severity') == 'critical' or 'critical' in f.get('type', '')
        ]
        if critical_findings:
            alerts.append({
                'level': 'CRITICAL',
                'title': f'Critical Security Vulnerabilities Found ({len(critical_findings)})',
                'message': 'Immediate action required to address critical security vulnerabilities',
                'findings': critical_findings
            })
        high_findings = [
            f for f in report['findings']
            if f.get('severity') == 'high'
        ]
        if high_findings:
            alerts.append({
                'level': 'HIGH',
                'title': f'High Severity Vulnerabilities Found ({len(high_findings)})',
                'message': 'High severity vulnerabilities require prompt attention',
                'findings': high_findings
            })
        major_upgrades = [
            f for f in report['findings']
            if f.get('upgrade_type') == 'major'
        ]
        if major_upgrades:
            alerts.append({
                'level': 'WARNING',
                'title': f'Major Version Upgrades Available ({len(major_upgrades)})',
                'message': 'Major version upgrades may require compatibility testing',
                'findings': major_upgrades
            })
        license_violations = [
            f for f in report['findings']
            if f.get('type') == 'license_violation'
        ]
        if license_violations:
            alerts.append({
                'level': 'WARNING',
                'title': f'License Compliance Issues ({len(license_violations)})',
                'message': 'Some packages may not comply with enterprise license policies',
                'findings': license_violations
            })
        return alerts
    def save_report(self, report: Dict, output_dir: Path = None):
        if output_dir is None:
            output_dir = self.base_dir / 'reports' / 'dependency_health'
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = output_dir / f'dependency_health_{timestamp}.json'
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        alerts = self.generate_alerts(report)
        if alerts:
            alerts_file = output_dir / f'alerts_{timestamp}.json'
            with open(alerts_file, 'w') as f:
                json.dump(alerts, f, indent=2)
        html_file = output_dir / f'report_{timestamp}.html'
        self._generate_html_report(report, alerts, html_file)
        logger.info(f"Reports saved to {output_dir}")
        return json_file, alerts_file, html_file
    def _generate_html_report(self, report: Dict, alerts: List[Dict], output_file: Path):
        html_content = f
        if alerts:
            html_content += "<h2>🚨 Alerts</h2>"
            for alert in alerts:
                alert_class = f"alert-{alert['level'].lower()}"
                html_content += f"<div class='alert {alert_class}'>{alert['message']}</div>"
        html_content += "<h2>Findings</h2>"
        for finding in report['findings'][:20]:  
            severity_class = ""
            if finding.get('severity') == 'critical':
                severity_class = "critical"
            elif finding.get('severity') == 'high':
                severity_class = "warning"
            html_content += f
        html_content += 
        with open(output_file, 'w') as f:
            f.write(html_content)
def main():
    checker = DependencyHealthChecker()
    try:
        report = checker.generate_report()
        json_file, alerts_file, html_file = checker.save_report(report)
        summary = report['summary']
        print(f"\n🔍 Dependency Health Check Complete")
        print(f"📊 Files checked: {summary['total_files_checked']}")
        print(f"🚨 Critical vulnerabilities: {summary['critical_vulnerabilities']}")
        print(f"⚠️  Total vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"📦 Outdated packages: {summary['outdated_packages']}")
        print(f"⚖️  License violations: {summary['license_violations']}")
        print(f"📄 Reports saved to: {json_file.parent}")
        if summary['critical_vulnerabilities'] > 0:
            print("❌ Critical vulnerabilities found - immediate action required!")
            sys.exit(1)
        elif summary['total_vulnerabilities'] > 0:
            print("⚠️  Vulnerabilities found - attention required")
            sys.exit(2)
        else:
            print("✅ All dependencies healthy!")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Dependency health check failed: {str(e)}")
        sys.exit(3)
if __name__ == "__main__":
    main()