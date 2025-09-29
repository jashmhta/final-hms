import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Add backend directory to path for apps
sys.path.insert(0, str(BASE_DIR))

# Add libs directory to path for encrypted_model_fields
sys.path.insert(0, str(BASE_DIR / "libs"))

SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-testing-only")
DEBUG = False
ALLOWED_HOSTS = ["*"]

AUTH_USER_MODEL = "users.User"

# Test encryption key
FIELD_ENCRYPTION_KEY = "d-81mPwXIDePWNgD0XNVXdtA5pDqstbgmz9cyUpv4PU="

# Test secrets
os.environ.setdefault("SECRETS_MASTER_KEY", "test-master-key-for-testing-only")
os.environ.setdefault("FERNET_KEY", FIELD_ENCRYPTION_KEY)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    # "django.contrib.admin",  # Has issues with missing models
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
    "core",
    "users",
    # "appointments",  # Has dependencies on hospitals, patients
    # "ehr",  # Has dependencies
    # "hr",  # Has dependencies
    # "superadmin",  # Has dependencies
    # "authentication",  # Has dependencies
    # "compliance",  # Has dependencies
    # "accounting_advanced",  # Has dependencies
    # "feedback",  # Has dependencies
    # "ai_ml",  # Has dependencies
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "hms.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "hms.wsgi.application"
ASGI_APPLICATION = "hms.asgi.application"

TEST_RUNNER = "django.test.runner.DiscoverRunner"
