from django.contrib.auth.models import User
from factory import Factory, RelatedFactory, Sequence, post_generation
from factory_boy import DjangoModelFactory
from faker import Faker
from .models import InsuranceProvider, TPAAuthorization, TPAClaim
fake = Faker()
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    username = Sequence(lambda n: f"testuser{n}")
    email = Sequence(lambda n: f"testuser{n}@example.com")
    password = "testpass123"
class InsuranceProviderFactory(DjangoModelFactory):
    class Meta:
        model = InsuranceProvider
    name = Sequence(lambda n: f"Insurance Provider {n}")
    provider_code = Sequence(lambda n: f"INS{n:04d}")
    contact_email = fake.email()
    is_active = True
class PatientFactory(Factory):
    class Meta:
        abstract = True
    patient_id = Sequence(lambda n: f"PAT{n:06d}")
    first_name = fake.first_name()
    last_name = fake.last_name()
    date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=90)
    insurance_number = Sequence(lambda n: f"INSNUM{n:08d}")
class TPAClaimFactory(DjangoModelFactory):
    class Meta:
        model = TPAClaim
    claim_id = Sequence(lambda n: f"CLAIM{n:08d}")
    patient = RelatedFactory(PatientFactory, "claim")
    insurance_provider = RelatedFactory(InsuranceProviderFactory, "claims")
    amount = fake.pydecimal(left_digits=5, right_digits=2, positive=True)
    status = "pending"
    created_by = RelatedFactory(UserFactory, "tpa_claims")
class TPAAuthorizationFactory(DjangoModelFactory):
    class Meta:
        model = TPAAuthorization
    auth_id = Sequence(lambda n: f"AUTH{n:08d}")
    claim = RelatedFactory(TPAClaimFactory, "authorization")
    authorized_amount = fake.pydecimal(left_digits=5, right_digits=2, positive=True)
    approval_status = "approved"
    approved_by = RelatedFactory(UserFactory, "tpa_authorizations")
    expiry_date = fake.future_date(end_of_year=1)