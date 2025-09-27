#!/usr/bin/env python3
"""
HMS Enterprise-Grade Configuration Generator
Automates creation of service configurations to eliminate redundancy.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, Template


class ConfigGenerator:
    """Generates standardized configurations for HMS services."""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"

        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_docker_compose(
        self,
        service_name: str,
        service_description: str,
        version: str = "1.0.0",
        service_port: int = 8000,
        db_port: int = None,
        redis_port: int = None,
        output_file: str = None,
        **kwargs,
    ) -> str:
        """Generate docker-compose.yml from template."""
        template = self.env.get_template("docker/docker-compose.template.yml")

        # Default values
        if db_port is None:
            db_port = 5432 + (service_port - 8000)
        if redis_port is None:
            redis_port = 6379 + (service_port - 8000)

        # Configuration context
        context = {
            "SERVICE_NAME": service_name.lower().replace("-", "_"),
            "SERVICE_DESCRIPTION": service_description,
            "SERVICE_VERSION": version,
            "SERVICE_PORT": service_port,
            "CONTAINER_PORT": 8000,
            "DATABASE_NAME": f"{service_name.lower().replace('-', '_')}_db",
            "DATABASE_USER": "hms",
            "DATABASE_PASSWORD": "hms",
            "DB_PORT": db_port,
            "REDIS_PORT": redis_port,
            "ENVIRONMENT": kwargs.get("environment", "development"),
            "LOG_LEVEL": kwargs.get("log_level", "INFO"),
            "CORS_ORIGINS": kwargs.get("cors_origins", "*"),
            "NETWORK_SUBNET": "172.20.0.0/16",
            # Optional services ports
            "PROMETHEUS_PORT": kwargs.get("prometheus_port", 9090),
            "GRAFANA_PORT": kwargs.get("grafana_port", 3000),
            "RABBITMQ_PORT": kwargs.get("rabbitmq_port", 5672),
            "RABBITMQ_MGMT_PORT": kwargs.get("rabbitmq_mgmt_port", 15672),
            "RABBITMQ_USER": kwargs.get("rabbitmq_user", "guest"),
            "RABBITMQ_PASSWORD": kwargs.get("rabbitmq_password", "guest"),
        }

        # Generate configuration
        config = template.render(**context)

        # Save to file if specified
        if output_file:
            self._save_config(config, output_file)

        return config

    def generate_k8s_deployment(
        self,
        service_name: str,
        service_description: str,
        version: str = "1.0.0",
        namespace: str = "default",
        output_file: str = None,
        **kwargs,
    ) -> str:
        """Generate Kubernetes deployment manifests."""
        template = self.env.get_template("k8s/deployment.template.yaml")

        # Configuration context
        context = {
            "SERVICE_NAME": service_name.lower().replace("-", "_"),
            "SERVICE_DESCRIPTION": service_description,
            "SERVICE_VERSION": version,
            "NAMESPACE": namespace,
            "CONTAINER_PORT": 8000,
            "SERVICE_PORT": kwargs.get("service_port", 80),
            "SERVICE_TYPE": kwargs.get("service_type", "ClusterIP"),
            "REPLICAS": kwargs.get("replicas", 2),
            "MIN_REPLICAS": kwargs.get("min_replicas", 2),
            "MAX_REPLICAS": kwargs.get("max_replicas", 10),
            "IMAGE_REGISTRY": kwargs.get("image_registry", "hms-enterprise"),
            "IMAGE_NAME": service_name.lower().replace("-", "_"),
            "IMAGE_TAG": version,
            "IMAGE_PULL_POLICY": kwargs.get("image_pull_policy", "IfNotPresent"),
            # Resource limits
            "MEMORY_REQUEST": kwargs.get("memory_request", "256Mi"),
            "MEMORY_LIMIT": kwargs.get("memory_limit", "512Mi"),
            "CPU_REQUEST": kwargs.get("cpu_request", "250m"),
            "CPU_LIMIT": kwargs.get("cpu_limit", "500m"),
            # Health checks
            "LIVENESS_INITIAL_DELAY": kwargs.get("liveness_initial_delay", 30),
            "LIVENESS_PERIOD": kwargs.get("liveness_period", 10),
            "LIVENESS_TIMEOUT": kwargs.get("liveness_timeout", 5),
            "LIVENESS_FAILURE_THRESHOLD": kwargs.get("liveness_failure_threshold", 3),
            "LIVENESS_SUCCESS_THRESHOLD": kwargs.get("liveness_success_threshold", 1),
            "READINESS_INITIAL_DELAY": kwargs.get("readiness_initial_delay", 5),
            "READINESS_PERIOD": kwargs.get("readiness_period", 5),
            "READINESS_TIMEOUT": kwargs.get("readiness_timeout", 3),
            "READINESS_FAILURE_THRESHOLD": kwargs.get("readiness_failure_threshold", 3),
            "READINESS_SUCCESS_THRESHOLD": kwargs.get("readiness_success_threshold", 1),
            # Scaling
            "MAX_SURGE": kwargs.get("max_surge", "25%"),
            "MAX_UNAVAILABLE": kwargs.get("max_unavailable", "25%"),
            # Autoscaling
            "CPU_TARGET_UTILIZATION": kwargs.get("cpu_target_utilization", 70),
            "MEMORY_TARGET_UTILIZATION": kwargs.get("memory_target_utilization", 80),
            "MIN_AVAILABLE": kwargs.get("min_available", 1),
            # Security
            "RUN_AS_NON_ROOT": kwargs.get("run_as_non_root", True),
            "RUN_AS_USER": kwargs.get("run_as_user", 1000),
            "RUN_AS_GROUP": kwargs.get("run_as_group", 1000),
            "READ_ONLY_ROOT_FILESYSTEM": kwargs.get("read_only_root_filesystem", True),
            "ALLOW_PRIVILEGE_ESCALATION": kwargs.get(
                "allow_privilege_escalation", False
            ),
            # External service references
            "DATABASE_SECRET_NAME": kwargs.get(
                "database_secret_name", f"{service_name}-db-secret"
            ),
            "SECURITY_SECRET_NAME": kwargs.get(
                "security_secret_name", f"{service_name}-security-secret"
            ),
            "REDIS_HOST": kwargs.get("redis_host", "redis-service"),
            "REDIS_PORT": kwargs.get("redis_port", 6379),
            "RABBITMQ_HOST": kwargs.get("rabbitmq_host", "rabbitmq-service"),
            "RABBITMQ_PORT": kwargs.get("rabbitmq_port", 5672),
            "LOG_LEVEL": kwargs.get("log_level", "INFO"),
            "PROMETHEUS_ENABLED": kwargs.get("prometheus_enabled", "true"),
            "METRICS_ENABLED": kwargs.get("metrics_enabled", "true"),
            "ENVIRONMENT": kwargs.get("environment", "development"),
            # Optional configurations
            "CONFIG_CHECKSUM": kwargs.get("config_checksum", "latest"),
            "SERVICE_ACCOUNT_NAME": kwargs.get("service_account_name"),
            "NODE_PORT": kwargs.get("node_port"),
            "SERVICE_ANNOTATIONS": kwargs.get("service_annotations"),
            "NODE_SELECTOR": kwargs.get("node_selector"),
            "TOLERATIONS": kwargs.get("tolerations"),
            "AFFINITY": kwargs.get("affinity"),
            "TOPOLOGY_SPREAD_CONSTRAINTS": kwargs.get("topology_spread_constraints"),
            "CUSTOM_METRICS": kwargs.get("custom_metrics"),
            "TLS_VOLUME_MOUNTS": kwargs.get("tls_volume_mounts"),
            "TLS_VOLUMES": kwargs.get("tls_volumes"),
            "CAPABILITIES_TO_ADD": kwargs.get("capabilities_to_add"),
        }

        # Generate configuration
        config = template.render(**context)

        # Save to file if specified
        if output_file:
            self._save_config(config, output_file)

        return config

    def generate_service_config(
        self,
        service_name: str,
        service_description: str,
        version: str = "1.0.0",
        output_file: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate service configuration dictionary."""
        config = {
            "service": {
                "name": service_name,
                "description": service_description,
                "version": version,
                "port": kwargs.get("port", 8000),
                "host": kwargs.get("host", "0.0.0.0"),
                "environment": kwargs.get("environment", "development"),
            },
            "database": {
                "host": kwargs.get("db_host", "localhost"),
                "port": kwargs.get("db_port", 5432),
                "database": kwargs.get(
                    "db_database", f"{service_name.lower().replace('-', '_')}_db"
                ),
                "username": kwargs.get("db_username", "hms"),
                "password": kwargs.get("db_password", "hms"),
            },
            "redis": {
                "host": kwargs.get("redis_host", "localhost"),
                "port": kwargs.get("redis_port", 6379),
                "password": kwargs.get("redis_password"),
                "db": kwargs.get("redis_db", 0),
            },
            "security": {
                "secret_key": kwargs.get(
                    "secret_key", "your-secret-key-change-in-production"
                ),
                "algorithm": kwargs.get("algorithm", "HS256"),
                "access_token_expire_minutes": kwargs.get(
                    "access_token_expire_minutes", 30
                ),
                "hipaa_encryption_key": kwargs.get(
                    "hipaa_encryption_key", "your-hipaa-key-change-in-production"
                ),
            },
            "monitoring": {
                "log_level": kwargs.get("log_level", "INFO"),
                "prometheus_enabled": kwargs.get("prometheus_enabled", True),
                "metrics_enabled": kwargs.get("metrics_enabled", True),
                "tracing_enabled": kwargs.get("tracing_enabled", False),
            },
            "cors": {
                "origins": kwargs.get("cors_origins", ["*"]),
                "allow_credentials": kwargs.get("allow_credentials", True),
                "allow_methods": kwargs.get("allow_methods", ["*"]),
                "allow_headers": kwargs.get("allow_headers", ["*"]),
            },
        }

        # Save to file if specified
        if output_file:
            self._save_config_json(config, output_file)

        return config

    def generate_env_file(
        self, service_config: Dict[str, Any], output_file: str = ".env"
    ) -> str:
        """Generate .env file from service configuration."""
        env_lines = []

        # Service configuration
        service = service_config.get("service", {})
        env_lines.extend(
            [
                f"SERVICE_NAME={service.get('name', '')}",
                f"SERVICE_DESCRIPTION={service.get('description', '')}",
                f"SERVICE_VERSION={service.get('version', '1.0.0')}",
                f"SERVICE_PORT={service.get('port', 8000)}",
                f"SERVICE_HOST={service.get('host', '0.0.0.0')}",
                f"ENVIRONMENT={service.get('environment', 'development')}",
            ]
        )

        # Database configuration
        database = service_config.get("database", {})
        env_lines.extend(
            [
                f"DB_HOST={database.get('host', 'localhost')}",
                f"DB_PORT={database.get('port', 5432)}",
                f"DB_DATABASE={database.get('database', 'hms')}",
                f"DB_USERNAME={database.get('username', 'hms')}",
                f"DB_PASSWORD={database.get('password', 'hms')}",
            ]
        )

        # Redis configuration
        redis = service_config.get("redis", {})
        env_lines.extend(
            [
                f"REDIS_HOST={redis.get('host', 'localhost')}",
                f"REDIS_PORT={redis.get('port', 6379)}",
                f"REDIS_PASSWORD={redis.get('password', '')}",
                f"REDIS_DB={redis.get('db', 0)}",
            ]
        )

        # Security configuration
        security = service_config.get("security", {})
        env_lines.extend(
            [
                f"SECRET_KEY={security.get('secret_key', '')}",
                f"ALGORITHM={security.get('algorithm', 'HS256')}",
                f"ACCESS_TOKEN_EXPIRE_MINUTES={security.get('access_token_expire_minutes', 30)}",
                f"HIPAA_ENCRYPTION_KEY={security.get('hipaa_encryption_key', '')}",
            ]
        )

        # Monitoring configuration
        monitoring = service_config.get("monitoring", {})
        env_lines.extend(
            [
                f"LOG_LEVEL={monitoring.get('log_level', 'INFO')}",
                f"PROMETHEUS_ENABLED={monitoring.get('prometheus_enabled', True)}",
                f"METRICS_ENABLED={monitoring.get('metrics_enabled', True)}",
                f"TRACING_ENABLED={monitoring.get('tracing_enabled', False)}",
            ]
        )

        # CORS configuration
        cors = service_config.get("cors", {})
        env_lines.append(f"CORS_ORIGINS={','.join(cors.get('origins', ['*']))}")

        env_content = "\n".join(env_lines)

        # Save to file
        if output_file:
            self._save_config(env_content, output_file)

        return env_content

    def _save_config(self, config: str, output_file: str):
        """Save configuration to file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(config)
        print(f"Configuration saved to: {output_path}")

    def _save_config_json(self, config: Dict[str, Any], output_file: str):
        """Save JSON configuration to file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, default=str)
        print(f"Configuration saved to: {output_path}")


