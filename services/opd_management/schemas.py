from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
class ConsultationType(str, Enum):
    GENERAL = "general"
    SPECIALIST = "specialist"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
class PatientBase(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str
    contact_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: Optional[Dict[str, Any]] = None
    medical_history: Optional[Dict[str, Any]] = None
    insurance_details: Optional[Dict[str, Any]] = None
class PatientCreate(PatientBase):
    pass
class Patient(PatientBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class DoctorBase(BaseModel):
    doctor_id: str
    first_name: str
    last_name: str
    specialization: str
    qualification: str
    contact_number: str
    email: str
    consultation_fee: float
    working_hours: Dict[str, Any]
class DoctorCreate(DoctorBase):
    pass
class Doctor(DoctorBase):
    id: int
    is_available: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class AppointmentBase(BaseModel):
    appointment_id: str
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    status: AppointmentStatus
    consultation_type: ConsultationType
    reason_for_visit: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
class AppointmentCreate(AppointmentBase):
    pass
class Appointment(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class ConsultationBase(BaseModel):
    consultation_id: str
    appointment_id: int
    patient_id: int
    doctor_id: int
    consultation_date: datetime
    vital_signs: Optional[Dict[str, Any]] = None
    symptoms: Dict[str, Any]
    diagnosis: str
    treatment_plan: str
    prescriptions: Optional[Dict[str, Any]] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
class ConsultationCreate(ConsultationBase):
    pass
class Consultation(ConsultationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class OPDBillBase(BaseModel):
    bill_id: str
    consultation_id: int
    patient_id: int
    total_amount: float
    discount: float = 0
    tax_amount: float
    final_amount: float
    payment_status: str
    payment_method: Optional[str] = None
    insurance_claim_id: Optional[str] = None
class OPDBillCreate(OPDBillBase):
    pass
class OPDBill(OPDBillBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class AppointmentSlot(BaseModel):
    doctor_id: int
    date: datetime
    available_slots: List[Dict[str, Any]]
class OPDStatistics(BaseModel):
    total_patients: int
    total_appointments: int
    completed_appointments: int
    revenue_today: float
    revenue_month: float
    average_wait_time: float
class DoctorAvailability(BaseModel):
    doctor_id: int
    date: datetime
    available: bool
    available_slots: List[Dict[str, Any]]