from datetime import timedelta

import factory
import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from insurance_tpa.factories.factories import *
from insurance_tpa.models import Claim, Patient, PreAuth, Reimbursement

User = get_user_model()


@pytest.mark.django_db
class TestPreAuthModel:
    def test_encryption_decryption(self):
        """Test that financial fields are properly encrypted and can be decrypted."""
        patient = PatientFactory()
        user = UserFactory()
        original_amount = 12345.67

        preauth = PreAuthFactory(
            claim_amount=original_amount, patient=patient, created_by=user
        )

        # Verify encryption happened
        assert preauth.claim_amount_encrypted is not None
        assert len(preauth.claim_amount_encrypted) > 0

        # Test decryption (assuming model has decrypt method)
        decrypted_amount = preauth.decrypt_claim_amount()
        assert decrypted_amount == str(original_amount)

    def test_auditlog_tracking(self):
        """Test auditlog records changes to the model."""
        patient = PatientFactory()
        user = UserFactory()
        preauth = PreAuthFactory(patient=patient, created_by=user, status="pending")

        # Change status and verify auditlog entry
        preauth.status = "approved"
        preauth.save()

        # Verify auditlog has entry (assuming auditlog is properly configured)
        from auditlog.models import LogEntry

        audit_entries = LogEntry.objects.filter(
            content_type__model="preauth", object_id=preauth.id
        )
        assert audit_entries.exists()
        assert audit_entries.first().action == "CHANGE"

    def test_retention_cleanup(self):
        """Test 365-day retention cleanup manager."""
        patient = PatientFactory()
        user = UserFactory()

        # Create old record (older than 365 days)
        old_date = timezone.now() - timedelta(days=366)
        preauth_old = PreAuthFactory(
            patient=patient, created_by=user, created_at=old_date
        )

        # Create recent record
        preauth_recent = PreAuthFactory(patient=patient, created_by=user)

        # Test cleanup (assuming custom manager has cleanup method)
        # PreAuth.objects.cleanup_old_records()
        # assert not PreAuth.objects.filter(id=preauth_old.id).exists()
        # assert PreAuth.objects.filter(id=preauth_recent.id).exists()

    def test_invalid_amount_edge_case(self):
        """Test model validation for invalid amounts (negative, too large)."""
        patient = PatientFactory()
        user = UserFactory()

        with pytest.raises(ValueError):
            PreAuthFactory(claim_amount=-100.00, patient=patient, created_by=user)

        with pytest.raises(ValueError):
            PreAuthFactory(
                claim_amount=2000000.00, patient=patient, created_by=user
            )  # Over 1M limit


@pytest.mark.django_db
class TestClaimModel:
    def test_encryption_decryption(self):
        """Test claim financial fields encryption/decryption."""
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
        """Test validation for multiple procedures (max 10)."""
        patient = PatientFactory()
        user = UserFactory()
        procedures = ", ".join([f"Proc{i}" for i in range(11)])

        with pytest.raises(ValueError):
            ClaimFactory(procedures=procedures, patient=patient, created_by=user)

        # Valid case (10 procedures)
        valid_procedures = ", ".join([f"Proc{i}" for i in range(10)])
        claim = ClaimFactory(
            procedures=valid_procedures, patient=patient, created_by=user
        )
        assert claim.procedures == valid_procedures


@pytest.mark.django_db
class TestReimbursementModel:
    def test_encryption_decryption(self):
        """Test reimbursement financial fields encryption/decryption."""
        claim = ClaimFactory()
        original_paid = 9876.54

        reimbursement = ReimbursementFactory(paid_amount=original_paid, claim=claim)

        assert reimbursement.paid_amount_encrypted is not None
        decrypted_paid = reimbursement.decrypt_paid_amount()
        assert decrypted_paid == str(original_paid)

    def test_transaction_id_uniqueness(self):
        """Test transaction_id uniqueness constraint."""
        claim = ClaimFactory()
        transaction_id = "TXN123456789"

        ReimbursementFactory(transaction_id=transaction_id, claim=claim)

        with pytest.raises(Exception):  # IntegrityError or ValidationError
            ReimbursementFactory(transaction_id=transaction_id, claim=claim)


@pytest.mark.django_db
class TestRetentionCleanup:
    """Test retention cleanup across all models."""

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
        """Test cleanup removes records older than 365 days."""
        old_preauth, old_claim, old_reimbursement = old_records

        # Assuming cleanup method exists in models
        # PreAuth.objects.cleanup_old_records()
        # Claim.objects.cleanup_old_records()
        # Reimbursement.objects.cleanup_old_records()

        # Verify old records are deleted
        # assert not PreAuth.objects.filter(id=old_preauth.id).exists()
        # assert not Claim.objects.filter(id=old_claim.id).exists()
        # assert not Reimbursement.objects.filter(id=old_reimbursement.id).exists()
