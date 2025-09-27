"""
conftest module
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from insurance_tpa.models import InsuranceProvider, TPAAuthorization, TPAClaim

import django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

User = get_user_model()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        django.setup()


@pytest.fixture(scope="function")
def django_db_setup(django_db_setup, django_db_blocker):
    pass


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(scope="session")
def django_settings():
    if not settings.configured:
        settings.configure(
            DJANGO_SETTINGS_MODULE="insurance_tpa.settings_integration",
            DATABASES={...},
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.sessions",
                "django.contrib.messages",
                "django.contrib.staticfiles",
                "rest_framework",
                "rest_framework.authtoken",
                "insurance_tpa",
            ],
            MIDDLEWARE=[
                "django.middleware.security.SecurityMiddleware",
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.middleware.common.CommonMiddleware",
                "django.middleware.csrf.CsrfViewMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                "django.contrib.messages.middleware.MessageMiddleware",
                "django.middleware.clickjacking.XFrameOptionsMiddleware",
            ],
            ROOT_URLCONF="insurance_tpa.urls",
            TEMPLATES=[
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
            ],
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            REST_FRAMEWORK={
                "DEFAULT_AUTHENTICATION_CLASSES": [
                    "rest_framework.authentication.TokenAuthentication",
                ],
                "DEFAULT_PERMISSION_CLASSES": [
                    "rest_framework.permissions.IsAuthenticated",
                ],
                "TEST_REQUEST_DEFAULT_FORMAT": "json",
            },
        )
    return settings


@pytest.fixture(scope="function")
def api_client(django_db_setup, django_settings):
    client = Client()
    user = User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )
    client.login(username="testuser", password="testpass123")
    yield client
    client.logout()


@pytest.fixture
def mock_patient_model(monkeypatch):
    class MockPatient:
        def __init__(
            self, patient_id, first_name, last_name, date_of_birth, insurance_number
        ):
            self.patient_id = patient_id
            self.first_name = first_name
            self.last_name = last_name
            self.date_of_birth = date_of_birth
            self.insurance_number = insurance_number

        def __str__(self):
            return f"Patient {self.patient_id}"

    monkeypatch.setattr("insurance_tpa.models.Patient", MockPatient)
    return MockPatient


@pytest.fixture
def mock_celery_task(monkeypatch):
    mock_task = Mock()
    mock_task.delay.return_value = Mock()
    monkeypatch.setattr("celery.task.base.Task.apply_async", mock_task)
    return mock_task


@pytest.fixture
def mock_redis_connection(monkeypatch):
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    monkeypatch.setattr("redis.Redis", lambda **kwargs: mock_redis)
    return mock_redis


@pytest.fixture
def mock_tpa_api(monkeypatch):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "data": {"claim_id": "MOCK123", "approved": True},
    }
    with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
        mock_post.return_value = mock_response
        mock_get.return_value = mock_response
        yield mock_post, mock_get


@pytest.fixture
def sample_uploaded_file():
    return SimpleUploadedFile(
        name="test_claim.pdf",
        content=b"This is a test PDF file for claim submission.",
        content_type="application/pdf",
    )


@pytest.fixture
def sample_tpa_claim(api_client, mock_patient_model):
    patient = mock_patient_model("PAT001", "John", "Doe", "1990-01-01", "INS12345678")
    claim = TPAClaim.objects.create(
        claim_id="CLAIM001",
        patient=patient,
        amount=1000.00,
        status="pending",
        created_by=api_client.user,
    )
    return claim


@pytest.fixture
def sample_tpa_authorization(sample_tpa_claim):
    auth = TPAAuthorization.objects.create(
        auth_id="AUTH001",
        claim=sample_tpa_claim,
        authorized_amount=900.00,
        approval_status="approved",
        approved_by=sample_tpa_claim.created_by,
    )
    return auth


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    cache.clear()
    monkeypatch.setattr(
        "django.db.models.signals.post_save.send_robust", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "django.db.models.signals.post_delete.send_robust", lambda *args, **kwargs: None
    )


@pytest.mark.django_db
@pytest.fixture
def authenticated_client(api_client):
    return api_client


@pytest.fixture
def insurance_provider(db):
    provider = InsuranceProvider.objects.create(
        name="Test Insurance Co",
        provider_code="TEST001",
        contact_email="test@insurance.com",
        is_active=True,
    )
    return provider


@pytest.fixture
def clear_cache(monkeypatch):
    cache.clear()
