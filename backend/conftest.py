"""
conftest module
"""

import pytest
from factory.django import DjangoModelFactory
from faker import Faker

from django.conf import settings

fake = Faker()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture
def user_factory():
    class UserFactory(DjangoModelFactory):
        class Meta:
            model = "users.User"

        username = fake.user_name()
        email = fake.email()

    return UserFactory


@pytest.fixture
def patient_factory():
    class PatientFactory(DjangoModelFactory):
        class Meta:
            model = "patients.Patient"

        first_name = fake.first_name()
        last_name = fake.last_name()
        date_of_birth = fake.date_of_birth()

    return PatientFactory
