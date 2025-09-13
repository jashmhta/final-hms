from decimal import Decimal, InvalidOperation
from unittest import mock

import pytest
from insurance_tpa.factories.factories import *
from insurance_tpa.serializers import (
    ClaimSerializer,
    PreAuthSerializer,
    ReimbursementSerializer,
)
from pydantic import ValidationError


@pytest.mark.django_db
class TestPreAuthSerializer:
    def test_valid_preauth_data(self):
        """Test valid pre-auth data passes validation."""
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": 50000.00,
            "procedures": "Procedure1,Procedure2",
            "diagnosis": "Test diagnosis",
        }

        serializer = PreAuthSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["claim_amount"] == Decimal("50000.00")

    def test_invalid_negative_amount(self):
        """Test validation for negative claim amounts."""
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": -100.00,
            "procedures": "Procedure1",
        }

        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)

    def test_amount_over_limit(self):
        """Test validation for claim amount over 1M limit."""
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": 1500000.00,
            "procedures": "Procedure1",
        }

        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)

    def test_invalid_procedure_format(self):
        """Test validation for invalid procedure codes (non-alphanumeric)."""
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": 50000.00,
            "procedures": "Proc@1, Proc#2",  # Contains special characters
        }

        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)

    def test_too_many_procedures(self):
        """Test validation for too many procedures (max 10)."""
        procedures = ", ".join([f"Proc{i}" for i in range(11)])
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": 50000.00,
            "procedures": procedures,
        }

        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)

    def test_missing_required_fields(self):
        """Test validation for missing required fields."""
        data = {
            "claim_amount": 50000.00,
            "procedures": "Procedure1",
        }  # Missing patient_id

        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)

    @mock.patch("cryptography.fernet.Fernet.decrypt")
    def test_encrypted_field_decryption(self, mock_decrypt):
        """Test proper handling of encrypted financial fields."""
        mock_decrypt.return_value = b"50000.00"

        data = {
            "patient_id": "PAT12345678",
            "claim_amount_encrypted": "encrypted_data_here",
            "procedures": "Procedure1",
        }

        serializer = PreAuthSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["claim_amount"] == Decimal("50000.00")
        mock_decrypt.assert_called_once()


