"""
service_validator module
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


class ServiceValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.services_dir = self.project_root / "services"
        self.valid_services = 0
        self.total_services = 0
        self.service_issues = []
    def validate_service_structure(self, service_path: Path) -> Dict:
        service_name = service_path.name
        validation_result = {
            "service_name": service_name,
            "valid": False,
            "issues": [],
            "files_found": [],
            "required_files": ["models.py", "main.py", "schemas.py"]
        }
        if not service_path.exists():
            validation_result["issues"].append("Service directory does not exist")
            return validation_result
        required_files = validation_result["required_files"]
        for required_file in required_files:
            file_path = service_path / required_file
            if file_path.exists():
                validation_result["files_found"].append(required_file)
                if file_path.stat().st_size > 0:
                    if required_file.endswith('.py'):
                        try:
                            subprocess.run(
                                ['python3', '-m', 'py_compile', str(file_path)],
                                capture_output=True,
                                text=True,
                                timeout=10
                            )
                        except subprocess.TimeoutExpired:
                            validation_result["issues"].append(f"{required_file} compilation timeout")
                        except Exception as e:
                            validation_result["issues"].append(f"{required_file} compilation error: {e}")
                else:
                    validation_result["issues"].append(f"{required_file} is empty")
            else:
                validation_result["issues"].append(f"Missing required file: {required_file}")
        validation_result["valid"] = len(validation_result["files_found"]) >= 2
        return validation_result
    def validate_all_services(self) -> Dict:
        print("🔍 Validating all HMS services...")
        if not self.services_dir.exists():
            print("❌ Services directory not found")
            return {"error": "Services directory not found"}
        service_dirs = [d for d in self.services_dir.iterdir() if d.is_dir()]
        self.total_services = len(service_dirs)
        validation_results = []
        self.valid_services = 0
        for service_dir in service_dirs:
            result = self.validate_service_structure(service_dir)
            validation_results.append(result)
            if result["valid"]:
                self.valid_services += 1
                print(f"   ✅ {result['service_name']} - Valid")
            else:
                print(f"   ❌ {result['service_name']} - Invalid")
                for issue in result["issues"]:
                    print(f"      - {issue}")
        success_rate = (self.valid_services / self.total_services) * 100 if self.total_services > 0 else 0
        summary = {
            "total_services": self.total_services,
            "valid_services": self.valid_services,
            "success_rate": success_rate,
            "validation_results": validation_results,
            "recommendations": self.generate_recommendations(validation_results)
        }
        return summary
    def generate_recommendations(self, validation_results: List[Dict]) -> List[str]:
        recommendations = []
        missing_files_count = 0
        empty_files_count = 0
        compilation_errors_count = 0
        for result in validation_results:
            for issue in result["issues"]:
                if "Missing required file" in issue:
                    missing_files_count += 1
                elif "is empty" in issue:
                    empty_files_count += 1
                elif "compilation error" in issue:
                    compilation_errors_count += 1
        if missing_files_count > 0:
            recommendations.append(f"Create missing required files for {missing_files_count} services")
        if empty_files_count > 0:
            recommendations.append(f"Add content to empty files in {empty_files_count} services")
        if compilation_errors_count > 0:
            recommendations.append(f"Fix compilation errors in {compilation_errors_count} services")
        if self.valid_services < self.total_services:
            recommendations.append(f"Focus on improving the {self.total_services - self.valid_services} invalid services")
        return recommendations
    def create_missing_service_files(self, service_name: str):
        service_path = self.services_dir / service_name
        if not service_path.exists():
            service_path.mkdir(parents=True, exist_ok=True)
        models_file = service_path / "models.py"
        if not models_file.exists():
            models_content = .format(service_name, service_name.title(), service_name, service_name.replace('_', '_'))
            with open(models_file, 'w') as f:
                f.write(models_content)
            print(f"   Created models.py for {service_name}")
        main_file = service_path / "main.py"
        if not main_file.exists():
            main_content = .format(service_name, service_name.title(), service_name, service_name, service_name)
            with open(main_file, 'w') as f:
                f.write(main_content)
            print(f"   Created main.py for {service_name}")
        schemas_file = service_path / "schemas.py"
        if not schemas_file.exists():
            schemas_content = .format(service_name, service_name.title(), service_name, service_name.title(),
           service_name.title(), service_name, service_name.title(), service_name, service_name.title(), service_name)
            with open(schemas_file, 'w') as f:
                f.write(schemas_content)
            print(f"   Created schemas.py for {service_name}")
    def fix_invalid_services(self, validation_results: List[Dict]):
        print("🔧 Fixing invalid services...")
        for result in validation_results:
            if not result["valid"]:
                service_name = result["service_name"]
                print(f"   Fixing {service_name}...")
                self.create_missing_service_files(service_name)
    def save_validation_report(self, summary: Dict):
        report_file = self.project_root / "service_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"   Validation report saved to: {report_file}")
    def run_complete_validation(self):
        print("🚀 Starting complete service validation...")
        initial_summary = self.validate_all_services()
        print(f"\n📊 Initial Results:")
        print(f"   Total Services: {initial_summary['total_services']}")
        print(f"   Valid Services: {initial_summary['valid_services']}")
        print(f"   Success Rate: {initial_summary['success_rate']:.1f}%")
        if initial_summary['valid_services'] < initial_summary['total_services']:
            print("\n🔧 Fixing invalid services...")
            self.fix_invalid_services(initial_summary['validation_results'])
            print("\n🔄 Re-validating after fixes...")
            final_summary = self.validate_all_services()
            print(f"\n📊 Final Results:")
            print(f"   Total Services: {final_summary['total_services']}")
            print(f"   Valid Services: {final_summary['valid_services']}")
            print(f"   Success Rate: {final_summary['success_rate']:.1f}%")
            self.save_validation_report(final_summary)
            print(f"\n✅ Service validation and fixing completed!")
            print(f"   Services improved from {initial_summary['valid_services']} to {final_summary['valid_services']}")
            return final_summary
        else:
            print("✅ All services are already valid!")
            self.save_validation_report(initial_summary)
            return initial_summary
if __name__ == "__main__":
    validator = ServiceValidator()
    validator.run_complete_validation()