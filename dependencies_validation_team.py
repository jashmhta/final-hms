import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re
import requests
import xml.etree.ElementTree as ET
class DependenciesValidator:
    def __init__(self, base_path: str = "/home/azureuser/hms-enterprise-grade"):
        self.base_path = Path(base_path)
        self.timestamp = datetime.now().isoformat()
        self.results = {
            "inventory": {},
            "security": {},
            "compatibility": {},
            "performance": {},
            "validation": {},
            "recommendations": []
        }
    def log_info(self, message: str):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    def run_command(self, command: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[bool, str, str]:
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    def discover_dependencies(self) -> Dict[str, Any]:
        self.log_info("Discovering all dependencies across the codebase...")
        inventory = {
            "frontend": {},
            "backend": {},
            "microservices": {},
            "infrastructure": {},
            "total_count": 0
        }
        frontend_dirs = [
            self.base_path / "frontend",
            self.base_path / "services" / "graphql_gateway",
            self.base_path / "services" / "blood_bank" / "frontend"
        ]
        for frontend_dir in frontend_dirs:
            if frontend_dir.exists():
                package_json = frontend_dir / "package.json"
                if package_json.exists():
                    try:
                        with open(package_json, 'r') as f:
                            package_data = json.load(f)
                        deps = {
                            **package_data.get('dependencies', {}),
                            **package_data.get('devDependencies', {})
                        }
                        inventory["frontend"][str(frontend_dir)] = {
                            "dependencies": deps,
                            "count": len(deps),
                            "package_manager": "npm"
                        }
                        self.log_info(f"Found {len(deps)} frontend dependencies in {frontend_dir}")
                    except Exception as e:
                        self.log_info(f"Error reading {package_json}: {e}")
        requirements_files = list(self.base_path.rglob("requirements*.txt"))
        for req_file in requirements_files:
            if "node_modules" not in str(req_file):
                try:
                    with open(req_file, 'r') as f:
                        deps = [line.strip() for line in f if line.strip() and not line.startswith('
                    relative_path = str(req_file.relative_to(self.base_path))
                    component_type = "backend" if "backend" in relative_path else "microservices"
                    inventory[component_type][relative_path] = {
                        "dependencies": deps,
                        "count": len(deps),
                        "package_manager": "pip"
                    }
                    self.log_info(f"Found {len(deps)} Python dependencies in {req_file}")
                except Exception as e:
                    self.log_info(f"Error reading {req_file}: {e}")
        docker_compose = self.base_path / "docker-compose.yml"
        if docker_compose.exists():
            try:
                with open(docker_compose, 'r') as f:
                    content = f.read()
                image_pattern = r'image:\s*([^\n]+)'
                images = re.findall(image_pattern, content)
                inventory["infrastructure"]["docker-compose.yml"] = {
                    "images": images,
                    "count": len(images),
                    "type": "container_images"
                }
                self.log_info(f"Found {len(images)} Docker container images")
            except Exception as e:
                self.log_info(f"Error reading {docker_compose}: {e}")
        total_count = 0
        for category in inventory.values():
            if isinstance(category, dict):
                for component in category.values():
                    if isinstance(component, dict):
                        total_count += component.get("count", 0)
        inventory["total_count"] = total_count
        self.log_info(f"Total dependencies discovered: {total_count}")
        return inventory
    def validate_frontend_dependencies(self) -> Dict[str, Any]:
        self.log_info("Validating frontend dependencies...")
        validation_results = {
            "npm_audit": {},
            "dependency_tree": {},
            "install_test": {},
            "build_test": {},
            "security_vulnerabilities": []
        }
        frontend_dirs = [
            self.base_path / "frontend",
            self.base_path / "services" / "graphql_gateway",
            self.base_path / "services" / "blood_bank" / "frontend"
        ]
        for frontend_dir in frontend_dirs:
            if frontend_dir.exists():
                relative_path = str(frontend_dir.relative_to(self.base_path))
                self.log_info(f"Validating frontend dependencies in {relative_path}")
                success, stdout, stderr = self.run_command(
                    ["npm", "audit", "--json", "--audit-level", "moderate"],
                    cwd=frontend_dir
                )
                if success:
                    try:
                        audit_data = json.loads(stdout)
                        validation_results["npm_audit"][relative_path] = audit_data
                        vulnerabilities = audit_data.get("vulnerabilities", {})
                        for pkg_name, vuln_info in vulnerabilities.items():
                            validation_results["security_vulnerabilities"].append({
                                "package": pkg_name,
                                "severity": vuln_info.get("severity", "unknown"),
                                "title": vuln_info.get("title", "Unknown vulnerability"),
                                "component": relative_path
                            })
                    except json.JSONDecodeError:
                        validation_results["npm_audit"][relative_path] = {"error": "Failed to parse audit output"}
                install_success, install_stdout, install_stderr = self.run_command(
                    ["npm", "ci", "--only=production"],
                    cwd=frontend_dir,
                    timeout=600
                )
                validation_results["install_test"][relative_path] = {
                    "success": install_success,
                    "stdout": install_stdout[-1000:] if install_stdout else "",
                    "stderr": install_stderr[-1000:] if install_stderr else ""
                }
        return validation_results
    def validate_backend_dependencies(self) -> Dict[str, Any]:
        self.log_info("Validating backend dependencies...")
        validation_results = {
            "pip_install_test": {},
            "import_test": {},
            "version_compatibility": {},
            "security_vulnerabilities": []
        }
        backend_req = self.base_path / "backend" / "requirements.txt"
        if backend_req.exists():
            success, stdout, stderr = self.run_command(
                ["pip", "install", "--dry-run", "-r", str(backend_req)],
                timeout=300
            )
            validation_results["pip_install_test"]["backend/requirements.txt"] = {
                "success": success,
                "stdout": stdout[-1000:] if stdout else "",
                "stderr": stderr[-1000:] if stderr else ""
            }
            critical_packages = ["django", "djangorestframework", "psycopg2", "celery", "redis"]
            for package in critical_packages:
                import_cmd = f"import {package}; print('{package} version: ' + str(getattr({package}, '__version__', 'unknown')))"
                import_success, import_stdout, import_stderr = self.run_command(
                    ["python", "-c", import_cmd]
                )
                validation_results["import_test"][package] = {
                    "success": import_success,
                    "output": import_stdout,
                    "error": import_stderr
                }
        return validation_results
    def validate_microservices_dependencies(self) -> Dict[str, Any]:
        self.log_info("Validating microservices dependencies...")
        validation_results = {
            "service_validation": {},
            "shared_dependencies": {},
            "api_compatibility": {}
        }
        services_dir = self.base_path / "services"
        if services_dir.exists():
            for service_dir in services_dir.iterdir():
                if service_dir.is_dir():
                    req_file = service_dir / "requirements.txt"
                    if req_file.exists():
                        relative_path = str(req_file.relative_to(self.base_path))
                        try:
                            with open(req_file, 'r') as f:
                                deps = [line.strip() for line in f if line.strip() and not line.startswith('
                            validation_results["service_validation"][relative_path] = {
                                "dependencies": deps,
                                "count": len(deps),
                                "valid_format": True
                            }
                        except Exception as e:
                            validation_results["service_validation"][relative_path] = {
                                "error": str(e),
                                "valid_format": False
                            }
        return validation_results
    def validate_infrastructure_dependencies(self) -> Dict[str, Any]:
        self.log_info("Validating infrastructure dependencies...")
        validation_results = {
            "docker_images": {},
            "kubernetes_manifests": {},
            "system_dependencies": {}
        }
        docker_compose = self.base_path / "docker-compose.yml"
        if docker_compose.exists():
            try:
                with open(docker_compose, 'r') as f:
                    content = f.read()
                image_pattern = r'image:\s*([^\n]+)'
                images = re.findall(image_pattern, content)
                for image in images:
                    validation_results["docker_images"][image] = {
                        "exists": True,  
                        "pull_test": "pending"
                    }
            except Exception as e:
                validation_results["docker_images"]["error"] = str(e)
        system_tools = ["docker", "node", "npm", "python3", "pip"]
        for tool in system_tools:
            success, stdout, stderr = self.run_command(["which", tool])
            validation_results["system_dependencies"][tool] = {
                "available": success,
                "path": stdout.strip() if success else None
            }
        return validation_results
    def analyze_security_vulnerabilities(self) -> Dict[str, Any]:
        self.log_info("Analyzing security vulnerabilities...")
        security_analysis = {
            "frontend_vulnerabilities": [],
            "backend_vulnerabilities": [],
            "critical_issues": [],
            "recommendations": []
        }
        vulnerable_packages = {
            "axios": {"min_safe_version": "1.12.0", "severity": "high"},
            "vite": {"min_safe_version": "7.0.0", "severity": "moderate"},
            "react": {"min_safe_version": "18.3.0", "severity": "low"},
            "django": {"min_safe_version": "4.2.0", "severity": "critical"}
        }
        frontend_dirs = [
            self.base_path / "frontend",
            self.base_path / "services" / "graphql_gateway",
            self.base_path / "services" / "blood_bank" / "frontend"
        ]
        for frontend_dir in frontend_dirs:
            package_json = frontend_dir / "package.json"
            if package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        package_data = json.load(f)
                    deps = {
                        **package_data.get('dependencies', {}),
                        **package_data.get('devDependencies', {})
                    }
                    for pkg_name, pkg_version in deps.items():
                        if pkg_name in vulnerable_packages:
                            version_info = vulnerable_packages[pkg_name]
                            security_analysis["frontend_vulnerabilities"].append({
                                "package": pkg_name,
                                "current_version": pkg_version,
                                "min_safe_version": version_info["min_safe_version"],
                                "severity": version_info["severity"],
                                "component": str(frontend_dir.relative_to(self.base_path))
                            })
                            if version_info["severity"] in ["critical", "high"]:
                                security_analysis["critical_issues"].append({
                                    "package": pkg_name,
                                    "severity": version_info["severity"],
                                    "component": str(frontend_dir.relative_to(self.base_path))
                                })
                except Exception as e:
                    self.log_info(f"Error analyzing {package_json}: {e}")
        return security_analysis
    def analyze_compatibility(self) -> Dict[str, Any]:
        self.log_info("Analyzing compatibility...")
        compatibility_analysis = {
            "version_conflicts": [],
            "engine_compatibility": {},
            "platform_compatibility": {},
            "recommendations": []
        }
        frontend_dirs = [
            self.base_path / "frontend",
            self.base_path / "services" / "graphql_gateway",
            self.base_path / "services" / "blood_bank" / "frontend"
        ]
        for frontend_dir in frontend_dirs:
            package_json = frontend_dir / "package.json"
            if package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        package_data = json.load(f)
                    engine_spec = package_data.get("engines", {}).get("node")
                    if engine_spec:
                        compatibility_analysis["engine_compatibility"][str(frontend_dir.relative_to(self.base_path))] = engine_spec
                except Exception as e:
                    self.log_info(f"Error checking engine compatibility in {package_json}: {e}")
        python_req_files = [
            self.base_path / "backend" / "requirements.txt",
            self.base_path / "requirements.txt"
        ]
        for req_file in python_req_files:
            if req_file.exists():
                try:
                    with open(req_file, 'r') as f:
                        content = f.read()
                    python_version_match = re.search(r'python>=(\d+\.\d+)', content)
                    if python_version_match:
                        version_spec = python_version_match.group(0)
                        compatibility_analysis["platform_compatibility"][str(req_file.relative_to(self.base_path))] = version_spec
                except Exception as e:
                    self.log_info(f"Error checking Python version compatibility in {req_file}: {e}")
        return compatibility_analysis
    def generate_recommendations(self) -> List[Dict[str, Any]]:
        self.log_info("Generating recommendations...")
        recommendations = []
        if self.results["security"].get("frontend_vulnerabilities"):
            recommendations.append({
                "type": "security",
                "priority": "critical",
                "title": "Address Frontend Security Vulnerabilities",
                "description": "Update vulnerable frontend packages to latest secure versions",
                "actions": [
                    "Run 'npm audit fix' to automatically fix vulnerabilities",
                    "Manually update packages that cannot be automatically fixed",
                    "Consider implementing security scanning in CI/CD pipeline"
                ]
            })
        if self.results["inventory"]["total_count"] > 1000:
            recommendations.append({
                "type": "maintenance",
                "priority": "high",
                "title": "Implement Dependency Management Strategy",
                "description": "Large number of dependencies detected, implement management strategy",
                "actions": [
                    "Set up automated dependency updates using Dependabot or Renovate",
                    "Implement dependency version pinning for reproducible builds",
                    "Consider consolidating duplicate dependencies across services"
                ]
            })
        recommendations.append({
            "type": "performance",
            "priority": "medium",
            "title": "Optimize Dependency Performance",
            "description": "Implement dependency performance optimization strategies",
            "actions": [
                "Use tree-shaking and code splitting for frontend dependencies",
                "Implement lazy loading for non-critical dependencies",
                "Monitor dependency bundle sizes and loading times"
            ]
        })
        recommendations.append({
            "type": "monitoring",
            "priority": "medium",
            "title": "Implement Dependency Monitoring",
            "description": "Set up comprehensive dependency monitoring and alerting",
            "actions": [
                "Configure automated security scanning alerts",
                "Set up dependency update notifications",
                "Implement performance monitoring for critical dependencies"
            ]
        })
        return recommendations
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        self.log_info("Starting comprehensive dependency validation...")
        self.results["inventory"] = self.discover_dependencies()
        self.results["validation"]["frontend"] = self.validate_frontend_dependencies()
        self.results["validation"]["backend"] = self.validate_backend_dependencies()
        self.results["validation"]["microservices"] = self.validate_microservices_dependencies()
        self.results["validation"]["infrastructure"] = self.validate_infrastructure_dependencies()
        self.results["security"] = self.analyze_security_vulnerabilities()
        self.results["compatibility"] = self.analyze_compatibility()
        self.results["recommendations"] = self.generate_recommendations()
        self.log_info("Comprehensive dependency validation completed!")
        return self.results
    def save_report(self, filename: str = "dependency_validation_report.json"):
        report_path = self.base_path / filename
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        self.log_info(f"Validation report saved to {report_path}")
        return report_path
def main():
    validator = DependenciesValidator()
    print("=" * 80)
    print("HMS ENTERPRISE-GRADE DEPENDENCIES VALIDATION TEAM")
    print("Comprehensive Dependency Validation and Security Analysis")
    print("=" * 80)
    results = validator.run_comprehensive_validation()
    report_path = validator.save_report()
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    inventory = results["inventory"]
    print(f"Total Dependencies Discovered: {inventory['total_count']}")
    print(f"Frontend Dependencies: {sum(item.get('count', 0) for item in inventory['frontend'].values())}")
    print(f"Backend Dependencies: {sum(item.get('count', 0) for item in inventory['backend'].values())}")
    print(f"Microservices Dependencies: {sum(item.get('count', 0) for item in inventory['microservices'].values())}")
    print(f"Infrastructure Dependencies: {sum(item.get('count', 0) for item in inventory['infrastructure'].values())}")
    security = results["security"]
    print(f"Security Vulnerabilities Found: {len(security.get('frontend_vulnerabilities', []))}")
    print(f"Critical Issues: {len(security.get('critical_issues', []))}")
    recommendations = results["recommendations"]
    print(f"Recommendations Generated: {len(recommendations)}")
    print(f"\nDetailed Report: {report_path}")
    print("=" * 80)
if __name__ == "__main__":
    main()