def main():
    """Command line interface for configuration generator."""
    parser = argparse.ArgumentParser(
        description="Generate HMS Enterprise-Grade service configurations"
    )
    parser.add_argument("service_name", help="Name of the service")
    parser.add_argument("service_description", help="Description of the service")
    parser.add_argument("--version", default="1.0.0", help="Service version")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument(
        "--generate",
        choices=["docker-compose", "k8s", "config", "env", "all"],
        default="all",
        help="What to generate",
    )

    args = parser.parse_args()

    generator = ConfigGenerator()
    service_name = args.service_name.lower().replace("-", "_")
    output_dir = Path(args.output_dir)

    if args.generate in ["docker-compose", "all"]:
        print(f"Generating Docker Compose configuration for {service_name}...")
        docker_compose = generator.generate_docker_compose(
            service_name=args.service_name,
            service_description=args.service_description,
            version=args.version,
            output_file=str(output_dir / "docker-compose.yml"),
        )

    if args.generate in ["k8s", "all"]:
        print(f"Generating Kubernetes configuration for {service_name}...")
        k8s_config = generator.generate_k8s_deployment(
            service_name=args.service_name,
            service_description=args.service_description,
            version=args.version,
            output_file=str(output_dir / "k8s-deployment.yaml"),
        )

    if args.generate in ["config", "all"]:
        print(f"Generating service configuration for {service_name}...")
        service_config = generator.generate_service_config(
            service_name=args.service_name,
            service_description=args.service_description,
            version=args.version,
            output_file=str(output_dir / "service-config.json"),
        )

        if args.generate in ["env", "all"]:
            print(f"Generating .env file for {service_name}...")
            generator.generate_env_file(
                service_config, output_file=str(output_dir / ".env")
            )

    print(f"\nConfiguration generation completed for {service_name}!")
    print(f"Output files saved to: {output_dir}")


if __name__ == "__main__":
    main()
