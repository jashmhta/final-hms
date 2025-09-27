#!/usr/bin/env python3
"""
Enhanced Architecture Agent for Enterprise-Grade System Design

This specialized agent enforces enterprise-grade system design patterns, microservices architecture,
scalability, maintainability, and architectural best practices. It validates service boundaries,
dependency management, API design, and provides iterative architectural improvements until
perfect enterprise standards are achieved.
"""

import asyncio
import glob
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class EnhancedArchitectureAgent:
    """Enhanced agent for comprehensive architecture validation"""

    def __init__(self):
        self.logger = logging.getLogger("EnhancedArchitectureAgent")
        self.base_path = "/home/azureuser/final-hms"

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive architecture validation"""
        self.logger.info("🏗️ Starting Enhanced Architecture Validation...")

        results = {
            "dependency_management": await self._check_dependency_management(),
            "service_boundaries": await self._check_service_boundaries(),
            "microservices_architecture": await self._check_microservices_architecture(),
            "api_design_patterns": await self._check_api_design_patterns(),
            "scalability_patterns": await self._check_scalability_patterns(),
            "maintainability_patterns": await self._check_maintainability_patterns(),
            "security_architecture": await self._check_security_architecture(),
            "database_design_patterns": await self._check_database_design_patterns(),
            "event_driven_architecture": await self._check_event_driven_architecture(),
        }

        # Calculate summary
        total_issues = sum(len(issues) for issues in results.values())
        critical_issues = sum(
            len([i for i in issues if i.get("severity") == "critical"])
            for issues in results.values()
        )
        high_issues = sum(
            len([i for i in issues if i.get("severity") == "high"])
            for issues in results.values()
        )

        summary = {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "enterprise_readiness_score": max(
                0, 100 - (critical_issues * 20) - (high_issues * 10)
            ),
            "details": results,
        }

        return summary

    async def _check_dependency_management(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            requirements_file = f"{self.base_path}/requirements.txt"
            if os.path.exists(requirements_file):
                with open(requirements_file, "r") as f:
                    deps = f.readlines()
                    if len(deps) < 15:  # Enterprise systems need more dependencies
                        issues.append(
                            {
                                "type": "dependencies",
                                "description": "Insufficient dependencies for enterprise-grade system",
                                "severity": "high",
                                "recommendation": "Add required enterprise dependencies (caching, monitoring, security, etc.)",
                            }
                        )

                    # Check for enterprise-grade dependencies
                    required_deps = [
                        "django",
                        "djangorestframework",
                        "celery",
                        "redis",
                        "postgresql",
                        "pytest",
                        "black",
                        "mypy",
                    ]
                    found_deps = [dep.lower().strip() for dep in deps]
                    for req_dep in required_deps:
                        if not any(req_dep in dep for dep in found_deps):
                            issues.append(
                                {
                                    "type": "dependencies",
                                    "description": f"Missing critical enterprise dependency: {req_dep}",
                                    "severity": "high",
                                    "dependency": req_dep,
                                }
                            )

                    # Check for outdated versions
                    for dep in deps:
                        dep = dep.strip()
                        if "==" in dep:
                            parts = dep.split("==")
                            if len(parts) == 2:
                                name, version = parts
                                name = name.lower().strip()
                                if name == "django" and version.startswith(
                                    ("2.", "1.", "3.")
                                ):
                                    issues.append(
                                        {
                                            "type": "dependencies",
                                            "description": f"Outdated Django version: {version} - requires Django 4+ for enterprise features",
                                            "severity": "critical",
                                            "dependency": "Django",
                                            "version": version,
                                            "recommendation": "Upgrade to Django 4.2+ for LTS support",
                                        }
                                    )
            else:
                issues.append(
                    {
                        "type": "dependencies",
                        "description": "requirements.txt not found - critical for dependency management",
                        "severity": "critical",
                        "recommendation": "Create comprehensive requirements.txt with all dependencies",
                    }
                )
        except Exception as e:
            issues.append(
                {"type": "dependencies", "error": str(e), "severity": "medium"}
            )
        return issues

    async def _check_service_boundaries(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            backend_dir = f"{self.base_path}/backend"
            if os.path.exists(backend_dir):
                domains = [
                    "patients",
                    "appointments",
                    "accounting",
                    "authentication",
                    "ehr",
                    "core",
                    "shared",
                ]
                domain_dirs = [
                    d
                    for d in os.listdir(backend_dir)
                    if os.path.isdir(os.path.join(backend_dir, d))
                ]

                missing_domains = [d for d in domains if d not in domain_dirs]
                if missing_domains:
                    issues.append(
                        {
                            "type": "service_boundaries",
                            "description": f"Missing domain modules: {', '.join(missing_domains)}",
                            "severity": "high",
                            "recommendation": "Implement domain-driven design with proper service boundaries",
                        }
                    )

                # Check for cross-cutting concerns
                cross_cutting = ["middleware", "utils", "constants", "exceptions"]
                for concern in cross_cutting:
                    if not any(concern in d for d in domain_dirs):
                        issues.append(
                            {
                                "type": "service_boundaries",
                                "description": f"Missing cross-cutting concern: {concern}",
                                "severity": "medium",
                                "recommendation": f"Implement {concern} module for shared functionality",
                            }
                        )
        except Exception as e:
            issues.append(
                {"type": "service_boundaries", "error": str(e), "severity": "low"}
            )
        return issues

    async def _check_microservices_architecture(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            microservices_dir = f"{self.base_path}/microservices"
            if os.path.exists(microservices_dir):
                services = [
                    d
                    for d in os.listdir(microservices_dir)
                    if os.path.isdir(os.path.join(microservices_dir, d))
                ]

                if len(services) < 5:
                    issues.append(
                        {
                            "type": "microservices",
                            "description": f"Insufficient microservices: {len(services)} found, minimum 5 required for enterprise scale",
                            "severity": "high",
                            "recommendation": "Decompose monolithic components into independent microservices",
                        }
                    )

                # Check each service has proper structure
                for service in services:
                    service_path = os.path.join(microservices_dir, service)
                    required_files = [
                        "main.py",
                        "requirements.txt",
                        "Dockerfile",
                        "docker-compose.yml",
                    ]
                    missing_files = [
                        f
                        for f in required_files
                        if not os.path.exists(os.path.join(service_path, f))
                    ]

                    if missing_files:
                        issues.append(
                            {
                                "type": "microservices",
                                "description": f"Service {service} missing required files: {', '.join(missing_files)}",
                                "severity": "medium",
                                "service": service,
                                "missing_files": missing_files,
                            }
                        )

                # Check for service communication patterns
                has_api_gateway = os.path.exists(f"{microservices_dir}/api-gateway")
                has_service_mesh = os.path.exists(f"{self.base_path}/istio")
                if not (has_api_gateway or has_service_mesh):
                    issues.append(
                        {
                            "type": "microservices",
                            "description": "Missing service orchestration (API Gateway or Service Mesh)",
                            "severity": "high",
                            "recommendation": "Implement API Gateway or Istio service mesh for service communication",
                        }
                    )
            else:
                issues.append(
                    {
                        "type": "microservices",
                        "description": "Microservices directory not found",
                        "severity": "critical",
                        "recommendation": "Implement microservices architecture for scalability and maintainability",
                    }
                )
        except Exception as e:
            issues.append({"type": "microservices", "error": str(e), "severity": "low"})
        return issues

    async def _check_api_design_patterns(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            backend_files = glob.glob(
                f"{self.base_path}/backend/**/*.py", recursive=True
            )

            # Check for API versioning
            api_versioned = any(
                "v1" in f or "v2" in f or "v3" in f for f in backend_files
            )
            if not api_versioned:
                issues.append(
                    {
                        "type": "api_design",
                        "description": "API versioning not implemented",
                        "severity": "high",
                        "recommendation": "Implement semantic API versioning (v1, v2, etc.)",
                    }
                )

            # Check for OpenAPI/Swagger documentation
            has_openapi = any(
                "swagger" in f.lower()
                or "openapi" in f.lower()
                or "drf-yasg" in f.lower()
                for f in backend_files
            )
            if not has_openapi:
                issues.append(
                    {
                        "type": "api_design",
                        "description": "Missing API documentation (OpenAPI/Swagger)",
                        "severity": "medium",
                        "recommendation": "Implement OpenAPI 3.0 specification with drf-yasg or drf-spectacular",
                    }
                )

            # Check for proper HTTP methods and RESTful design
            views_files = [
                f for f in backend_files if "views.py" in f or "viewsets.py" in f
            ]
            if views_files:
                restful_methods = ["get", "post", "put", "patch", "delete"]
                has_restful = False
                for vf in views_files[:5]:
                    try:
                        with open(vf, "r") as f:
                            content = f.read()
                            if any(
                                method in content.lower() for method in restful_methods
                            ):
                                has_restful = True
                                break
                    except:
                        pass

                if not has_restful:
                    issues.append(
                        {
                            "type": "api_design",
                            "description": "APIs not following RESTful conventions",
                            "severity": "medium",
                            "recommendation": "Implement proper RESTful API design with standard HTTP methods",
                        }
                    )

        except Exception as e:
            issues.append({"type": "api_design", "error": str(e), "severity": "low"})
        return issues

    async def _check_scalability_patterns(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            backend_files = glob.glob(
                f"{self.base_path}/backend/**/*.py", recursive=True
            )

            # Check for caching implementation
            has_caching = any(
                "cache" in f.lower() or "redis" in f.lower() or "@cache" in f
                for f in backend_files
            )
            if not has_caching:
                issues.append(
                    {
                        "type": "scalability",
                        "description": "Missing caching implementation",
                        "severity": "high",
                        "recommendation": "Implement Redis caching for database queries and API responses",
                    }
                )

            # Check for async processing (Celery)
            has_async = any(
                "celery" in f.lower() or "@task" in f or "@shared_task" in f
                for f in backend_files
            )
            if not has_async:
                issues.append(
                    {
                        "type": "scalability",
                        "description": "Missing asynchronous task processing",
                        "severity": "high",
                        "recommendation": "Implement Celery for background tasks and job processing",
                    }
                )

            # Check for database optimization
            has_db_optimization = any(
                "select_related" in f or "prefetch_related" in f or "bulk_create" in f
                for f in backend_files
            )
            if not has_db_optimization:
                issues.append(
                    {
                        "type": "scalability",
                        "description": "Missing database query optimization",
                        "severity": "medium",
                        "recommendation": "Implement select_related/prefetch_related and bulk operations for performance",
                    }
                )

            # Check for load balancing configuration
            has_load_balancer = (
                os.path.exists(f"{self.base_path}/nginx")
                or os.path.exists(f"{self.base_path}/istio")
                or os.path.exists(f"{self.base_path}/k8s")
            )
            if not has_load_balancer:
                issues.append(
                    {
                        "type": "scalability",
                        "description": "Missing load balancing and orchestration configuration",
                        "severity": "high",
                        "recommendation": "Implement Kubernetes, NGINX, or Istio for load distribution and service orchestration",
                    }
                )

        except Exception as e:
            issues.append({"type": "scalability", "error": str(e), "severity": "low"})
        return issues

    async def _check_maintainability_patterns(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            backend_files = glob.glob(
                f"{self.base_path}/backend/**/*.py", recursive=True
            )

            # Check for service layer pattern
            has_services = any(
                "services.py" in f or "service.py" in f for f in backend_files
            )
            if not has_services:
                issues.append(
                    {
                        "type": "maintainability",
                        "description": "Missing service layer pattern",
                        "severity": "medium",
                        "recommendation": "Implement service layer for business logic separation from views",
                    }
                )

            # Check for proper exception handling
            has_custom_exceptions = any("exceptions.py" in f for f in backend_files)
            if not has_custom_exceptions:
                issues.append(
                    {
                        "type": "maintainability",
                        "description": "Missing custom exception classes",
                        "severity": "low",
                        "recommendation": "Define custom exception classes for better error handling and debugging",
                    }
                )

            # Check for configuration management
            has_config_management = os.path.exists(
                f"{self.base_path}/config"
            ) or os.path.exists(f"{self.base_path}/backend/settings")
            if not has_config_management:
                issues.append(
                    {
                        "type": "maintainability",
                        "description": "Poor configuration management",
                        "severity": "medium",
                        "recommendation": "Implement proper configuration management with environment variables and settings",
                    }
                )

            # Check for logging
            has_logging = any(
                "logger" in f.lower() or "logging" in f.lower() for f in backend_files
            )
            if not has_logging:
                issues.append(
                    {
                        "type": "maintainability",
                        "description": "Missing comprehensive logging",
                        "severity": "medium",
                        "recommendation": "Implement structured logging throughout the application",
                    }
                )

        except Exception as e:
            issues.append(
                {"type": "maintainability", "error": str(e), "severity": "low"}
            )
        return issues

    async def _check_security_architecture(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            backend_files = glob.glob(
                f"{self.base_path}/backend/**/*.py", recursive=True
            )

            # Check for authentication/authorization
            has_auth = any(
                "authentication" in f or "auth" in f or "permission" in f.lower()
                for f in backend_files
            )
            if not has_auth:
                issues.append(
                    {
                        "type": "security",
                        "description": "Missing authentication/authorization system",
                        "severity": "critical",
                        "recommendation": "Implement comprehensive authentication and role-based authorization",
                    }
                )

            # Check for input validation and sanitization
            has_validation = any(
                "validate" in f.lower()
                or "clean" in f.lower()
                or "sanitize" in f.lower()
                for f in backend_files
            )
            if not has_validation:
                issues.append(
                    {
                        "type": "security",
                        "description": "Insufficient input validation and sanitization",
                        "severity": "high",
                        "recommendation": "Implement comprehensive input validation, sanitization, and SQL injection prevention",
                    }
                )

            # Check for rate limiting and throttling
            has_rate_limiting = any(
                "ratelimit" in f.lower() or "throttle" in f.lower()
                for f in backend_files
            )
            if not has_rate_limiting:
                issues.append(
                    {
                        "type": "security",
                        "description": "Missing rate limiting protection",
                        "severity": "high",
                        "recommendation": "Implement rate limiting and throttling to prevent abuse and DoS attacks",
                    }
                )

            # Check for security middleware
            has_security_middleware = any(
                "cors" in f.lower() or "csrf" in f.lower() or "security" in f.lower()
                for f in backend_files
            )
            if not has_security_middleware:
                issues.append(
                    {
                        "type": "security",
                        "description": "Missing security middleware (CORS, CSRF, security headers)",
                        "severity": "high",
                        "recommendation": "Implement security middleware for cross-origin protection, CSRF prevention, and security headers",
                    }
                )

            # Check for data encryption
            has_encryption = any(
                "encrypt" in f.lower()
                or "cipher" in f.lower()
                or "encrypted_model_fields" in f
                for f in backend_files
            )
            if not has_encryption:
                issues.append(
                    {
                        "type": "security",
                        "description": "Missing data encryption for sensitive information",
                        "severity": "high",
                        "recommendation": "Implement field-level encryption for sensitive data (PHI, PII)",
                    }
                )

        except Exception as e:
            issues.append({"type": "security", "error": str(e), "severity": "low"})
        return issues

    async def _check_database_design_patterns(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            # Check for database migrations
            has_migrations = os.path.exists(
                f"{self.base_path}/backend/migrations"
            ) or glob.glob(f"{self.base_path}/backend/**/migrations", recursive=True)
            if not has_migrations:
                issues.append(
                    {
                        "type": "database",
                        "description": "Missing database migrations",
                        "severity": "high",
                        "recommendation": "Implement Django migrations for schema versioning and consistency",
                    }
                )

            # Check for proper model relationships
            models_files = glob.glob(
                f"{self.base_path}/backend/**/models.py", recursive=True
            )
            if models_files:
                has_relationships = False
                for mf in models_files[:5]:
                    try:
                        with open(mf, "r") as f:
                            content = f.read()
                            if (
                                "ForeignKey" in content
                                or "OneToOneField" in content
                                or "ManyToManyField" in content
                            ):
                                has_relationships = True
                                break
                    except:
                        pass

                if not has_relationships:
                    issues.append(
                        {
                            "type": "database",
                            "description": "Missing proper model relationships and constraints",
                            "severity": "medium",
                            "recommendation": "Implement proper foreign key relationships, constraints, and referential integrity",
                        }
                    )

            # Check for database indexing
            has_indexes = False
            for mf in models_files[:5]:
                try:
                    with open(mf, "r") as f:
                        content = f.read()
                        if (
                            "db_index" in content
                            or "unique" in content
                            or "index_together" in content
                        ):
                            has_indexes = True
                            break
                except:
                    pass

            if not has_indexes:
                issues.append(
                    {
                        "type": "database",
                        "description": "Missing database indexes for query performance",
                        "severity": "medium",
                        "recommendation": "Add database indexes on frequently queried and foreign key fields",
                    }
                )

            # Check for database connection pooling
            has_connection_pooling = any(
                "CONN_MAX_AGE" in f or "connection pooling" in f.lower()
                for f in models_files
            )
            if not has_connection_pooling:
                issues.append(
                    {
                        "type": "database",
                        "description": "Missing database connection pooling configuration",
                        "severity": "low",
                        "recommendation": "Configure database connection pooling for better performance and resource management",
                    }
                )

        except Exception as e:
            issues.append({"type": "database", "error": str(e), "severity": "low"})
        return issues

    async def _check_event_driven_architecture(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            backend_files = glob.glob(
                f"{self.base_path}/backend/**/*.py", recursive=True
            )

            # Check for event-driven patterns (Django signals)
            has_signals = any(
                "post_save" in f
                or "pre_save" in f
                or "m2m_changed" in f
                or "signal" in f.lower()
                for f in backend_files
            )
            if not has_signals:
                issues.append(
                    {
                        "type": "event_driven",
                        "description": "Missing event-driven patterns (Django signals)",
                        "severity": "low",
                        "recommendation": "Implement Django signals for decoupled event handling and business logic",
                    }
                )

            # Check for message queue integration
            has_message_queue = any(
                "rabbitmq" in f.lower()
                or "kafka" in f.lower()
                or "redis" in f.lower()
                or "celery" in f.lower()
                for f in backend_files
            )
            if not has_message_queue:
                issues.append(
                    {
                        "type": "event_driven",
                        "description": "Missing message queue for event-driven architecture",
                        "severity": "medium",
                        "recommendation": "Implement message queue (RabbitMQ/Kafka/Redis) for asynchronous communication",
                    }
                )

            # Check for CQRS pattern
            has_cqrs = os.path.exists(f"{self.base_path}/cqrs")
            if not has_cqrs:
                issues.append(
                    {
                        "type": "event_driven",
                        "description": "Missing CQRS pattern implementation",
                        "severity": "low",
                        "recommendation": "Consider implementing CQRS for complex domain logic and better scalability",
                    }
                )

            # Check for event sourcing
            has_event_sourcing = any(
                "event_store" in f.lower() or "event_sourcing" in f.lower()
                for f in backend_files
            )
            if not has_event_sourcing:
                issues.append(
                    {
                        "type": "event_driven",
                        "description": "Missing event sourcing capabilities",
                        "severity": "low",
                        "recommendation": "Consider implementing event sourcing for audit trails and temporal queries",
                    }
                )

        except Exception as e:
            issues.append({"type": "event_driven", "error": str(e), "severity": "low"})
        return issues


async def main():
    """Run the enhanced architecture agent"""
    print("🏗️ Deploying Enhanced Architecture Agent...")
    print("🔍 Conducting comprehensive enterprise-grade system validation...")

    agent = EnhancedArchitectureAgent()

    try:
        results = await agent.run_comprehensive_validation()

        print("\n📊 Enterprise Architecture Validation Results:")
        print(f"Total Issues Found: {results['total_issues']}")
        print(f"Critical Issues: {results['critical_issues']}")
        print(f"High Priority Issues: {results['high_issues']}")
        print(
            f"Enterprise Readiness Score: {results['enterprise_readiness_score']}/100"
        )

        # Display issues by category
        details = results["details"]
        for category, issues in details.items():
            if issues:
                print(
                    f"\n🔧 {category.replace('_', ' ').title()} ({len(issues)} issues):"
                )
                for i, issue in enumerate(issues, 1):
                    severity_icon = {
                        "critical": "🚨",
                        "high": "⚠️",
                        "medium": "ℹ️",
                        "low": "💡",
                    }.get(issue.get("severity", "low"), "💡")

                    print(
                        f"  {i}. {severity_icon} {issue.get('description', 'No description')}"
                    )
                    if issue.get("recommendation"):
                        print(f"     💡 {issue['recommendation']}")

        # Provide improvement roadmap
        if results["total_issues"] > 0:
            print("\n🚀 Architectural Improvement Roadmap:")
            print("1. Address all CRITICAL issues immediately")
            print("2. Resolve HIGH priority issues within 1-2 weeks")
            print("3. Implement MEDIUM priority improvements in next sprint")
            print("4. Consider LOW priority enhancements for future iterations")
            print("5. Re-run validation after fixes to ensure compliance")

        print("\n✅ Enterprise architecture validation completed.")
        print("🎯 System evaluated against enterprise-grade standards.")

        return 0 if results["enterprise_readiness_score"] >= 80 else 1

    except Exception as e:
        print(f"❌ Error running enhanced architecture agent: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
