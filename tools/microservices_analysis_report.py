"""
microservices_analysis_report module
"""

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class ServiceAnalysis:
    name: str
    has_main: bool
    has_models: bool
    has_schemas: bool
    has_dockerfile: bool
    has_requirements: bool
    has_docker_compose: bool
    has_tests: bool
    framework: str
    port: int
    dependencies: List[str]
    security_features: List[str]
    compliance_features: List[str]
    criticality_score: float
    readiness_score: float
    issues: List[str]
    recommendations: List[str]
class MicroservicesAnalysis:
    def __init__(self, services_dir: str = "/home/azureuser/hms-enterprise-grade/services"):
        self.services_dir = services_dir
        self.service_analyses: Dict[str, ServiceAnalysis] = {}
        self.logger = self._setup_logging()
    def _setup_logging(self):
        import logging
        logger = logging.getLogger("MicroservicesAnalysis")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    def analyze_service(self, service_name: str) -> ServiceAnalysis:
        service_path = os.path.join(self.services_dir, service_name)
        self.logger.info(f"🔍 Analyzing service: {service_name}")
        analysis = ServiceAnalysis(
            name=service_name,
            has_main=False,
            has_models=False,
            has_schemas=False,
            has_dockerfile=False,
            has_requirements=False,
            has_docker_compose=False,
            has_tests=False,
            framework="Unknown",
            port=0,
            dependencies=[],
            security_features=[],
            compliance_features=[],
            criticality_score=0.0,
            readiness_score=0.0,
            issues=[],
            recommendations=[]
        )
        main_files = ["main.py", "app/main.py"]
        for main_file in main_files:
            if os.path.exists(os.path.join(service_path, main_file)):
                analysis.has_main = True
                self._analyze_main_file(os.path.join(service_path, main_file), analysis)
                break
        if os.path.exists(os.path.join(service_path, "models.py")):
            analysis.has_models = True
            self._analyze_models_file(os.path.join(service_path, "models.py"), analysis)
        if os.path.exists(os.path.join(service_path, "schemas.py")):
            analysis.has_schemas = True
            self._analyze_schemas_file(os.path.join(service_path, "schemas.py"), analysis)
        if os.path.exists(os.path.join(service_path, "Dockerfile")):
            analysis.has_dockerfile = True
            self._analyze_dockerfile(os.path.join(service_path, "Dockerfile"), analysis)
        if os.path.exists(os.path.join(service_path, "requirements.txt")):
            analysis.has_requirements = True
            self._analyze_requirements(os.path.join(service_path, "requirements.txt"), analysis)
        if os.path.exists(os.path.join(service_path, "docker-compose.yml")):
            analysis.has_docker_compose = True
        test_files = ["test_*.py", "*_test.py", "tests/"]
        for test_pattern in test_files:
            if os.path.exists(os.path.join(service_path, test_pattern.replace("*", "").replace("/", ""))):
                analysis.has_tests = True
                break
        readiness_factors = [
            analysis.has_main,
            analysis.has_models,
            analysis.has_schemas,
            analysis.has_dockerfile,
            analysis.has_requirements
        ]
        analysis.readiness_score = sum(readiness_factors) / len(readiness_factors)
        analysis.criticality_score = self._calculate_criticality(service_name, analysis)
        analysis.recommendations = self._generate_recommendations(analysis)
        return analysis
    def _analyze_main_file(self, main_file_path: str, analysis: ServiceAnalysis):
        try:
            with open(main_file_path, 'r') as f:
                content = f.read()
            if "from fastapi import" in content:
                analysis.framework = "FastAPI"
            elif "from flask import" in content:
                analysis.framework = "Flask"
            elif "from django import" in content:
                analysis.framework = "Django"
            port_match = re.search(r'port\s*=\s*(\d+)', content)
            if port_match:
                analysis.port = int(port_match.group(1))
            security_indicators = [
                "authentication", "authorization", "jwt", "token",
                "encryption", "security", "cors", "middleware"
            ]
            for indicator in security_indicators:
                if indicator.lower() in content.lower():
                    analysis.security_features.append(indicator)
            compliance_indicators = [
                "audit", "log", "hipaa", "compliance", "privacy", "phi"
            ]
            for indicator in compliance_indicators:
                if indicator.lower() in content.lower():
                    analysis.compliance_features.append(indicator)
        except Exception as e:
            analysis.issues.append(f"Error analyzing main file: {str(e)}")
    def _analyze_models_file(self, models_file_path: str, analysis: ServiceAnalysis):
        try:
            with open(models_file_path, 'r') as f:
                content = f.read()
            if "Base = declarative_base()" in content:
                analysis.dependencies.append("SQLAlchemy")
            sensitive_fields = ["password", "ssn", "medical", "patient", "health"]
            for field in sensitive_fields:
                if field in content.lower():
                    analysis.compliance_features.append(f"Handles {field} data")
        except Exception as e:
            analysis.issues.append(f"Error analyzing models file: {str(e)}")
    def _analyze_schemas_file(self, schemas_file_path: str, analysis: ServiceAnalysis):
        try:
            with open(schemas_file_path, 'r') as f:
                content = f.read()
            if "from pydantic import" in content:
                analysis.dependencies.append("Pydantic")
            if "validator" in content.lower():
                analysis.security_features.append("Input validation")
        except Exception as e:
            analysis.issues.append(f"Error analyzing schemas file: {str(e)}")
    def _analyze_dockerfile(self, dockerfile_path: str, analysis: ServiceAnalysis):
        try:
            with open(dockerfile_path, 'r') as f:
                content = f.read()
            port_match = re.search(r'EXPOSE\s+(\d+)', content)
            if port_match and analysis.port == 0:
                analysis.port = int(port_match.group(1))
            security_practices = ["python:3", "slim", "alpine", "non-root"]
            for practice in security_practices:
                if practice.lower() in content.lower():
                    analysis.security_features.append(f"Docker {practice}")
        except Exception as e:
            analysis.issues.append(f"Error analyzing Dockerfile: {str(e)}")
    def _analyze_requirements(self, requirements_path: str, analysis: ServiceAnalysis):
        try:
            with open(requirements_path, 'r') as f:
                dependencies = f.read().strip().split('\n')
            for dep in dependencies:
                dep = dep.strip()
                if dep and not dep.startswith('
                    analysis.dependencies.append(dep)
                    security_packages = [
                        "cryptography", "jwt", "bcrypt", "pydantic",
                        "sqlalchemy", "psycopg2", "redis"
                    ]
                    for sec_pkg in security_packages:
                        if sec_pkg in dep.lower():
                            analysis.security_features.append(f"Uses {sec_pkg}")
        except Exception as e:
            analysis.issues.append(f"Error analyzing requirements: {str(e)}")
    def _calculate_criticality(self, service_name: str, analysis: ServiceAnalysis) -> float:
        criticality = 0.5  
        critical_services = [
            "audit", "patients", "billing", "pharmacy", "lab", "radiology",
            "appointments", "er_alerts", "emergency", "triage", "prescription",
            "notifications", "backup", "security", "auth"
        ]
        for critical_service in critical_services:
            if critical_service in service_name.lower():
                criticality += 0.3
                break
        if any(feature in analysis.compliance_features for feature in ["patient", "medical", "phi"]):
            criticality += 0.2
        return min(1.0, criticality)
    def _generate_recommendations(self, analysis: ServiceAnalysis) -> List[str]:
        recommendations = []
        if not analysis.has_main:
            recommendations.append("Add main.py file with service entry point")
        if not analysis.has_models:
            recommendations.append("Add models.py for database schema")
        if not analysis.has_schemas:
            recommendations.append("Add schemas.py for API validation")
        if not analysis.has_dockerfile:
            recommendations.append("Add Dockerfile for containerization")
        if not analysis.has_requirements:
            recommendations.append("Add requirements.txt for dependencies")
        if not analysis.security_features:
            recommendations.append("Implement security features (authentication, authorization)")
        if "authentication" not in analysis.security_features:
            recommendations.append("Add authentication mechanisms")
        if "encryption" not in analysis.security_features:
            recommendations.append("Implement data encryption")
        if not analysis.compliance_features:
            recommendations.append("Add compliance features (audit logging, HIPAA)")
        if "audit" not in analysis.compliance_features:
            recommendations.append("Implement audit logging")
        if not analysis.has_tests:
            recommendations.append("Add unit and integration tests")
        return recommendations
    def analyze_all_services(self) -> Dict[str, ServiceAnalysis]:
        self.logger.info("🚀 Starting comprehensive microservices analysis...")
        service_dirs = [d for d in os.listdir(self.services_dir)
                       if os.path.isdir(os.path.join(self.services_dir, d))
                       and d not in ['.', '..', 'templates']]
        for service_name in service_dirs:
            analysis = self.analyze_service(service_name)
            self.service_analyses[service_name] = analysis
        return self.service_analyses
    def generate_analysis_report(self) -> Dict[str, Any]:
        total_services = len(self.service_analyses)
        ready_services = sum(1 for a in self.service_analyses.values() if a.readiness_score >= 0.8)
        critical_services = sum(1 for a in self.service_analyses.values() if a.criticality_score >= 0.8)
        avg_readiness = sum(a.readiness_score for a in self.service_analyses.values()) / total_services if total_services > 0 else 0
        avg_criticality = sum(a.criticality_score for a in self.service_analyses.values()) / total_services if total_services > 0 else 0
        framework_counts = {}
        for analysis in self.service_analyses.values():
            framework = analysis.framework
            framework_counts[framework] = framework_counts.get(framework, 0) + 1
        all_issues = []
        for analysis in self.service_analyses.values():
            all_issues.extend(analysis.issues)
        issue_counts = {}
        for issue in all_issues:
            issue_type = issue.split(":")[0] if ":" in issue else issue
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        all_recommendations = []
        for analysis in self.service_analyses.values():
            all_recommendations.extend(analysis.recommendations)
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        report = {
            "analysis_summary": {
                "total_services": total_services,
                "ready_services": ready_services,
                "critical_services": critical_services,
                "average_readiness_score": avg_readiness,
                "average_criticality_score": avg_criticality,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            },
            "framework_distribution": framework_counts,
            "common_issues": issue_counts,
            "top_recommendations": dict(sorted(recommendation_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "service_analyses": {name: asdict(analysis) for name, analysis in self.service_analyses.items()},
            "overall_assessment": self._generate_overall_assessment()
        }
        return report
    def _generate_overall_assessment(self) -> Dict[str, Any]:
        total_services = len(self.service_analyses)
        ready_services = sum(1 for a in self.service_analyses.values() if a.readiness_score >= 0.8)
        assessment = {
            "architecture_maturity": "Emerging",
            "deployment_readiness": "Low",
            "security_posture": "Basic",
            "compliance_readiness": "Partial",
            "overall_health": "Needs Improvement",
            "key_strengths": [],
            "critical_gaps": [],
            "immediate_actions": []
        }
        if ready_services / total_services >= 0.8:
            assessment["architecture_maturity"] = "Mature"
        elif ready_services / total_services >= 0.5:
            assessment["architecture_maturity"] = "Developing"
        docker_ready = sum(1 for a in self.service_analyses.values() if a.has_dockerfile)
        if docker_ready / total_services >= 0.8:
            assessment["deployment_readiness"] = "High"
        elif docker_ready / total_services >= 0.5:
            assessment["deployment_readiness"] = "Medium"
        framework_consistency = len(set(a.framework for a in self.service_analyses.values())) <= 2
        if framework_consistency:
            assessment["key_strengths"].append("Consistent framework usage")
        services_without_main = sum(1 for a in self.service_analyses.values() if not a.has_main)
        if services_without_main > 0:
            assessment["critical_gaps"].append(f"{services_without_main} services missing main.py")
        services_without_docker = sum(1 for a in self.service_analyses.values() if not a.has_dockerfile)
        if services_without_docker > 0:
            assessment["critical_gaps"].append(f"{services_without_docker} services missing Dockerfile")
        if services_without_main > 0:
            assessment["immediate_actions"].append("Create main.py files for all services")
        if services_without_docker > 0:
            assessment["immediate_actions"].append("Create Dockerfiles for all services")
        return assessment
    def print_analysis_summary(self):
        report = self.generate_analysis_report()
        print("\n" + "="*80)
        print("🏥 HMS ENTERPRISE-GRADE MICROSERVICES ANALYSIS REPORT")
        print("="*80)
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"   Total Services Analyzed: {report['analysis_summary']['total_services']}")
        print(f"   Ready Services (≥80%): {report['analysis_summary']['ready_services']}")
        print(f"   Critical Services: {report['analysis_summary']['critical_services']}")
        print(f"   Average Readiness Score: {report['analysis_summary']['average_readiness_score']:.2f}")
        print(f"   Average Criticality Score: {report['analysis_summary']['average_criticality_score']:.2f}")
        print(f"\n🔧 FRAMEWORK DISTRIBUTION:")
        for framework, count in report['framework_distribution'].items():
            percentage = (count / report['analysis_summary']['total_services']) * 100
            print(f"   {framework}: {count} services ({percentage:.1f}%)")
        assessment = report['overall_assessment']
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"   Architecture Maturity: {assessment['architecture_maturity']}")
        print(f"   Deployment Readiness: {assessment['deployment_readiness']}")
        print(f"   Security Posture: {assessment['security_posture']}")
        print(f"   Compliance Readiness: {assessment['compliance_readiness']}")
        print(f"   Overall Health: {assessment['overall_health']}")
        if assessment['key_strengths']:
            print(f"\n💪 KEY STRENGTHS:")
            for strength in assessment['key_strengths']:
                print(f"   ✅ {strength}")
        if assessment['critical_gaps']:
            print(f"\n🚨 CRITICAL GAPS:")
            for gap in assessment['critical_gaps']:
                print(f"   ❌ {gap}")
        if assessment['immediate_actions']:
            print(f"\n⚡ IMMEDIATE ACTIONS:")
            for action in assessment['immediate_actions']:
                print(f"   🔧 {action}")
        print(f"\n💡 TOP RECOMMENDATIONS:")
        for rec, count in list(report['top_recommendations'].items())[:5]:
            print(f"   {rec} (affects {count} services)")
        print(f"\n📋 SERVICE READINESS BREAKDOWN:")
        readiness_ranges = {
            "Excellent (≥90%)": 0,
            "Good (80-89%)": 0,
            "Fair (60-79%)": 0,
            "Poor (<60%)": 0
        }
        for analysis in self.service_analyses.values():
            if analysis.readiness_score >= 0.9:
                readiness_ranges["Excellent (≥90%)"] += 1
            elif analysis.readiness_score >= 0.8:
                readiness_ranges["Good (80-89%)"] += 1
            elif analysis.readiness_score >= 0.6:
                readiness_ranges["Fair (60-79%)"] += 1
            else:
                readiness_ranges["Poor (<60%)"] += 1
        for category, count in readiness_ranges.items():
            percentage = (count / report['analysis_summary']['total_services']) * 100
            print(f"   {category}: {count} services ({percentage:.1f}%)")
        print("\n" + "="*80)
def main():
    print("🚀 Starting HMS Enterprise-Grade Microservices Analysis")
    analyzer = MicroservicesAnalysis()
    analyses = analyzer.analyze_all_services()
    report = analyzer.generate_analysis_report()
    analyzer.print_analysis_summary()
    report_file = "/home/azureuser/hms-enterprise-grade/microservices_analysis_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n📄 Detailed analysis report saved to: {report_file}")
    return 0
if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)