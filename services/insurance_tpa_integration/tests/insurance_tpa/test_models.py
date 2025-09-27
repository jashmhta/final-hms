"""
test_models module
"""

from datetime import timedelta

import factory
import pytest
from insurance_tpa.factories.factories import *
from insurance_tpa.models import Claim, Patient, PreAuth, Reimbursement

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

User = get_user_model()


@pytest.mark.django_db
class TestPreAuthModel:
    def test_encryption_decryption(self):
        patient = PatientFactory()
        user = UserFactory()
        original_amount = 12345.67
        preauth = PreAuthFactory(
            claim_amount=original_amount, patient=patient, created_by=user
        )
        assert preauth.claim_amount_encrypted is not None
        assert len(preauth.claim_amount_encrypted) > 0
        decrypted_amount = preauth.decrypt_claim_amount()
        assert decrypted_amount == str(original_amount)

    def test_auditlog_tracking(self):
        patient = PatientFactory()
        user = UserFactory()
        preauth = PreAuthFactory(patient=patient, created_by=user, status="pending")
        preauth.status = "approved"
        preauth.save()
        from auditlog.models import LogEntry

        audit_entries = LogEntry.objects.filter(
            content_type__model="preauth", object_id=preauth.id
        )
        assert audit_entries.exists()
        assert audit_entries.first().action == "CHANGE"

    def test_retention_cleanup(self):
        patient = PatientFactory()
        user = UserFactory()
        old_date = timezone.now() - timedelta(days=366)
        preauth_old = PreAuthFactory(
            patient=patient, created_by=user, created_at=old_date
        )
        preauth_recent = PreAuthFactory(patient=patient, created_by=user)

    def test_invalid_amount_edge_case(self):
        patient = PatientFactory()
        user = UserFactory()
        with pytest.raises(ValueError):
            PreAuthFactory(claim_amount=-100.00, patient=patient, created_by=user)
        with pytest.raises(ValueError):
            PreAuthFactory(claim_amount=2000000.00, patient=patient, created_by=user)


@pytest.mark.django_db
class TestClaimModel:
    def test_encryption_decryption(self):
        patient = PatientFactory()
        user = UserFactory()
        original_billed = 54321.98
        claim = ClaimFactory(
            billed_amount=original_billed, patient=patient, created_by=user
        )
        assert claim.billed_amount_encrypted is not None
        decrypted_billed = claim.decrypt_billed_amount()
        assert decrypted_billed == str(original_billed)

    def test_multiple_procedures_validation(self):
        patient = PatientFactory()
        user = UserFactory()
        procedures = ", ".join([f"Proc{i}" for i in range(11)])
        with pytest.raises(ValueError):
            ClaimFactory(procedures=procedures, patient=patient, created_by=user)
        valid_procedures = ", ".join([f"Proc{i}" for i in range(10)])
        claim = ClaimFactory(
            procedures=valid_procedures, patient=patient, created_by=user
        )
        assert claim.procedures == valid_procedures


@pytest.mark.django_db
class TestReimbursementModel:
    def test_encryption_decryption(self):
        claim = ClaimFactory()
        original_paid = 9876.54
        reimbursement = ReimbursementFactory(paid_amount=original_paid, claim=claim)
        assert reimbursement.paid_amount_encrypted is not None
        decrypted_paid = reimbursement.decrypt_paid_amount()
        assert decrypted_paid == str(original_paid)

    def test_transaction_id_uniqueness(self):
        claim = ClaimFactory()
        transaction_id = "TXN123456789"
        ReimbursementFactory(transaction_id=transaction_id, claim=claim)
        with pytest.raises(Exception):
            ReimbursementFactory(transaction_id=transaction_id, claim=claim)


@pytest.mark.django_db
class TestRetentionCleanup:
    @pytest.fixture
    def old_records(self):
        patient = PatientFactory()
        user = UserFactory()
        claim = ClaimFactory(patient=patient, created_by=user)
        old_date = timezone.now() - timedelta(days=366)
        old_preauth = PreAuthFactory(
            patient=patient, created_by=user, created_at=old_date
        )
        old_claim = ClaimFactory(patient=patient, created_by=user, created_at=old_date)
        old_reimbursement = ReimbursementFactory(claim=old_claim, created_at=old_date)
        return old_preauth, old_claim, old_reimbursement

    def test_cleanup_old_records(self, old_records):
        old_preauth, old_claim, old_reimbursement = old_records
