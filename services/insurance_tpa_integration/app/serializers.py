"""
serializers module
"""

import logging
from typing import List, Optional

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


class PreAuthPydantic(BaseModel):
    patient_id: str = Field(..., min_length=1, max_length=50)
    policy_number: str = Field(..., min_length=5, max_length=20)
    procedure_code: str = Field(..., min_length=1, max_length=10)
    estimated_amount: float = Field(..., gt=0, le=1000000)
    diagnosis_code: Optional[str] = Field(None, min_length=1, max_length=10)
    status: str = Field("pending", pattern="^(pending|approved|rejected)$")

    class Config:
        schema_extra = {
            "examples": [
                {
                    "patient_id": "PAT001",
                    "policy_number": "POL12345",
                    "procedure_code": "PROC001",
                    "estimated_amount": 2500.00,
                    "diagnosis_code": "DX001",
                    "status": "pending",
                }
            ]
        }

    @validator("estimated_amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Estimated amount must be positive")
        if v > 1000000:
            raise ValueError("Estimated amount exceeds maximum limit of $1,000,000")
        return v


class ClaimPydantic(BaseModel):
    patient_id: str = Field(..., min_length=1, max_length=50)
    policy_number: str = Field(..., min_length=5, max_length=20)
    claim_amount: float = Field(..., gt=0, le=500000)
    procedure_codes: List[str] = Field(..., min_items=1, max_items=10)
    diagnosis_codes: List[str] = Field(..., min_items=1, max_items=5)
    status: str = Field(
        "submitted", pattern="^(submitted|processing|approved|rejected|paid)$"
    )
    tpa_transaction_id: Optional[str] = Field(None, max_length=100)

    class Config:
        schema_extra = {
            "examples": [
                {
                    "patient_id": "PAT001",
                    "policy_number": "POL12345",
                    "claim_amount": 4500.00,
                    "procedure_codes": ["PROC001", "PROC002"],
                    "diagnosis_codes": ["DX001"],
                    "status": "submitted",
                    "tpa_transaction_id": None,
                }
            ]
        }

    @validator("claim_amount")
    def validate_claim_amount(cls, v):
        if v <= 0:
            raise ValueError("Claim amount must be positive")
        if v > 500000:
            raise ValueError("Claim amount exceeds maximum limit of $500,000")
        return v

    @validator("procedure_codes")
    def validate_procedure_cocryptography.fernet.Fernet(cls, v):
        for code in v:
            if len(code) < 1 or len(code) > 10:
                raise ValueError("Each procedure code must be between 1-10 characters")
            if not code.isalnum():
                raise ValueError("Procedure codes must be alphanumeric")
        return v


class ReimbursementPydantic(BaseModel):
    claim_id: str = Field(..., min_length=1, max_length=50)
    reimbursed_amount: float = Field(..., gt=0, le=500000)
    status: str = Field("processed", pattern="^(processed|pending|failed)$")
    transaction_id: str = Field(..., min_length=1, max_length=100)

    class Config:
        schema_extra = {
            "examples": [
                {
                    "claim_id": "CLAIM001",
                    "reimbursed_amount": 4050.00,
                    "status": "processed",
                    "transaction_id": "TXN123456789",
                }
            ]
        }

    @validator("reimbursed_amount")
    def validate_reimbursed_amount(cls, v):
        if v <= 0:
            raise ValueError("Reimbursed amount must be positive")
        if v > 500000:
            raise ValueError("Reimbursed amount exceeds maximum limit of $500,000")
        return v

    @validator("transaction_id")
    def validate_transaction_id(cls, v):
        if not v.isalnum():
            raise ValueError("Transaction ID must be alphanumeric")
        return v


class PreAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreAuth
        fields = [
            "id",
            "patient_id",
            "policy_number",
            "procedure_code",
            "estimated_amount",
            "diagnosis_code",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        try:
            pydantic_model = PreAuthPydantic(**data)
        except PydanticValidationError as e:
            raise serializers.ValidationError({"pydantic_errors": e.errors()})
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, "patient_id_encrypted") and instance.patient_id_encrypted:
            try:
                f = Fernet(settings.ENCRYPTION_KEY)
                decrypted_patient_id = f.decrypt(
                    instance.patient_id_encrypted.encode()
                ).decode()
                data["patient_id"] = decrypted_patient_id
                logger.info(
                    f"Successfully decrypted patient_id for PreAuth {instance.id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to decrypt patient_id for PreAuth {instance.id}: {e}"
                )
                data["patient_id"] = "***DECRYPTION_FAILED***"
                data["decryption_error"] = str(e)
        return data

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        instance = super().create(validated_data)
        logger.info(
            f'Created PreAuth {instance.id} for user {self.context["request"].user.id}'
        )
        return instance


class ClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = [
            "id",
            "patient_id",
            "policy_number",
            "claim_amount",
            "procedure_codes",
            "diagnosis_codes",
            "status",
            "tpa_transaction_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        try:
            pydantic_model = ClaimPydantic(**data)
        except PydanticValidationError as e:
            raise serializers.ValidationError({"pydantic_errors": e.errors()})
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, "patient_id_encrypted") and instance.patient_id_encrypted:
            try:
                f = Fernet(settings.ENCRYPTION_KEY)
                decrypted_patient_id = f.decrypt(
                    instance.patient_id_encrypted.encode()
                ).decode()
                data["patient_id"] = decrypted_patient_id
                logger.info(
                    f"Successfully decrypted patient_id for Claim {instance.id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to decrypt patient_id for Claim {instance.id}: {e}"
                )
                data["patient_id"] = "***DECRYPTION_FAILED***"
                data["decryption_error"] = str(e)
        return data

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        instance = super().create(validated_data)
        logger.info(
            f'Created Claim {instance.id} for user {self.context["request"].user.id}'
        )
        return instance


class ReimbursementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reimbursement
        fields = [
            "id",
            "claim_id",
            "reimbursed_amount",
            "status",
            "transaction_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        try:
            pydantic_model = ReimbursementPydantic(**data)
        except PydanticValidationError as e:
            raise serializers.ValidationError({"pydantic_errors": e.errors()})
        return data

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        instance = super().create(validated_data)
        logger.info(
            f'Created Reimbursement {instance.id} for user {self.context["request"].user.id}'
        )
        return instance


class PreAuthBulkSerializer(serializers.ListSerializer):
    child = PreAuthSerializer()


class ClaimBulkSerializer(serializers.ListSerializer):
    child = ClaimSerializer()


class ReimbursementBulkSerializer(serializers.ListSerializer):
    child = ReimbursementSerializer()
