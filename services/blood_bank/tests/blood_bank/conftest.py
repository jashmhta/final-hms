import os
import pytest
from django.conf import settings
from django.test import Client
@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        pass
@pytest.fixture
def api_client():
    client = Client()
    return client
@pytest.fixture
def admin_user(db, django_user_model):
    User = django_user_model
    user = User.objects.create_user(
        username="admin_test",
        email="admin@test.com",
        password="testpass123",
        role="ADMIN",
    )
    return user
@pytest.fixture
def doctor_user(db, django_user_model):
    User = django_user_model
    user = User.objects.create_user(
        username="doctor_test",
        email="doctor@test.com",
        password="testpass123",
        role="DOCTOR",
    )
    return user
@pytest.fixture
def patient_user(db, django_user_model):
    User = django_user_model
    patient = User.objects.create(
        id=1,
        name="John Doe",
        dob="1980-01-01",
        gender="Male",
        contact="123-456-7890",
        medical_history="Test patient history",
        created_at="2023-01-01T00:00:00Z",
    )
    return patient