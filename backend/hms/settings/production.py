import os
from urllib.parse import urlparse
from .base import *
DEBUG = False
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")
ALLOWED_HOSTS = [
    "hms.yourdomain.com",
    "api.hms.yourdomain.com",
    "*.hms.yourdomain.com",
    "localhost",  
]
DATABASE_URL = os.environ.get("DATABASE_URL")
ACCOUNTING_DB_URL = os.environ.get("ACCOUNTING_DB_URL", DATABASE_URL)
ANALYTICS_DB_URL = os.environ.get("ANALYTICS_DB_URL", DATABASE_URL)
APPOINTMENTS_DB_URL = os.environ.get("APPOINTMENTS_DB_URL", DATABASE_URL)
BILLING_DB_URL = os.environ.get("BILLING_DB_URL", DATABASE_URL)
EHR_DB_URL = os.environ.get("EHR_DB_URL", DATABASE_URL)
FACILITIES_DB_URL = os.environ.get("FACILITIES_DB_URL", DATABASE_URL)
HR_DB_URL = os.environ.get("HR_DB_URL", DATABASE_URL)
LAB_DB_URL = os.environ.get("LAB_DB_URL", DATABASE_URL)
PATIENTS_DB_URL = os.environ.get("PATIENTS_DB_URL", DATABASE_URL)
PHARMACY_DB_URL = os.environ.get("PHARMACY_DB_URL", DATABASE_URL)
USERS_DB_URL = os.environ.get("USERS_DB_URL", DATABASE_URL)
def parse_db_url(db_url):
    if not db_url:
        return None
    url = urlparse(db_url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": url.path[1:],
        "USER": url.username,
        "PASSWORD": url.password,
        "HOST": url.hostname,
        "PORT": url.port or 5432,
        "OPTIONS": {
            "sslmode": "require",
            "connect_timeout": 60,
            "options": "-c default_transaction_isolation=serializable",
        },
        "CONN_MAX_AGE": 600,
        "CONN_HEALTH_CHECKS": True,
    }
DATABASES = {
    "default": parse_db_url(DATABASE_URL) or {},
    "accounting": parse_db_url(ACCOUNTING_DB_URL) or parse_db_url(DATABASE_URL),
    "analytics": parse_db_url(ANALYTICS_DB_URL) or parse_db_url(DATABASE_URL),
    "appointments": parse_db_url(APPOINTMENTS_DB_URL) or parse_db_url(DATABASE_URL),
    "billing": parse_db_url(BILLING_DB_URL) or parse_db_url(DATABASE_URL),
    "ehr": parse_db_url(EHR_DB_URL) or parse_db_url(DATABASE_URL),
    "facilities": parse_db_url(FACILITIES_DB_URL) or parse_db_url(DATABASE_URL),
    "hr": parse_db_url(HR_DB_URL) or parse_db_url(DATABASE_URL),
    "lab": parse_db_url(LAB_DB_URL) or parse_db_url(DATABASE_URL),
    "patients": parse_db_url(PATIENTS_DB_URL) or parse_db_url(DATABASE_URL),
    "pharmacy": parse_db_url(PHARMACY_DB_URL) or parse_db_url(DATABASE_URL),
    "users": parse_db_url(USERS_DB_URL) or parse_db_url(DATABASE_URL),
}
if not DATABASES["default"]:
    raise ValueError("DATABASE_URL environment variable is required")
DATABASE_ROUTERS = ["core.routers.DatabaseRouter"]
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis-service:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 100,
                "retry_on_timeout": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            },
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
        },
        "KEY_PREFIX": "hms_prod",
        "TIMEOUT": 300,
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 1800  
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_TRUSTED_ORIGINS = [
    "https://hms.yourdomain.com",
    "https://api.hms.yourdomain.com",
]
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000  
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_PERMISSIONS_POLICY = {
    "accelerometer": [],
    "ambient-light-sensor": [],
    "autoplay": [],
    "battery": [],
    "camera": ["self"],
    "clipboard-read": [],
    "clipboard-write": ["self"],
    "display-capture": [],
    "document-domain": [],
    "encrypted-media": [],
    "execution-while-not-rendered": [],
    "execution-while-out-of-viewport": [],
    "fullscreen": ["self"],
    "gamepad": [],
    "geolocation": [],
    "gyroscope": [],
    "hid": [],
    "idle-detection": [],
    "local-fonts": [],
    "magnetometer": [],
    "microphone": ["self"],
    "midi": [],
    "navigation-override": [],
    "payment": ["self"],
    "picture-in-picture": [],
    "publickey-credentials-get": ["self"],
    "screen-wake-lock": [],
    "serial": [],
    "speaker-selection": [],
    "sync-xhr": [],
    "usb": [],
    "web-share": [],
    "xr-spatial-tracking": [],
}
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.jsdelivr.net",
    "https://unpkg.com",
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://fonts.googleapis.com",
    "https://cdn.jsdelivr.net",
)
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "data:")
CSP_IMG_SRC = ("'self'", "data:", "https:", "blob:")
CSP_CONNECT_SRC = (
    "'self'",
    "https://api.hms.yourdomain.com",
    "wss://api.hms.yourdomain.com",
)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FORM_ACTION = ("'self'",)
CSP_BASE_URI = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_MEDIA_SRC = ("'self'", "https:", "blob:")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/logs/django.log",
            "maxBytes": 1024 * 1024 * 100,  
            "backupCount": 5,
            "formatter": "json",
        },
        "security": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/logs/security.log",
            "maxBytes": 1024 * 1024 * 50,  
            "backupCount": 10,
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["security"],
            "level": "INFO",
            "propagate": False,
        },
        "authentication": {
            "handlers": ["security"],
            "level": "INFO",
            "propagate": False,
        },
        "hms": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = "HMS Enterprise <noreply@hms.yourdomain.com>"
