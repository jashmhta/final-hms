#!/usr/bin/env python3
"""
HMS Enterprise-Grade Redundancy Elimination Validation
Validates that redundancy has been effectively eliminated across the system.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, Counter
import json


class RedundancyValidator:
    """Validates redundancy elimination across the HMS system."""

    def __init__(self, root_path: str = None):
        self.root_path = Path(root_path) if root_path else Path.cwd()
        self.redundancy_issues = []
        self.metrics = {
            "total_files": 0,
            "python_files": 0,
            "duplicate_lines": 0,
            "redundant_patterns": 0,
            "shared_components_used": 0,
            "efficiency_score": 0
        }

    def validate_system(self) -> Dict[str, Any]:
        """Comprehensive validation of redundancy elimination."""
        print("🔍 Starting HMS Enterprise-Grade Redundancy Validation...")
        print(f"Root path: {self.root_path}")

        results = {
            "file_analysis": self._analyze_file_structure(),
            "code_patterns": self._analyze_code_patterns(),
            "configuration_analysis": self._analyze_configuration(),
            "shared_library_usage": self._analyze_shared_library_usage(),
            "service_consistency": self._analyze_service_consistency(),
            "recommendations": []
        }

        # Calculate overall metrics
        self._calculate_metrics(results)

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def _analyze_file_structure(self) -> Dict[str, Any]:
        """Analyze file structure for redundancy."""
        print("📁 Analyzing file structure...")

        file_stats = {
            "total_files": 0,
            "python_files": 0,
            "config_files": 0,
            "duplicate_files": 0,
            "file_size_distribution": defaultdict(int),
            "duplicate_names": defaultdict(list)
        }

        for file_path in self.root_path.rglob("*"):
            if file_path.is_file():
                file_stats["total_files"] += 1

                # Analyze by file type
                if file_path.suffix == ".py":
                    file_stats["python_files"] += 1
                elif file_path.name in ["docker-compose.yml", "deployment.yaml"] or file_path.suffix in [".yml", ".yaml"]:
                    file_stats["config_files"] += 1

                # Check for duplicate file names
                relative_path = file_path.relative_to(self.root_path)
                file_name = relative_path.name
                file_stats["duplicate_names"][file_name].append(str(relative_path))

                # Analyze file sizes
                try:
                    size = file_path.stat().st_size
                    if size < 1024:
                        file_stats["file_size_distribution"]["<1KB"] += 1
                    elif size < 10240:
                        file_stats["file_size_distribution"]["1-10KB"] += 1
                    elif size < 102400:
                        file_stats["file_size_distribution"]["10-100KB"] += 1
                    else:
                        file_stats["file_size_distribution"][">100KB"] += 1
                except:
                    pass

        # Count actual duplicates
        for name, paths in file_stats["duplicate_names"].items():
            if len(paths) > 1:
                file_stats["duplicate_files"] += len(paths) - 1

        return dict(file_stats)

    def _analyze_code_patterns(self) -> Dict[str, Any]:
        """Analyze code patterns for redundancy."""
        print("🔍 Analyzing code patterns...")

        patterns = {
            "timestamp_fields": 0,
            "health_check_endpoints": 0,
            "cors_middleware": 0,
            "base_model_patterns": 0,
            "crud_operations": 0,
            "error_handling_patterns": 0,
            "import_statements": Counter(),
            "function_definitions": Counter(),
            "class_definitions": Counter()
        }

        python_files = list(self.root_path.rglob("*.py"))

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                # Analyze AST
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            patterns["import_statements"][alias.name] += 1
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            patterns["import_statements"][node.module] += 1
                    elif isinstance(node, ast.FunctionDef):
                        patterns["function_definitions"][node.name] += 1
                    elif isinstance(node, ast.ClassDef):
                        patterns["class_definitions"][node.name] += 1

                # Analyze text patterns
                patterns["timestamp_fields"] += content.count("created_at = Column(DateTime, default=datetime.utcnow)")
                patterns["health_check_endpoints"] += content.count('def health_check(')
                patterns["cors_middleware"] += content.count('CORSMiddleware')
                patterns["base_model_patterns"] += content.count('class.*Model.*Base:')
                patterns["crud_operations"] += content.count('.get_multi(') + content.count('.create(') + content.count('.update(')

            except:
                continue

        return patterns

    def _analyze_configuration(self) -> Dict[str, Any]:
        """Analyze configuration files for redundancy."""
        print("⚙️ Analyzing configuration files...")

        config_stats = {
            "docker_compose_files": 0,
            "k8s_deployment_files": 0,
            "requirements_files": 0,
            "duplicate_configs": [],
            "configuration_patterns": {
                "postgres_image": 0,
                "resource_limits": 0,
                "health_checks": 0,
                "env_variables": 0
            }
        }

        # Analyze Docker Compose files
        for file_path in self.root_path.rglob("docker-compose.yml"):
            config_stats["docker_compose_files"] += 1
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    config_stats["configuration_patterns"]["postgres_image"] += content.count("postgres:")
                    config_stats["configuration_patterns"]["resource_limits"] += content.count("mem_limit")
                    config_stats["configuration_patterns"]["health_checks"] += content.count("healthcheck")
            except:
                pass

        # Analyze K8s deployment files
        for file_path in self.root_path.rglob("deployment.yaml"):
            config_stats["k8s_deployment_files"] += 1
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    config_stats["configuration_patterns"]["resource_limits"] += content.count("resources:")
                    config_stats["configuration_patterns"]["health_checks"] += content.count("livenessProbe")
                    config_stats["configuration_patterns"]["env_variables"] += content.count("env:")
            except:
                pass

        # Analyze requirements files
        for file_path in self.root_path.rglob("requirements*.txt"):
            config_stats["requirements_files"] += 1

        return config_stats

    def _analyze_shared_library_usage(self) -> Dict[str, Any]:
        """Analyze usage of shared libraries."""
        print("📚 Analyzing shared library usage...")

        shared_usage = {
            "shared_imports": 0,
            "services_using_shared": 0,
            "shared_components_used": 0,
            "components_found": {
                "BaseServiceApp": 0,
                "HMSBaseModel": 0,
                "BaseCRUD": 0,
                "BaseConfig": 0,
                "ServiceBuilder": 0
            }
        }

        python_files = list(self.root_path.rglob("*.py"))

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for shared library imports
                if "from shared." in content:
                    shared_usage["shared_imports"] += 1

                # Check for specific shared components
                for component in shared_usage["components_found"]:
                    if component in content:
                        shared_usage["components_found"][component] += 1
                        shared_usage["shared_components_used"] += 1

                # Check if this is a service using shared libraries
                if any(f"from shared.{comp}" in content for comp in ["service", "database", "api", "config"]):
                    shared_usage["services_using_shared"] += 1

            except:
                continue

        return shared_usage

    def _analyze_service_consistency(self) -> Dict[str, Any]:
        """Analyze consistency across services."""
        print("🔄 Analyzing service consistency...")

        consistency_stats = {
            "services_found": 0,
            "consistent_health_checks": 0,
            "consistent_error_handling": 0,
            "consistent_logging": 0,
            "inconsistent_patterns": []
        }

        # Find main.py files in services
        service_files = list(self.root_path.glob("services/*/main.py"))
        consistency_stats["services_found"] = len(service_files)

        for file_path in service_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for consistent patterns
                if '"/health"' in content:
                    consistency_stats["consistent_health_checks"] += 1

                if "HTTPException" in content:
                    consistency_stats["consistent_error_handling"] += 1

                if "logging" in content:
                    consistency_stats["consistent_logging"] += 1

            except:
                continue

        return consistency_stats

    def _calculate_metrics(self, results: Dict[str, Any]):
        """Calculate overall metrics."""
        file_analysis = results["file_analysis"]
        shared_usage = results["shared_library_usage"]
        consistency = results["service_consistency"]

        self.metrics["total_files"] = file_analysis["total_files"]
        self.metrics["python_files"] = file_analysis["python_files"]

        # Calculate efficiency score (0-100)
        efficiency_score = 0

        # Shared library usage (40 points)
        if shared_usage["services_using_shared"] > 0:
            usage_ratio = shared_usage["services_using_shared"] / max(consistency["services_found"], 1)
            efficiency_score += min(40, usage_ratio * 40)

        # Configuration consistency (30 points)
        if file_analysis["duplicate_files"] < 10:
            efficiency_score += 30

        # Service consistency (20 points)
        if consistency["services_found"] > 0:
            consistency_ratio = consistency["consistent_health_checks"] / consistency["services_found"]
            efficiency_score += min(20, consistency_ratio * 20)

        # Shared components (10 points)
        if shared_usage["shared_components_used"] > 10:
            efficiency_score += 10

        self.metrics["efficiency_score"] = min(100, int(efficiency_score))

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []

        # File structure recommendations
        if results["file_analysis"]["duplicate_files"] > 20:
            recommendations.append("High number of duplicate files found. Consider consolidating similar configurations.")

        # Shared library usage recommendations
        if results["shared_library_usage"]["services_using_shared"] < 5:
            recommendations.append("Low shared library adoption. Migrate more services to use shared components.")

        # Configuration recommendations
        if results["configuration_analysis"]["docker_compose_files"] > 10:
            recommendations.append("Many Docker Compose files found. Use template-based configuration generation.")

        # Consistency recommendations
        if results["service_consistency"]["consistent_health_checks"] < results["service_consistency"]["services_found"]:
            recommendations.append("Inconsistent health check implementations. Standardize using shared patterns.")

        # Performance recommendations
        if self.metrics["efficiency_score"] < 70:
            recommendations.append("Low efficiency score. Focus on shared library adoption and configuration consolidation.")

        return recommendations

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate validation report."""
        report = f"""
# HMS Enterprise-Grade Redundancy Elimination Validation Report

## Overall Metrics
- **Efficiency Score**: {self.metrics['efficiency_score']}/100
- **Total Files**: {self.metrics['total_files']}
- **Python Files**: {self.metrics['python_files']}
- **Shared Components Used**: {results['shared_library_usage']['shared_components_used']}

## File Structure Analysis
- **Total Files**: {results['file_analysis']['total_files']}
- **Python Files**: {results['file_analysis']['python_files']}
- **Configuration Files**: {results['file_analysis']['config_files']}
- **Duplicate Files**: {results['file_analysis']['duplicate_files']}

## Code Pattern Analysis
- **Timestamp Fields**: {results['code_patterns']['timestamp_fields']}
- **Health Check Endpoints**: {results['code_patterns']['health_check_endpoints']}
- **CORS Middleware**: {results['code_patterns']['cors_middleware']}
- **Base Model Patterns**: {results['code_patterns']['base_model_patterns']}

## Configuration Analysis
- **Docker Compose Files**: {results['configuration_analysis']['docker_compose_files']}
- **K8s Deployment Files**: {results['configuration_analysis']['k8s_deployment_files']}
- **Requirements Files**: {results['configuration_analysis']['requirements_files']}

## Shared Library Usage
- **Services Using Shared Libraries**: {results['shared_library_usage']['services_using_shared']}
- **Shared Imports Found**: {results['shared_library_usage']['shared_imports']}

## Service Consistency
- **Services Found**: {results['service_consistency']['services_found']}
- **Consistent Health Checks**: {results['service_consistency']['consistent_health_checks']}
- **Consistent Error Handling**: {results['service_consistency']['consistent_error_handling']}

## Recommendations
"""

        for i, rec in enumerate(results['recommendations'], 1):
            report += f"{i}. {rec}\n"

        return report


def main():
    """Main validation function."""
    print("🚀 HMS Enterprise-Grade Redundancy Elimination Validation")
    print("=" * 60)

    validator = RedundancyValidator()
    results = validator.validate_system()

    # Generate and display report
    report = validator.generate_report(results)
    print(report)

    # Save detailed results
    with open("redundancy_validation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📊 Detailed results saved to: redundancy_validation_results.json")

    # Print summary
    print(f"\n🎯 VALIDATION COMPLETE")
    print(f"   Efficiency Score: {validator.metrics['efficiency_score']}/100")
    if validator.metrics['efficiency_score'] >= 80:
        print("   ✅ EXCELLENT - Redundancy elimination successful!")
    elif validator.metrics['efficiency_score'] >= 60:
        print("   ⚠️  GOOD - Redundancy elimination progress made, room for improvement")
    else:
        print("   ❌ NEEDS WORK - Significant redundancy still present")


if __name__ == "__main__":
    main()