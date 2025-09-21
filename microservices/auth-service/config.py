"""
Authentication Service Configuration

Centralized configuration management for the Authentication microservice.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field, validator
import secrets

class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Service Configuration
    SERVICE_NAME: str = Field(default="auth-service", env="SERVICE_NAME")
    SERVICE_VERSION: str = Field(default="1.0.0", env="SERVICE_VERSION")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/auth_db",
        env="DATABASE_URL"
    )

    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/1",
        env="REDIS_URL"
    )

    # Security Configuration
    JWT_SECRET_KEY: str = Field(
        default=secrets.token_urlsafe(32),
        env="JWT_SECRET_KEY"
    )
    JWT_REFRESH_SECRET_KEY: str = Field(
        default=secrets.token_urlsafe(32),
        env="JWT_REFRESH_SECRET_KEY"
    )

    # Token Configuration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # MFA Configuration
    MFA_ISSUER_NAME: str = Field(default="HMS Enterprise", env="MFA_ISSUER_NAME")
    MFA_TOKEN_VALIDITY: int = Field(default=30, env="MFA_TOKEN_VALIDITY")
    MFA_BACKUP_CODES_COUNT: int = Field(default=10, env="MFA_BACKUP_CODES_COUNT")

    # Security Policies
    PASSWORD_MIN_LENGTH: int = Field(default=12, env="PASSWORD_MIN_LENGTH")
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    ACCOUNT_LOCKOUT_DURATION: int = Field(default=30, env="ACCOUNT_LOCKOUT_DURATION")  # minutes

    # Monitoring Configuration
    JAEGER_AGENT_HOST: str = Field(default="localhost", env="JAEGER_AGENT_HOST")
    JAEGER_AGENT_PORT: int = Field(default=6831, env="JAEGER_AGENT_PORT")

    # API Configuration
    API_PREFIX: str = Field(default="/api", env="API_PREFIX")
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )

    # Email Configuration
    EMAIL_SERVICE_URL: str = Field(default="http://email-service:8002", env="EMAIL_SERVICE_URL")
    EMAIL_FROM: str = Field(default="noreply@hms.enterprise", env="EMAIL_FROM")

    # Rate Limiting
    RATE_LIMIT_LOGIN: int = Field(default=5, env="RATE_LIMIT_LOGIN")  # per minute
    RATE_LIMIT_REGISTER: int = Field(default=3, env="RATE_LIMIT_REGISTER")  # per minute
    RATE_LIMIT_PASSWORD_RESET: int = Field(default=2, env="RATE_LIMIT_PASSWORD_RESET")  # per hour

    # Session Configuration
    SESSION_TIMEOUT: int = Field(default=1800, env="SESSION_TIMEOUT")  # seconds

    # Audit Configuration
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=365, env="AUDIT_LOG_RETENTION_DAYS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

# Initialize settings
settings = Settings()

# Validate configuration
if len(settings.JWT_SECRET_KEY) < 32:
    print("Warning: JWT_SECRET_KEY is too short, generating a new one")
    settings.JWT_SECRET_KEY = secrets.token_urlsafe(32)

if len(settings.JWT_REFRESH_SECRET_KEY) < 32:
    print("Warning: JWT_REFRESH_SECRET_KEY is too short, generating a new one")
    settings.JWT_REFRESH_SECRET_KEY = secrets.token_urlsafe(32)

# Export configuration
DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_REFRESH_SECRET_KEY = settings.JWT_REFRESH_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
SERVICE_NAME = settings.SERVICE_NAME
SERVICE_VERSION = settings.SERVICE_VERSION
JAEGER_AGENT_HOST = settings.JAEGER_AGENT_HOST
JAEGER_AGENT_PORT = settings.JAEGER_AGENT_PORT
MFA_ISSUER_NAME = settings.MFA_ISSUER_NAME
MFA_TOKEN_VALIDITY = settings.MFA_TOKEN_VALIDITY
EMAIL_SERVICE_URL = settings.EMAIL_SERVICE_URL