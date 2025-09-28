import base64
import hashlib
import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Add libs directory to path for encrypted_model_fields
sys.path.insert(0, str(BASE_DIR / "libs"))

load_dotenv(BASE_DIR / ".env")

# Conditional imports for optional dependencies
if os.getenv("REDIS_URL"):
    try:
        import django_redis

        from core.middleware import PerformanceMonitoringMiddleware
    except ImportError:
        pass

# Enterprise-Grade Configuration
ENTERPRISE_CONFIG = {
    "SECURITY_LEVEL": os.getenv("ENTERPRISE_SECURITY_LEVEL", "enterprise"),
    "PERFORMANCE_LEVEL": os.getenv("ENTERPRISE_PERFORMANCE_LEVEL", "enterprise"),
    "AI_ENABLED": os.getenv("ENTERPRISE_AI_ENABLED", "true").lower() == "true",
    "MONITORING_ENABLED": os.getenv("ENTERPRISE_MONITORING_ENABLED", "true").lower()
    == "true",
    "AUTO_SCALING_ENABLED": os.getenv("ENTERPRISE_AUTO_SCALING_ENABLED", "true").lower()
    == "true",
    "MICROSERVICES_ENABLED": os.getenv(
        "ENTERPRISE_MICROSERVICES_ENABLED", "true"
    ).lower()
    == "true",
}

# Enterprise Security Configuration
ENTERPRISE_SECURITY = {
    "ZERO_TRUST_ENABLED": True,
    "HIPAA_COMPLIANCE_ENABLED": True,
    "GDPR_COMPLIANCE_ENABLED": True,
    "PCI_DSS_COMPLIANCE_ENABLED": True,
    "MFA_REQUIRED": os.getenv("ENTERPRISE_MFA_REQUIRED", "true").lower() == "true",
    "ENCRYPTION_ENABLED": True,
    "AUDIT_LOGGING_ENABLED": True,
    "RATE_LIMITING_ENABLED": True,
}

# Enterprise Performance Configuration
ENTERPRISE_PERFORMANCE = {
    "CACHE_STRATEGY": "multi_level",
    "TARGET_RESPONSE_TIME": 0.1,  # 100ms
    "MAX_CONCURRENT_USERS": 100000,
    "AUTO_SCALING_ENABLED": True,
    "LOAD_BALANCING_ENABLED": True,
    "DATABASE_OPTIMIZATION_ENABLED": True,
    "CDN_ENABLED": True,
}

# Enterprise AI/ML Configuration
ENTERPRISE_AI = {
    "PREDICTIVE_ANALYTICS_ENABLED": True,
    "MEDICAL_IMAGE_ANALYSIS_ENABLED": True,
    "NLP_ENABLED": True,
    "DRUG_INTERACTION_DETECTION_ENABLED": True,
    "CLINICAL_DECISION_SUPPORT_ENABLED": True,
    "MODEL_CACHE_ENABLED": True,
    "REAL_TIME_PREDICTIONS_ENABLED": True,
}

# Enterprise Infrastructure Configuration
ENTERPRISE_INFRASTRUCTURE = {
    "KUBERNETES_ENABLED": True,
    "DOCKER_ENABLED": True,
    "SERVICE_MESH_ENABLED": True,
    "API_GATEWAY_ENABLED": True,
    "MONITORING_STACK": "prometheus_grafana",
    "LOGGING_STACK": "elasticsearch_kibana",
    "MESSAGE_QUEUE": "kafka",
}

# Database Configuration Optimization
if os.getenv("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB"),
            "USER": os.getenv("POSTGRES_USER", ""),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "OPTIONS": {
                "sslmode": "prefer",
                "CONN_MAX_AGE": 600,
                "CONN_HEALTH_CHECKS": True,
                "OPTIONS": "-c default_transaction_isolation=read_committed",
                "connect_timeout": 10,
                "application_name": "hms_enterprise",
            },
            "CONN_MAX_AGE": 600,
            "AUTOCOMMIT": True,
            "DISABLE_SERVER_SIDE_CURSORS": True,
        }
    }
    # Read replica configuration for enterprise scaling
    if os.getenv("POSTGRES_READ_HOST"):
        DATABASES["default"]["TEST"] = {"MIRROR": "default"}
        DATABASES["replica"] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB"),
            "USER": os.getenv("POSTGRES_USER", ""),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_READ_HOST"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "OPTIONS": {
                "sslmode": "prefer",
                "CONN_MAX_AGE": 600,
                "CONN_HEALTH_CHECKS": True,
            },
        }
        DATABASE_ROUTERS = ["core.db_router.DatabaseRouter"]
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }

