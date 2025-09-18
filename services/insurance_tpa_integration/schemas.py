from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
class InsuranceProviderBase(BaseModel):
    name: str
    code: str
    tpa_code: Optional[str] = None
    api_endpoint: Optional[str] = None
    is_active: bool = True
class InsuranceProviderCreate(InsuranceProviderBase):
    api_key: Optional[str] = None
class InsuranceProvider(InsuranceProviderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class InsurancePolicyBase(BaseModel):
    patient_id: int
    policy_number: str
    insurance_provider_id: int
    group_number: Optional[str] = None
    effective_date: datetime
    expiration_date: datetime
    coverage_details: Dict[str, Any]
class InsurancePolicyCreate(InsurancePolicyBase):
    pass
class InsurancePolicy(InsurancePolicyBase):
    id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class InsuranceClaimBase(BaseModel):
    patient_id: int
    policy_id: int
    billing_id: int
    total_amount: float
    status: str
class InsuranceClaimCreate(InsuranceClaimBase):
    pass
class InsuranceClaim(InsuranceClaimBase):
    id: int
    claim_number: str
    approved_amount: Optional[float] = None
    submission_date: datetime
    approval_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    denial_reason: Optional[str] = None
    resubmission_count: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class TPATransactionBase(BaseModel):
    claim_id: int
    tpa_reference: str
    transaction_type: str
    request_data: Dict[str, Any]
    response_data: Dict[str, Any]
    status_code: int
class TPATransactionCreate(TPATransactionBase):
    error_message: Optional[str] = None
class TPATransaction(TPATransactionBase):
    id: int
    retry_count: int
    created_at: datetime
    class Config:
        from_attributes = True
class PaymentRecordBase(BaseModel):
    claim_id: int
    payment_amount: float
    payment_date: datetime
    payment_method: str
    reference_number: str
    adjustment_details: Dict[str, Any]
class PaymentRecordCreate(PaymentRecordBase):
    pass
class PaymentRecord(PaymentRecordBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True
class EligibilityRequest(BaseModel):
    patient_id: int
    policy_id: int
    service_date: datetime
class EligibilityResponse(BaseModel):
    is_eligible: bool
    coverage_details: Dict[str, Any]
    limitations: Optional[List[str]] = None
    requires_preauth: bool
class ClaimSubmissionRequest(BaseModel):
    claim_id: int
    tpa_provider_id: int
class PaymentPostingRequest(BaseModel):
    claim_id: int
    payment_data: Dict[str, Any]