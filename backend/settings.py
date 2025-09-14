# HIPAA Compliance Settings
HIPAA_ENCRYPTION_KEY = (
    "your-secure-hipaa-key-here=="  # Generate with Fernet.generate_key()
)
HIPAA_AUDIT_RETENTION_DAYS = 365  # 1 year minimum retention
HIPAA_CONSENT_EXPIRY_DAYS = 365  # Default consent expiry

# Security headers for HIPAA compliance
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# PHI field encryption settings
FERNET_KEYS = [
    "your-secure-fernet-key-here==",
]

# Logging configuration for HIPAA audit trails
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "hipaa": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "hipaa_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/var/log/hipaa_audit.log",
            "formatter": "hipaa",
        },
    },
    "loggers": {
        "compliance.hipaa": {
            "handlers": ["hipaa_file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
