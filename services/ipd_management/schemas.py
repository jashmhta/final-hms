from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AdmissionStatus(str, Enum):
    ADMITTED = "admitted"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"
    IN_PROGRESS = "in_progress"


class IPDAdmissionBase(BaseModel):
    patient_id: int
    admission_type: str
    admitting_doctor: int
    primary_diagnosis: str
    estimated_stay: int


class IPDAdmissionCreate(IPDAdmissionBase):
    pass


class IPDAdmission(IPDAdmissionBase):
    id: int
    admission_date: datetime
    actual_stay: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IPDBedBase(BaseModel):
    admission_id: int
    bed_number: str
    bed_type: str
    is_occupied: bool = True


class IPDBedCreate(IPDBedBase):
    pass


class IPDBed(IPDBedBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class NursingCareBase(BaseModel):
    admission_id: int
    nursing_notes: Optional[str] = None
    vital_signs: Optional[str] = None
    medication_administered: Optional[str] = None
    care_plan: Optional[str] = None


class NursingCareCreate(NursingCareBase):
    pass


class NursingCare(NursingCareBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DischargeSummaryBase(BaseModel):
    admission_id: int
    discharge_date: datetime
    discharge_diagnosis: str
    followup_instructions: str
    medications_prescribed: str


class DischargeSummaryCreate(DischargeSummaryBase):
    pass


class DischargeSummary(DischargeSummaryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