# Rate limiting configuration
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"

# Authentication rate limiting
AUTH_RATELIMIT = "5/h"
LOGIN_RATELIMIT = "3/m"
PASSWORD_RESET_RATELIMIT = "2/h"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "strong-django-secret-key-2024")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "django_prometheus",
    "django_celery_beat",
    # Core HMS apps - uncomment as dependencies are resolved
    "core",
    "hospitals",
    "users",
    "patients",
    "appointments",
    "ehr",
    "pharmacy",
    "lab",
    "billing",
    "accounting",
    "accounting_advanced",
    "feedback",
    "analytics",
    "hr",
    "facilities",
    "superadmin",
    "authentication",
    "ai_ml",
    # "accounting",
    # "accounting_advanced",
    # "analytics",
    # "feedback",
    # "hr",
    # "facilities",
    # "superadmin",
    # "authentication",
    # "ai_ml",  # Disabled for testing
    # "enterprise_core",  # Disabled for testing
]
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    # Comprehensive logging and monitoring middleware
    "core.logging_monitoring.LoggingMiddleware",
    # Database optimization and monitoring middleware
    "core.query_monitoring.DatabaseHealthMiddleware",
    "core.query_monitoring.QueryOptimizationMiddleware",
    "core.query_monitoring.QueryMonitoringMiddleware",
    "core.query_monitoring.CacheOptimizationMiddleware",
    # Performance and security middleware
    "core.middleware.PerformanceMonitoringMiddleware",
    "core.middleware.APICacheMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.RequestIdMiddleware",
    "core.middleware.SecurityHeadersMiddleware",
    "core.middleware.SecurityAuditMiddleware",
    "core.middleware.RateLimitMiddleware",
    "core.enterprise_middleware.EnterpriseMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]
ROOT_URLCONF = "hms.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "hms.wsgi.application"
FERNET_KEYS = [os.getenv("FERNET_SECRET_KEY", SECRET_KEY)]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.getenv("API_PAGE_SIZE", "25")),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": os.getenv("DRF_USER_THROTTLE", "1000/day"),
        "anon": os.getenv("DRF_ANON_THROTTLE", "100/day"),
        "login": os.getenv("DRF_LOGIN_THROTTLE", "5/min"),
        "register": os.getenv("DRF_REGISTER_THROTTLE", "3/min"),
        "password_reset": os.getenv("DRF_PASSWORD_RESET_THROTTLE", "3/hour"),
        "mfa_setup": os.getenv("DRF_MFA_SETUP_THROTTLE", "10/hour"),
    },
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "EXCEPTION_HANDLER": "core.logging_monitoring.custom_exception_handler",
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MIN", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "1"))),
    "SIGNING_KEY": os.getenv("JWT_SIGNING_KEY", SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Hospital Management System API",
    "DESCRIPTION": "Enterprise-grade Hospital Management System API providing comprehensive healthcare management capabilities including patient records, appointments, billing, pharmacy, laboratory, and administrative functions.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api",
    "SECURITY": [
        {"bearerAuth": []},
    ],
    "COMPONENTS": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
    "TAGS": [
        {
            "name": "authentication",
            "description": "User authentication and authorization",
        },
        {"name": "users", "description": "User management and profiles"},
        {"name": "patients", "description": "Patient information and management"},
        {
            "name": "appointments",
            "description": "Appointment scheduling and management",
        },
        {"name": "ehr", "description": "Electronic Health Records"},
        {"name": "pharmacy", "description": "Pharmacy and medication management"},
        {"name": "lab", "description": "Laboratory test ordering and results"},
        {"name": "billing", "description": "Billing and payment processing"},
        {"name": "accounting", "description": "Financial accounting and reporting"},
        {"name": "analytics", "description": "Healthcare analytics and reporting"},
        {"name": "feedback", "description": "Patient and system feedback"},
        {"name": "hr", "description": "Human resources management"},
        {"name": "facilities", "description": "Hospital facilities management"},
        {"name": "hospitals", "description": "Hospital information and management"},
    ],
    "EXAMPLES": [
        {
            "request": {
                "username": "doctor@example.com",
                "password": "securepassword123",
            },
            "response": {
                "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            },
        }
    ],
}
_cors_all = os.getenv("CORS_ALLOW_ALL_ORIGINS", "false").lower() == "true"
CORS_ALLOW_ALL_ORIGINS = _cors_all and DEBUG
if not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        o for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o
    ]
