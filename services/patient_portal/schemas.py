from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
class PatientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCHARGED = "discharged"
    DECEASED = "deceased"
class BloodGroup(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
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
    blood_group: Optional[BloodGroup] = None
    allergies: Optional[Dict[str, Any]] = None
    medical_history: Optional[Dict[str, Any]] = None
    insurance_details: Optional[Dict[str, Any]] = None
class PatientCreate(PatientBase):
    pass
class Patient(PatientBase):
    id: int
    status: PatientStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class PatientLoginBase(BaseModel):
    patient_id: int
    username: str
    password: str
class PatientLoginCreate(PatientLoginBase):
    pass
class PatientLogin(PatientLoginBase):
    id: int
    last_login: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class PatientAppointmentBase(BaseModel):
    patient_id: int
    appointment_id: str
    doctor_id: int
    appointment_date: datetime
    reason_for_visit: Optional[str] = None
    notes: Optional[str] = None
class PatientAppointmentCreate(PatientAppointmentBase):
    pass
class PatientAppointment(PatientAppointmentBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class PatientMedicalRecordBase(BaseModel):
    patient_id: int
    record_id: str
    record_type: str
    doctor_id: Optional[int] = None
    date: datetime
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    medications: Optional[Dict[str, Any]] = None
    lab_results: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
class PatientMedicalRecordCreate(PatientMedicalRecordBase):
    pass
class PatientMedicalRecord(PatientMedicalRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class PatientFeedbackBase(BaseModel):
    patient_id: int
    feedback_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None
    service_type: str
    doctor_id: Optional[int] = None
    is_anonymous: bool = False
class PatientFeedbackCreate(PatientFeedbackBase):
    pass
class PatientFeedback(PatientFeedbackBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class PatientNotificationBase(BaseModel):
    patient_id: int
    notification_id: str
    title: str
    message: str
    notification_type: str
class PatientNotificationCreate(PatientNotificationBase):
    pass
class PatientNotification(PatientNotificationBase):
    id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class PatientDashboard(BaseModel):
    patient_id: int
    patient_name: str
    upcoming_appointments: int
    pending_results: int
    unread_notifications: int
    recent_consultations: int
    health_summary: Dict[str, Any]
class PatientStatistics(BaseModel):
    total_patients: int
    active_patients: int
    new_registrations_today: int
    average_rating: float