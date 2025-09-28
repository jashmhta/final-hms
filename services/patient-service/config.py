"""
Patient Service Configuration

Centralized configuration management for the Patient microservice.
"""

import os
from typing import Optional

from cryptography.fernet import Fernet
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Service Configuration
    SERVICE_NAME: str = Field(default="patient-service", env="SERVICE_NAME")
    SERVICE_VERSION: str = Field(default="1.0.0", env="SERVICE_VERSION")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/patient_db",
        env="DATABASE_URL",
    )

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Security Configuration
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production", env="JWT_SECRET_KEY"
    )
    ENCRYPTION_KEY: str = Field(
        default="your-encryption-key-change-in-production", env="ENCRYPTION_KEY"
    )

    # Monitoring Configuration
    JAEGER_AGENT_HOST: str = Field(default="localhost", env="JAEGER_AGENT_HOST")
    JAEGER_AGENT_PORT: int = Field(default=6831, env="JAEGER_AGENT_PORT")

    # API Configuration
    API_PREFIX: str = Field(default="/api", env="API_PREFIX")
    CORS_ORIGINS: list = Field(default=["*"], env="CORS_ORIGINS")

    # Performance Configuration
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT"
    )

    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Initialize settings
settings = Settings()

# Validate encryption key
try:
    # Test if the encryption key is valid
    test_key = settings.ENCRYPTION_KEY
    if len(test_key) < 32:
        # Generate a new key if invalid
        test_key = Fernet.generate_key().decode()
        print(f"Warning: Generated new encryption key: {test_key}")
except Exception as e:
    print(f"Warning: Invalid encryption key, generating new one: {e}")
    settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

# Validate database URL
if not settings.DATABASE_URL or "postgresql://" not in settings.DATABASE_URL:
    print("Warning: Invalid DATABASE_URL, using default PostgreSQL configuration")

# Validate Redis URL
if not settings.REDIS_URL or "redis://" not in settings.REDIS_URL:
    print("Warning: Invalid REDIS_URL, using default Redis configuration")

# Export configuration
DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
ENCRYPTION_KEY = (
    settings.ENCRYPTION_KEY.encode()
    if isinstance(settings.ENCRYPTION_KEY, str)
    else settings.ENCRYPTION_KEY
)
SERVICE_NAME = settings.SERVICE_NAME
SERVICE_VERSION = settings.SERVICE_VERSION
JAEGER_AGENT_HOST = settings.JAEGER_AGENT_HOST
JAEGER_AGENT_PORT = settings.JAEGER_AGENT_PORT