CSRF_TRUSTED_ORIGINS = (
    os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if os.getenv("CSRF_TRUSTED_ORIGINS")
    else []
)
DEFAULT_APPOINTMENT_SLOT_MINUTES = int(
    os.getenv("DEFAULT_APPOINTMENT_SLOT_MINUTES", "30")
)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = (
    int(os.getenv("SECURE_HSTS_SECONDS", "31536000")) if not DEBUG else 0
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    not DEBUG and os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true"
)
SECURE_HSTS_PRELOAD = (
    not DEBUG and os.getenv("SECURE_HSTS_PRELOAD", "true").lower() == "true"
)
SECURE_SSL_REDIRECT = False
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@example.com")
ADMINS = [("Admin", os.getenv("ADMIN_EMAIL", "admin@example.com"))]
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if not DEBUG else "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "hms.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        },
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "audit.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "json",
        },
        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "security.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "json",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "loggers": {
        "hms.access": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "hms.audit": {
            "handlers": ["console", "audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        "hms.security": {
            "handlers": ["console", "security_file"],
            "level": "INFO",
            "propagate": False,
        },
        "hms.performance": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "hms.error": {
            "handlers": ["console", "error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "hms.business": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO" if not DEBUG else "DEBUG",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
}
if os.getenv("AWS_STORAGE_BUCKET_NAME"):
    INSTALLED_APPS.append("storages")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", None)
    AWS_S3_SIGNATURE_VERSION = os.getenv("AWS_S3_SIGNATURE_VERSION", "s3v4")
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
if os.getenv("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 20,
                    "decode_responses": True,
                    "retry_on_timeout": True,
                    "socket_connect_timeout": 5,
                    "socket_timeout": 5,
                },
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
            },
            "KEY_PREFIX": "hms",
            "TIMEOUT": 300,
            "VERSION": 1,
        },
        "session": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL") + "/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 10,
                    "decode_responses": True,
                },
            },
            "KEY_PREFIX": "session",
            "TIMEOUT": 3600,
        },
        "api_cache": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL") + "/2",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 15,
                    "decode_responses": True,
                },
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            },
            "KEY_PREFIX": "api",
            "TIMEOUT": 600,
        },
        "query_cache": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL") + "/3",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 10,
                    "decode_responses": True,
                },
            },
            "KEY_PREFIX": "query",
            "TIMEOUT": 1800,
        },
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "session"
    CACHE_MIDDLEWARE_ALIAS = "default"
    CACHE_MIDDLEWARE_SECONDS = 600
    CACHE_MIDDLEWARE_KEY_PREFIX = "middleware"
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0")
)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = (
    os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
)
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_TASK_SOFT_TIME_LIMIT = 300
CELERY_TASK_TIME_LIMIT = 600
CELERY_TASK_ROUTES = {
    "core.tasks.send_appointment_reminder": {"queue": "notifications"},
    "core.tasks.cache_warmup": {"queue": "maintenance"},
    "core.tasks.generate_performance_report": {"queue": "monitoring"},
    "core.tasks.optimize_database": {"queue": "maintenance"},
}
CELERY_BEAT_SCHEDULE = {
    "cache-warmup": {
        "task": "core.tasks.cache_warmup",
        "schedule": 1800.0,
    },
    "performance-report": {
        "task": "core.tasks.generate_performance_report",
        "schedule": 86400.0,
    },
    "database-optimization": {
        "task": "core.tasks.optimize_database",
        "schedule": 604800.0,
    },
}
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
    "rest_framework.throttling.UserRateThrottle",
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.ScopedRateThrottle",
]
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(
    {
        "slots": os.getenv("THROTTLE_SLOTS", "60/min"),
        "inventory": os.getenv("THROTTLE_INVENTORY", "60/min"),
    }
)
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25")) if os.getenv("EMAIL_HOST") else None
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "false").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false").lower() == "true"
if os.getenv("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        send_default_pii=False,
    )
# django_celery_beat already included above
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
# Reduced from default 2 weeks to 15 minutes for security
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", "900"))
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
_fe_key = os.getenv("FIELD_ENCRYPTION_KEY")
if not _fe_key:
    digest = hashlib.sha256(SECRET_KEY.encode("utf-8")).digest()
    _fe_key = base64.urlsafe_b64encode(digest).decode("utf-8")
FIELD_ENCRYPTION_KEY = _fe_key
