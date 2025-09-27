"""
factories module
"""

import base64

import insurance_tpa.models as models
from cryptography.fernet import Fernet
from factory import DjangoModelFactory, SubFactory, post_creation
from factory.fuzzy import FuzzyDecimal, FuzzyText

from django.contrib.auth.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = FuzzyText(length=8)
    email = "test@example.com"


class PatientFactory(DjangoModelFactory):
    class Meta:
        model = models.Patient

    patient_id = FuzzyText(length=10)
    name = FuzzyText(length=20)
    date_of_birth = "1990-01-01"


class PreAuthFactory(DjangoModelFactory):
    class Meta:
        model = models.PreAuth

    patient = SubFactory(PatientFactory)
    created_by = SubFactory(UserFactory)
    claim_amount = FuzzyDecimal(100.00, 1000000.00, 2)
    status = "pending"

    @post_creation
    def encrypt_fields(self, create, extracted, **kwargs):
        if create:
            fernet = Fernet(models.ENCRYPTION_KEY)
            self.claim_amount_encrypted = base64.urlsafe_b64encode(
                fernet.encrypt(str(self.claim_amount).encode())
            ).decode()
            self.save()


class ClaimFactory(DjangoModelFactory):
    class Meta:
        model = models.Claim

    patient = SubFactory(PatientFactory)
    created_by = SubFactory(UserFactory)
    billed_amount = FuzzyDecimal(500.00, 500000.00, 2)
    procedures = "Procedure1,Procedure2"
    status = "pending"

    @post_creation
    def encrypt_fields(self, create, extracted, **kwargs):
        if create:
            fernet = Fernet(models.ENCRYPTION_KEY)
            self.billed_amount_encrypted = base64.urlsafe_b64encode(
                fernet.encrypt(str(self.billed_amount).encode())
            ).decode()
            self.save()


class ReimbursementFactory(DjangoModelFactory):
    class Meta:
        model = models.Reimbursement

    claim = SubFactory(ClaimFactory)
    paid_amount = FuzzyDecimal(100.00, 100000.00, 2)
    payment_date = "2025-01-01"
    transaction_id = FuzzyText(length=20)
    status = "paid"

    @post_creation
    def encrypt_fields(self, create, extracted, **kwargs):
        if create:
            fernet = Fernet(models.ENCRYPTION_KEY)
            self.paid_amount_encrypted = base64.urlsafe_b64encode(
                fernet.encrypt(str(self.paid_amount).encode())
            ).decode()
            self.save()
