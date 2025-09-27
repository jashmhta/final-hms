"""
test_serializers module
"""

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
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": -100.00,
            "procedures": "Procedure1",
        }
        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)
    def test_amount_over_limit(self):
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": 1500000.00,
            "procedures": "Procedure1",
        }
        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)
    def test_invalid_procedure_format(self):
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": 50000.00,
            "procedures": "Proc@1, Proc
        }
        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)
    def test_too_many_procedures(self):
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
        data = {
            "claim_amount": 50000.00,
            "procedures": "Procedure1",
        }  
        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)
    @mock.patch("cryptography.fernet.Fernet.decrypt")
    def test_encrypted_field_decryption(self, mock_decrypt):
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
        data = {
            "patient_id": "PAT12345678",
            "billed_amount": 25000.123,  
            "procedures": "Proc1",
            "diagnosis": "Test",
        }
        with pytest.raises(ValidationError):
            serializer = ClaimSerializer(data=data)
            serializer.is_valid(raise_exception=True)
    def test_procedure_code_length_validation(self):
        long_procedure = "A" * 11  
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
        data_short = {
            "claim_id": 1,
            "paid_amount": 20000.00,
            "transaction_id": "TXN1",  
            "payment_date": "2025-01-15",
        }
        with pytest.raises(ValidationError):
            serializer = ReimbursementSerializer(data=data_short)
            serializer.is_valid(raise_exception=True)
        data_invalid = {
            "claim_id": 1,
            "paid_amount": 20000.00,
            "transaction_id": "TXN@12345678",  
            "payment_date": "2025-01-15",
        }
        with pytest.raises(ValidationError):
            serializer = ReimbursementSerializer(data=data_invalid)
            serializer.is_valid(raise_exception=True)
    def test_payment_date_validation(self):
        data_future = {
            "claim_id": 1,
            "paid_amount": 20000.00,
            "transaction_id": "TXN123456789",
            "payment_date": "2026-01-15",  
        }
        with pytest.raises(ValidationError):
            serializer = ReimbursementSerializer(data=data_future)
            serializer.is_valid(raise_exception=True)
    def test_paid_amount_greater_than_billed(self):
        data = {
            "claim_id": 1,
            "paid_amount": 30000.00,  
            "transaction_id": "TXN123456789",
            "payment_date": "2025-01-15",
        }
        with pytest.raises(ValidationError):
            serializer = ReimbursementSerializer(data=data)
            serializer.is_valid(raise_exception=True)
    def test_duplicate_transaction_id(self):
        data1 = {
            "claim_id": 1,
            "paid_amount": 20000.00,
            "transaction_id": "TXN123456789",
            "payment_date": "2025-01-15",
        }
        serializer1 = ReimbursementSerializer(data=data1)
        assert serializer1.is_valid()
        serializer2 = ReimbursementSerializer(data=data1)
        with pytest.raises(ValidationError):
            serializer2.is_valid(raise_exception=True)
@pytest.mark.django_db
class TestSerializerEdgeCases:
    def test_decimal_zero_amount(self):
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": 0.00,
            "procedures": "Procedure1",
        }
        serializer = PreAuthSerializer(data=data)
        assert serializer.is_valid()
    def test_maximum_valid_amount(self):
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": 1000000.00,
            "procedures": "Procedure1",
        }
        serializer = PreAuthSerializer(data=data)
        assert serializer.is_valid()
    def test_string_amount_conversion(self):
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": "50000.00",
            "procedures": "Procedure1",
        }
        serializer = PreAuthSerializer(data=data)
        assert serializer.is_valid()
        assert isinstance(serializer.validated_data["claim_amount"], Decimal)
    def test_invalid_decimal_string(self):
        data = {
            "patient_id": "PAT12345678",
            "claim_amount": "invalid_amount",
            "procedures": "Procedure1",
        }
        with pytest.raises(ValidationError):
            serializer = PreAuthSerializer(data=data)
            serializer.is_valid(raise_exception=True)