@pytest.mark.django_db
class TestClaimSerializer:
    def test_valid_claim_data(self):
        """Test valid claim data passes validation."""
        data = {
            "patient_id": "PAT12345678",
            "billed_amount": 25000.00,
            "procedures": "Proc1,Proc2,Proc3",
            "diagnosis": "Test diagnosis",
            "status": "pending",
        }

        serializer = ClaimSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["billed_amount"] == Decimal("25000.00")
        assert serializer.validated_data["status"] == "pending"

    def test_invalid_status_enum(self):
        """Test validation for invalid status values."""
        data = {
            "patient_id": "PAT12345678",
            "billed_amount": 25000.00,
            "procedures": "Proc1",
            "diagnosis": "Test",
            "status": "invalid_status",
        }

        with pytest.raises(ValidationError):
            serializer = ClaimSerializer(data=data)
            serializer.is_valid(raise_exception=True)

    def test_decimal_precision_validation(self):
        """Test decimal precision validation (2 decimal places)."""
        data = {
            "patient_id": "PAT12345678",
            "billed_amount": 25000.123,  # 3 decimal places
            "procedures": "Proc1",
            "diagnosis": "Test",
        }

        with pytest.raises(ValidationError):
            serializer = ClaimSerializer(data=data)
            serializer.is_valid(raise_exception=True)

    def test_procedure_code_length_validation(self):
        """Test procedure code length validation (max 10 chars)."""
        long_procedure = "A" * 11  # 11 characters
        data = {
            "patient_id": "PAT12345678",
            "billed_amount": 25000.00,
            "procedures": long_procedure,
            "diagnosis": "Test",
        }

        with pytest.raises(ValidationError):
            serializer = ClaimSerializer(data=data)
            serializer.is_valid(raise_exception=True)

    def test_empty_procedures_list(self):
        """Test validation for empty procedures field."""
        data = {
            "patient_id": "PAT12345678",
            "billed_amount": 25000.00,
            "procedures": "",
            "diagnosis": "Test",
        }

        with pytest.raises(ValidationError):
            serializer = ClaimSerializer(data=data)
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestReimbursementSerializer:
    def test_valid_reimbursement_data(self):
        """Test valid reimbursement data passes validation."""
        data = {
            "claim_id": 1,
            "paid_amount": 20000.00,
            "transaction_id": "TXN123456789",
            "payment_date": "2025-01-15",
            "status": "paid",
        }

        serializer = ReimbursementSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["paid_amount"] == Decimal("20000.00")
        assert serializer.validated_data["status"] == "paid"

    def test_transaction_id_format_validation(self):
        """Test transaction_id format validation (alphanumeric, 10-20 chars)."""
        # Too short
        data_short = {
            "claim_id": 1,
            "paid_amount": 20000.00,
            "transaction_id": "TXN1",  # 4 chars
            "payment_date": "2025-01-15",
        }

        with pytest.raises(ValidationError):
            serializer = ReimbursementSerializer(data=data_short)
            serializer.is_valid(raise_exception=True)

        # Invalid characters
        data_invalid = {
            "claim_id": 1,
            "paid_amount": 20000.00,
            "transaction_id": "TXN@12345678",  # Contains @
            "payment_date": "2025-01-15",
        }

        with pytest.raises(ValidationError):
            serializer = ReimbursementSerializer(data=data_invalid)
            serializer.is_valid(raise_exception=True)

    def test_payment_date_validation(self):
        """Test payment_date validation (must be in past or today)."""
        # Future date
        data_future = {
            "claim_id": 1,
            "paid_amount": 20000.00,
            "transaction_id": "TXN123456789",
            "payment_date": "2026-01-15",  # Future date
        }

        with pytest.raises(ValidationError):
            serializer = ReimbursementSerializer(data=data_future)
            serializer.is_valid(raise_exception=True)

    def test_paid_amount_greater_than_billed(self):
        """Test validation that paid_amount cannot exceed billed_amount."""
        data = {
            "claim_id": 1,
            "paid_amount": 30000.00,  # Assume billed was 25000.00
            "transaction_id": "TXN123456789",
            "payment_date": "2025-01-15",
        }

        with pytest.raises(ValidationError):
            serializer = ReimbursementSerializer(data=data)
            serializer.is_valid(raise_exception=True)

    def test_duplicate_transaction_id(self):
        """Test validation for duplicate transaction_id."""
        # First valid creation
        data1 = {
            "claim_id": 1,
            "paid_amount": 20000.00,
            "transaction_id": "TXN123456789",
            "payment_date": "2025-01-15",
        }
        serializer1 = ReimbursementSerializer(data=data1)
        assert serializer1.is_valid()

        # Second with same transaction_id should fail
        serializer2 = ReimbursementSerializer(data=data1)
        with pytest.raises(ValidationError):
            serializer2.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestSerializerEdgeCases:
    """Test various edge cases for all serializers."""

    def test_decimal_zero_amount(self):
        """Test zero amounts are allowed (minimum amount)."""
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": 0.00,
            "procedures": "Procedure1",
        }

        serializer = PreAuthSerializer(data=data)
        assert serializer.is_valid()

    def test_maximum_valid_amount(self):
        """Test maximum valid amount (exactly 1M)."""
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": 1000000.00,
            "procedures": "Procedure1",
        }

        serializer = PreAuthSerializer(data=data)
        assert serializer.is_valid()

    def test_string_amount_conversion(self):
        """Test string amounts are properly converted to Decimal."""
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": "50000.00",
            "procedures": "Procedure1",
        }

        serializer = PreAuthSerializer(data=data)
        assert serializer.is_valid()
        assert isinstance(serializer.validated_data["claim_amount"], Decimal)

    def test_invalid_decimal_string(self):
        """Test invalid decimal string format."""
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": "invalid_amount",
            "procedures": "Procedure1",
        }

        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)
