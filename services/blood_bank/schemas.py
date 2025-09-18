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
class BloodComponent(str, Enum):
    WHOLE_BLOOD = "whole_blood"
    RED_CELLS = "red_cells"
    PLATELETS = "platelets"
    PLASMA = "plasma"
    CRYOPRECIPITATE = "cryoprecipitate"
class DonorBase(BaseModel):
    patient_id: int
    blood_type: BloodType
class DonorCreate(DonorBase):
    pass
class Donor(DonorBase):
    id: int
    eligibility_status: str
    eligibility_reason: Optional[str] = None
    last_donation_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class BloodBagBase(BaseModel):
    blood_type: BloodType
    component: BloodComponent
    volume_ml: int = Field(gt=0)
    collection_date: datetime
    expiration_date: datetime
    storage_location: str
class BloodBagCreate(BloodBagBase):
    donation_id: int
class BloodBag(BloodBagBase):
    id: int
    status: str
    test_results: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class DonationBase(BaseModel):
    donor_id: int
    volume_ml: int = Field(gt=0)
    collection_staff_id: int
    collection_notes: Optional[str] = None
class DonationCreate(DonationBase):
    pass
class Donation(DonationBase):
    id: int
    donation_date: datetime
    status: str
    created_at: datetime
    class Config:
        from_attributes = True
class TransfusionBase(BaseModel):
    blood_bag_id: int
    patient_id: int
    doctor_id: int
    volume_ml: int = Field(gt=0)
    vital_signs: Optional[Dict[str, Any]] = None
class TransfusionCreate(TransfusionBase):
    pass
class Transfusion(TransfusionBase):
    id: int
    transfusion_date: datetime
    adverse_reaction: bool
    reaction_details: Optional[str] = None
    status: str
    created_at: datetime
    class Config:
        from_attributes = True
class BloodRequestBase(BaseModel):
    patient_id: int
    doctor_id: int
    blood_type: BloodType
    component: BloodComponent
    quantity: int = Field(gt=0)
    urgency: str
class BloodRequestCreate(BloodRequestBase):
    pass
class BloodRequest(BloodRequestBase):
    id: int
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True