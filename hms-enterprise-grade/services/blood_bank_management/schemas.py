from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BloodType(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class BloodUnitBase(BaseModel):
    unit_number: str
    blood_type: BloodType
    rh_factor: str
    collection_date: datetime
    expiration_date: datetime
    volume_ml: int
    donor_id: int
    test_results: Dict[str, Any]
    status: str
    storage_location: str
    notes: Optional[str] = None


class BloodUnitCreate(BloodUnitBase):
    pass


class BloodUnit(BloodUnitBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DonorBase(BaseModel):
    donor_id: str
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str
    blood_type: BloodType
    rh_factor: str
    contact_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    eligibility_status: str
    last_donation_date: Optional[datetime] = None
    total_donations: int = 0


class DonorCreate(DonorBase):
    pass


class Donor(DonorBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DonationBase(BaseModel):
    donation_id: str
    donor_id: int
    donation_date: datetime
    volume_ml: int
    collection_method: str
    collection_staff: str
    test_results: Dict[str, Any]
    status: str
    notes: Optional[str] = None


class DonationCreate(DonationBase):
    pass


class Donation(DonationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TransfusionRequestBase(BaseModel):
    request_id: str
    patient_id: int
    patient_blood_type: BloodType
    patient_rh_factor: str
    requested_blood_type: BloodType
    requested_rh_factor: str
    units_requested: int
    urgency: str
    requested_by: str
    request_date: datetime
    status: str
    approved_units: int = 0
    fulfilled_units: int = 0
    notes: Optional[str] = None


class TransfusionRequestCreate(TransfusionRequestBase):
    pass


class TransfusionRequest(TransfusionRequestBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransfusionBase(BaseModel):
    transfusion_id: str
    request_id: int
    blood_unit_id: int
    patient_id: int
    transfusion_date: datetime
    administered_by: str
    vital_signs: Dict[str, Any]
    adverse_reactions: Optional[Dict[str, Any]] = None
    outcome: str
    notes: Optional[str] = None


class TransfusionCreate(TransfusionBase):
    pass


class Transfusion(TransfusionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BloodTestBase(BaseModel):
    test_id: str
    blood_unit_id: int
    test_type: str
    test_date: datetime
    result: str
    performed_by: str
    notes: Optional[str] = None


class BloodTestCreate(BloodTestBase):
    pass


class BloodTest(BloodTestBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryAlertBase(BaseModel):
    alert_type: str
    blood_type: BloodType
    rh_factor: str
    current_quantity: int
    threshold: int
    alert_message: str
    severity: str
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


class InventoryAlertCreate(InventoryAlertBase):
    pass


class InventoryAlert(InventoryAlertBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BloodInventorySummary(BaseModel):
    blood_type: BloodType
    rh_factor: str
    total_units: int
    available_units: int
    reserved_units: int
    expired_units: int


class DonationStatistics(BaseModel):
    total_donations: int
    monthly_donations: int
    donor_count: int
    blood_type_distribution: Dict[str, int]


class TransfusionStatistics(BaseModel):
    total_transfusions: int
    monthly_transfusions: int
    blood_usage_by_type: Dict[str, int]
    adverse_reaction_count: int