SERVER_EMAIL = "HMS Server <server@hms.yourdomain.com>"
STATIC_URL = "https://cdn.hms.yourdomain.com/static/"
MEDIA_URL = "https://cdn.hms.yourdomain.com/media/"
if os.environ.get("USE_S3", "false").lower() == "true":
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_DEFAULT_ACL = None
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    AWS_S3_FILE_OVERWRITE = False
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
    "rest_framework.throttling.ScopedRateThrottle",
]
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "100/hour",
    "user": "10000/hour",
    "login": "10/minute",
    "password_reset": "5/minute",
    "admin": "1000/hour",
}
CORS_ALLOWED_ORIGINS = [
    "https://hms.yourdomain.com",
    "https://app.hms.yourdomain.com",
]
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ["Content-Range", "X-Total-Count"]
INSTALLED_APPS += [
    "superadmin",
    "authentication",
    "accounting_advanced",
    "django_prometheus",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "django_celery_beat",
    "django_celery_results",
]
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.SecurityEventMiddleware",
    "core.middleware.RateLimitMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {
            "user_attributes": ("username", "email", "first_name", "last_name"),
            "max_similarity": 0.7,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "authentication.validators.CustomPasswordValidator",
    },
]
MFA_ENABLED = True
MFA_REQUIRED_FOR_SUPERUSERS = True
MFA_TOKEN_VALIDITY = 300  
MFA_BACKUP_CODES_COUNT = 10
TOTP_ISSUER_NAME = "HMS Enterprise"
TOTP_TOKEN_VALIDITY = 30  
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable is required")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET", SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_LIFETIME = 900  
JWT_REFRESH_TOKEN_LIFETIME = 86400  
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  
FILE_UPLOAD_PERMISSIONS = 0o644
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
ALLOWED_UPLOAD_EXTENSIONS = [
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".mp4",
    ".avi",
    ".mov",
    ".wmv",
    ".txt",
    ".csv",
    ".json",
    ".xml",
]
HIPAA_AUDIT_ENABLED = True
HIPAA_ENCRYPTION_REQUIRED = True
HIPAA_ACCESS_LOGGING = True
HIPAA_DATA_RETENTION_DAYS = 2555  
MONITORING_ENABLED = True
PROMETHEUS_METRICS_ENABLED = True
JAEGER_TRACING_ENABLED = True
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style="url"),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment="production",
        release=os.environ.get("APP_VERSION", "unknown"),
    )
HEALTH_CHECK = {
    "DISK_USAGE_MAX": 90,  
    "MEMORY_MIN": 100,  
}
import signal
import sys
from django.core.management import execute_from_command_line
def graceful_shutdown(signum, frame):
    print("Received signal to shutdown gracefully...")
    from django.db import connections
    for conn in connections.all():
        conn.close()
    from celery import current_app
    if current_app:
        current_app.control.shutdown()
    sys.exit(0)
signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)
TALLY_INTEGRATION_ENABLED = True
TALLY_API_TIMEOUT = 30
TALLY_RETRY_ATTEMPTS = 3
SMS_PROVIDER = "twilio"  
SMS_API_KEY = os.environ.get("SMS_API_KEY")
EMAIL_PROVIDER = "sendgrid"  
EMAIL_API_KEY = os.environ.get("EMAIL_API_KEY")
CONN_MAX_AGE = 0  
DATABASE_CONN_HEALTH_CHECKS = True
USE_TZ = True
USE_I18N = True
USE_L10N = True
SECURITY_EVENT_RETENTION_DAYS = 365
FAILED_LOGIN_THRESHOLD = 5
FAILED_LOGIN_LOCKOUT_TIME = 1800  
SUSPICIOUS_ACTIVITY_THRESHOLD = 10
BACKUP_ENABLED = True
BACKUP_STORAGE = "s3://hms-backups/"
BACKUP_RETENTION_DAYS = 90
BACKUP_ENCRYPTION_ENABLED = True
DISASTER_RECOVERY_ENABLED = True
DR_REGION = "us-west-2"
DR_BACKUP_FREQUENCY = "daily"
DR_TEST_FREQUENCY = "monthly"
GDPR_COMPLIANCE_ENABLED = True
HIPAA_COMPLIANCE_ENABLED = True
SOX_COMPLIANCE_ENABLED = True
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {},
    "USE_SESSION_AUTH": False,
    "DOC_EXPANSION": "none",
    "APIS_SORTER": "alpha",
    "OPERATIONS_SORTER": "alpha",
    "TAGS_SORTER": "alpha",
    "SHOW_REQUEST_HEADERS": False,
}
REDOC_SETTINGS = {
    "LAZY_RENDERING": True,
    "HIDE_HOSTNAME": True,
    "EXPAND_RESPONSES": "none",
}
DJANGO_REST_SWAGGER_ENABLED = False
DATA_UPLOAD_MAX_NUMBER_FILES = 20
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
FILE_UPLOAD_TEMP_DIR = "/tmp/uploads"
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_TZ = True
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600
FEATURE_FLAGS = {
    "ADVANCED_ANALYTICS": True,
    "TALLY_INTEGRATION": True,
    "MFA_ENFORCEMENT": True,
    "REAL_TIME_NOTIFICATIONS": True,
    "MOBILE_APP_API": True,
    "AUDIT_LOGGING": True,
    "ENCRYPTION_AT_REST": True,
}