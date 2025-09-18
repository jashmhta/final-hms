from datetime import date, timedelta
from factory import DjangoModelFactory, Iterator, Sequence, SubFactory
from factory.fuzzy import FuzzyChoice, FuzzyDate, FuzzyText
from ....app.models import BloodInventory, Crossmatch, Donor, TransfusionRecord
class DonorFactory(DjangoModelFactory):
    class Meta:
        model = "blood_bank.Donor"
    name = FuzzyText(length=50)
    dob = Sequence(lambda n: f"{n:02d}/01/198{n}")
    ssn = Sequence(lambda n: f"{n:03d}-{(n+10):02d}-{n:04d}")
    address = FuzzyText(length=100)
    contact = Sequence(lambda n: f"{n:010d}")
    blood_type = FuzzyChoice(choices=[choice[0] for choice in BLOOD_TYPES])
    donation_history = {}
    is_active = True
class BloodInventoryFactory(DjangoModelFactory):
    class Meta:
        model = "blood_bank.BloodInventory"
    donor = SubFactory(DonorFactory)
    blood_type = FuzzyChoice(choices=[choice[0] for choice in BLOOD_TYPES])
    unit_id = Sequence(lambda n: f"UNIT-{n:03d}")
    expiry_date = FuzzyDate(
        start_date=date.today(), end_date=date.today() + timedelta(days=365)
    )
    status = FuzzyChoice(
        choices=["AVAILABLE", "RESERVED", "TRANSFUSED", "EXPIRED", "QUARANTINED"]
    )
    quantity = 1
    storage_location = FuzzyText(length=50)
class PatientFactory(DjangoModelFactory):
    class Meta:
        model = "patients.Patient"  
    name = FuzzyText(length=50)
    dob = FuzzyDate(start_date=date(1950, 1, 1), end_date=date(2005, 12, 31))
    gender = FuzzyChoice(choices=["Male", "Female", "Other"])
    contact = Sequence(lambda n: f"{n:010d}")
    medical_history = FuzzyText(length=200)
class TransfusionRecordFactory(DjangoModelFactory):
    class Meta:
        model = "blood_bank.TransfusionRecord"
    patient = SubFactory(PatientFactory)
    blood_unit = SubFactory(BloodInventoryFactory)
    quantity = 1
    notes = FuzzyText(length=100)
class CrossmatchFactory(DjangoModelFactory):
    class Meta:
        model = "blood_bank.Crossmatch"
    patient = SubFactory(PatientFactory)
    blood_unit = SubFactory(BloodInventoryFactory)
    compatibility_result = FuzzyChoice(
        choices=["COMPATIBLE", "INCOMPATIBLE", "PENDING", "ERROR"]
    )
    notes = FuzzyText(length=100)