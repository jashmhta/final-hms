"""
test_models module
"""

from datetime import date, timedelta

import pytest

from django.db import IntegrityError

from ..app.models import (
    BLOOD_TYPES,
    BloodInventory,
    Crossmatch,
    Donor,
    TransfusionRecord,
)


@pytest.mark.django_db
class TestBloodBankModels:
    def test_donor_creation(self):
        donor = Donor.objects.create(
            name="John Doe",
            dob="01/01/1980",
            ssn="123-45-6789",
            address="123 Test St, Test City",
            contact="1234567890",
            blood_type="O+",
            is_active=True,
        )
        assert donor.pk is not None
        assert donor.name == "John Doe"
        assert donor.blood_type == "O+"
        assert donor.is_active is True

    def test_donor_encryption(self):
        donor = Donor.objects.create(
            name="Jane Smith",
            dob="02/02/1990",
            ssn="987-65-4321",
            address="456 Test Ave",
            contact="0987654321",
            blood_type="A-",
            is_active=True,
        )
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM blood_bank_donor WHERE id = %s", [donor.pk]
            )
            encrypted_name = cursor.fetchone()[0]
            assert encrypted_name != "Jane Smith"

    def test_blood_inventory_creation(self):
        donor = Donor.objects.create(
            name="Test Donor",
            dob="01/01/1980",
            ssn="123-45-6789",
            address="123 Test St",
            contact="1234567890",
            blood_type="O+",
            is_active=True,
        )
        inventory = BloodInventory.objects.create(
            donor=donor,
            blood_type="O+",
            unit_id="UNIT-001",
            expiry_date=date.today() + timedelta(days=45),
            status="AVAILABLE",
            quantity=1,
            storage_location="Fridge A-1",
        )
        assert inventory.pk is not None
        assert inventory.unit_id == "UNIT-001"
        assert inventory.status == "AVAILABLE"
        assert inventory.donor == donor

    def test_blood_inventory_unique_unit_id(self):
        donor = Donor.objects.create(
            name="Test Donor",
            dob="01/01/1980",
            ssn="123-45-6789",
            address="123 Test St",
            contact="1234567890",
            blood_type="O+",
            is_active=True,
        )
        BloodInventory.objects.create(
            donor=donor,
            blood_type="O+",
            unit_id="UNIT-001",
            expiry_date=date.today() + timedelta(days=45),
            status="AVAILABLE",
            quantity=1,
        )
        with pytest.raises(IntegrityError):
            BloodInventory.objects.create(
                donor=donor,
                blood_type="O+",
                unit_id="UNIT-001",
                expiry_date=date.today() + timedelta(days=45),
                status="AVAILABLE",
                quantity=1,
            )

    def test_transfusion_record_creation(self):
        donor = Donor.objects.create(
            name="Test Donor",
            dob="01/01/1980",
            ssn="123-45-6789",
            address="123 Test St",
            contact="1234567890",
            blood_type="O+",
            is_active=True,
        )
        inventory = BloodInventory.objects.create(
            donor=donor,
            blood_type="O+",
            unit_id="UNIT-001",
            expiry_date=date.today() + timedelta(days=45),
            status="AVAILABLE",
            quantity=1,
        )
        from ..app.models import Patient

        patient = Patient.objects.create(
            id=1,
            name="John Doe",
            dob="1980-01-01",
            gender="Male",
            contact="123-456-7890",
            medical_history="Test patient",
        )
        transfusion = TransfusionRecord.objects.create(
            patient=patient, blood_unit=inventory, quantity=1, notes="Test transfusion"
        )
        assert transfusion.pk is not None
        assert transfusion.patient == patient
        assert transfusion.blood_unit == inventory
        assert transfusion.quantity == 1

    def test_crossmatch_creation(self):
        donor = Donor.objects.create(
            name="Test Donor",
            dob="01/01/1980",
            ssn="123-45-6789",
            address="123 Test St",
            contact="1234567890",
            blood_type="O+",
            is_active=True,
        )
        inventory = BloodInventory.objects.create(
            donor=donor,
            blood_type="O+",
            unit_id="UNIT-001",
            expiry_date=date.today() + timedelta(days=45),
            status="AVAILABLE",
            quantity=1,
        )
        from ..app.models import Patient

        patient = Patient.objects.create(
            id=1,
            name="John Doe",
            dob="1980-01-01",
            gender="Male",
            contact="123-456-7890",
            medical_history="Test patient",
        )
        crossmatch = Crossmatch.objects.create(
            patient=patient,
            blood_unit=inventory,
            compatibility_result="COMPATIBLE",
            notes="Test crossmatch",
        )
        assert crossmatch.pk is not None
        assert crossmatch.compatibility_result == "COMPATIBLE"
        assert crossmatch.patient == patient

    def test_blood_type_choices(self):
        assert "O-" in [choice[0] for choice in BLOOD_TYPES]
        assert "AB+" in [choice[0] for choice in BLOOD_TYPES]
        assert len(BLOOD_TYPES) == 8

    def test_inventory_status_choices(self):
        from ..app.models import INVENTORY_STATUS

        valid_statuses = [
            "AVAILABLE",
            "RESERVED",
            "TRANSFUSED",
            "EXPIRED",
            "QUARANTINED",
        ]
        assert all(status[0] in valid_statuses for status in INVENTORY_STATUS)

    def test_crossmatch_results_choices(self):
        from ..app.models import COMPATIBILITY_RESULTS

        valid_results = ["COMPATIBLE", "INCOMPATIBLE", "PENDING", "ERROR"]
        assert all(result[0] in valid_results for result in COMPATIBILITY_RESULTS)
