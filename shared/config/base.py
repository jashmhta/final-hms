"""
Shared Configuration Base Classes
Eliminates redundant configuration patterns across all services.
"""

import os
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseSettings, Field


class Environment(str, Enum):
    """Environment enumeration."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseConfig(BaseSettings):
    """Database configuration - eliminates redundant database setup."""

    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="hms", env="DB_DATABASE")
    username: str = Field(default="hms", env="DB_USERNAME")
    password: str = Field(default="hms", env="DB_PASSWORD")

    class Config:
        env_prefix = "DB_"

    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def_url_async(self) -> str:
        """Generate async database URL."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class SecurityConfig(BaseSettings):
    """Security configuration - eliminates redundant security setup."""

    secret_key: str = Field(default="your-secret-key", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # HIPAA encryption key
    hipaa_encryption_key: str = Field(default="hipaa-encryption-key", env="HIPAA_ENCRYPTION_KEY")

    class Config:
        env_prefix = "SECURITY_"


class ServiceConfig(BaseSettings):
    """Service configuration - eliminates redundant service setup."""

    name: str = Field(..., env="SERVICE_NAME")
    description: str = Field(..., env="SERVICE_DESCRIPTION")
    version: str = Field(default="1.0.0", env="SERVICE_VERSION")
    host: str = Field(default="0.0.0.0", env="SERVICE_HOST")
    port: int = Field(default=8000, env="SERVICE_PORT")

    # CORS configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")

    # Health check configuration
    health_check_enabled: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")
    health_check_path: str = Field(default="/health", env="HEALTH_CHECK_PATH")

    # Metrics configuration
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    metrics_path: str = Field(default="/metrics", env="METRICS_PATH")

    class Config:
        env_prefix = "SERVICE_"


class MonitoringConfig(BaseSettings):
    """Monitoring configuration - eliminates redundant monitoring setup."""

    # Prometheus metrics
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")

    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")

    # Tracing configuration
    tracing_enabled: bool = Field(default=False, env="TRACING_ENABLED")
    tracing_sampler_rate: float = Field(default=0.1, env="TRACING_SAMPLER_RATE")

    class Config:
        env_prefix = "MONITORING_"


class CacheConfig(BaseSettings):
    """Cache configuration - eliminates redundant cache setup."""

    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")

    # Cache TTL configuration
    default_ttl: int = Field(default=3600, env="CACHE_DEFAULT_TTL")
    short_ttl: int = Field(default=300, env="CACHE_SHORT_TTL")
    long_ttl: int = Field(default=86400, env="CACHE_LONG_TTL")

    class Config:
        env_prefix = "CACHE_"


class MessageQueueConfig(BaseSettings):
    """Message queue configuration - eliminates redundant queue setup."""

    rabbitmq_host: str = Field(default="localhost", env="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, env="RABBITMQ_PORT")
    rabbitmq_username: str = Field(default="guest", env="RABBITMQ_USERNAME")
    rabbitmq_password: str = Field(default="guest", env="RABBITMQ_PASSWORD")
    rabbitmq_vhost: str = Field(default="/", env="RABBITMQ_VHOST")

    class Config:
        env_prefix = "MQ_"


class BaseConfig(BaseSettings):
    """Base configuration combining all settings - eliminates redundant config classes."""

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # Service settings
    service: ServiceConfig = Field(default_factory=ServiceConfig)

    # Database settings
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # Security settings
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # Monitoring settings
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # Cache settings
    cache: CacheConfig = Field(default_factory=CacheConfig)

    # Message queue settings
    message_queue: MessageQueueConfig = Field(default_factory=MessageQueueConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == Environment.TESTING

    def get_service_url(self) -> str:
        """Get service URL."""
        return f"http://{self.service.host}:{self.service.port}"

    def get_database_url(self, async_mode: bool = False) -> str:
        """Get database URL."""
        if async_mode:
            return self.database._url_async
        return self.database.url

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of warnings/errors."""
        warnings = []

        # Security warnings
        if self.security.secret_key == "your-secret-key" and self.is_production:
            warnings.append("Using default secret key in production")

        if self.security.hipaa_encryption_key == "hipaa-encryption-key" and self.is_production:
            warnings.append("Using default HIPAA encryption key in production")

        # Database warnings
        if self.database.password == "hms" and self.is_production:
            warnings.append("Using default database password in production")

        # Service warnings
        if not self.service.name:
            warnings.append("Service name not configured")

        return warnings


class ConfigManager:
    """Configuration manager - eliminates redundant config loading."""

    _instance = None
    _config: Optional[BaseConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_config(self, config_file: Optional[str] = None) -> BaseConfig:
        """Load configuration from environment and optional file."""
        if self._config is None:
            if config_file and os.path.exists(config_file):
                self._config = BaseConfig(_env_file=config_file)
            else:
                self._config = BaseConfig()

            # Validate configuration
            warnings = self._config.validate_config()
            if warnings:
                print("Configuration warnings:")
                for warning in warnings:
                    print(f"  - {warning}")

        return self._config

    def get_config(self) -> BaseConfig:
        """Get current configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config

    def reload_config(self, config_file: Optional[str] = None) -> BaseConfig:
        """Reload configuration."""
        self._config = None
        return self.load_config(config_file)


# Configuration utility functions
def get_config() -> BaseConfig:
    """Get configuration instance."""
    manager = ConfigManager()
    return manager.get_config()


def load_config_from_file(config_file: str) -> BaseConfig:
    """Load configuration from specific file."""
    manager = ConfigManager()
    return manager.load_config(config_file)


def get_environment_config() -> Dict[str, Any]:
    """Get environment-specific configuration."""
    config = get_config()
    env_config = {
        "environment": config.environment.value,
        "debug": config.debug,
        "service_name": config.service.name,
        "service_port": config.service.port,
        "database_url": config.get_database_url(),
        "log_level": config.monitoring.log_level,
    }

    # Add secure fields only in development
    if config.is_development:
        env_config.update({
            "database_password": config.database.password,
            "secret_key": config.security.secret_key,
        })

    return env_config


def create_service_config(
    service_name: str,
    service_description: str,
    version: str = "1.0.0",
    port: int = 8000
) -> BaseConfig:
    """Create service-specific configuration."""
    os.environ["SERVICE_NAME"] = service_name
    os.environ["SERVICE_DESCRIPTION"] = service_description
    os.environ["SERVICE_VERSION"] = version
    os.environ["SERVICE_PORT"] = str(port)

    manager = ConfigManager()
    return manager.load_config()