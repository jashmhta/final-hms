from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
class MedicationBase(BaseModel):
    name: str
    generic_name: str
    dosage_form: str
    strength: str
    manufacturer: str
    ndc_code: str
    is_controlled: bool = False
class MedicationCreate(MedicationBase):
    pass
class Medication(MedicationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class PrescriptionBase(BaseModel):
    patient_id: int
    doctor_id: int
    medication_id: int
    dosage: str
    frequency: str
    duration: int
    quantity: int
    instructions: str
class PrescriptionCreate(PrescriptionBase):
    refills_allowed: int = 0
class Prescription(PrescriptionBase):
    id: int
    prescription_number: str
    status: str
    issue_date: datetime
    expiry_date: datetime
    refills_allowed: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class PharmacyBase(BaseModel):
    name: str
    address: str
    phone: str
    email: str
    license_number: str
class PharmacyCreate(PharmacyBase):
    is_active: bool = True
class Pharmacy(PharmacyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class PrescriptionDispatchBase(BaseModel):
    prescription_id: int
    pharmacy_id: int
    dispatch_status: str
    expected_pickup_date: datetime
class PrescriptionDispatchCreate(PrescriptionDispatchBase):
    pass
class PrescriptionDispatch(PrescriptionDispatchBase):
    id: int
    dispatch_date: datetime
    actual_pickup_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class DrugInteractionBase(BaseModel):
    medication1_id: int
    medication2_id: int
    interaction_level: str
    description: str
    recommendations: str
class DrugInteractionCreate(DrugInteractionBase):
    pass
class DrugInteraction(DrugInteractionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class PrescriptionCheckRequest(BaseModel):
    patient_id: int
    medication_ids: List[int]
    existing_prescriptions: List[int]
class PrescriptionCheckResponse(BaseModel):
    has_interactions: bool
    interactions: List[Dict[str, Any]]
    has_allergies: bool
    allergies: List[str]
    is_safe: bool
    warnings: List[str]