from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DoctorSpecialization(str, Enum):
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    ORTHOPEDICS = "orthopedics"
    PEDIATRICS = "pediatrics"
    GYNECOLOGY = "gynecology"
    DERMATOLOGY = "dermatology"
    PSYCHIATRY = "psychiatry"
    RADIOLOGY = "radiology"
    ANESTHESIOLOGY = "anesthesiology"
    EMERGENCY_MEDICINE = "emergency_medicine"
    GENERAL_MEDICINE = "general_medicine"


class DoctorBase(BaseModel):
    doctor_id: str
    first_name: str
    last_name: str
    specialization: DoctorSpecialization
    qualification: str
    license_number: str
    contact_number: str
    email: str
    consultation_fee: float
    working_hours: Dict[str, Any]
    department_id: int


class DoctorCreate(DoctorBase):
    pass


class Doctor(DoctorBase):
    id: int
    is_available: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentBase(BaseModel):
    department_name: str
    department_code: str
    head_doctor_id: Optional[int] = None
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class Department(DepartmentBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoctorScheduleBase(BaseModel):
    doctor_id: int
    day_of_week: int
    start_time: str
    end_time: str


class DoctorScheduleCreate(DoctorScheduleBase):
    pass


class DoctorSchedule(DoctorScheduleBase):
    id: int
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoctorLeaveBase(BaseModel):
    doctor_id: int
    leave_type: str
    start_date: datetime
    end_date: datetime
    reason: Optional[str] = None


class DoctorLeaveCreate(DoctorLeaveBase):
    pass


class DoctorLeave(DoctorLeaveBase):
    id: int
    status: str
    approved_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoctorPerformanceBase(BaseModel):
    doctor_id: int
    date: datetime
    patients_seen: int = 0
    consultations_completed: int = 0
    prescriptions_written: int = 0
    revenue_generated: float = 0
    patient_satisfaction_score: Optional[float] = None


class DoctorPerformanceCreate(DoctorPerformanceBase):
    pass


class DoctorPerformance(DoctorPerformanceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoctorDashboard(BaseModel):
    doctor_id: int
    doctor_name: str
    specialization: str
    department: str
    today_appointments: int
    pending_consultations: int
    monthly_revenue: float
    patient_satisfaction: float
    upcoming_leaves: int


class DoctorStatistics(BaseModel):
    total_doctors: int
    active_doctors: int
    doctors_on_leave: int
    average_consultation_fee: float
    total_monthly_revenue: float
