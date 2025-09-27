from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class TriageLevel(str, Enum):
    LEVEL_1 = "LEVEL_1"
    LEVEL_2 = "LEVEL_2"
    LEVEL_3 = "LEVEL_3"
    LEVEL_4 = "LEVEL_4"
    LEVEL_5 = "LEVEL_5"


class VisitStatus(str, Enum):
    REGISTERED = "REGISTERED"
    TRIAGED = "TRIAGED"
    WAITING = "WAITING"
    IN_TREATMENT = "IN_TREATMENT"
    ADMITTED = "ADMITTED"
    DISCHARGED = "DISCHARGED"
    TRANSFERRED = "TRANSFERRED"
    LEFT_AMA = "LEFT_AMA"
    LWBS = "LWBS"
    DECEASED = "DECEASED"


class AlertType(str, Enum):
    CODE_BLUE = "CODE_BLUE"
    CODE_RED = "CODE_RED"
    CODE_GRAY = "CODE_GRAY"
    CODE_SILVER = "CODE_SILVER"
    TRAUMA_ALERT = "TRAUMA_ALERT"
    STROKE_ALERT = "STROKE_ALERT"
    STEMI_ALERT = "STEMI_ALERT"
    SEPSIS_ALERT = "SEPSIS_ALERT"
    MASS_CASUALTY = "MASS_CASUALTY"
    PANDEMIC = "PANDEMIC"


class EmergencyVisitBase(BaseModel):
    patient_id: int
    chief_complaint: Optional[str] = None
    arrival_mode: Optional[str] = None


class EmergencyVisitCreate(EmergencyVisitBase):
    pass


class EmergencyVisit(EmergencyVisitBase):
    id: int
    visit_number: str
    arrival_time: datetime
    triage_level: Optional[TriageLevel] = None
    triage_time: Optional[datetime] = None
    status: VisitStatus
    registration_time: datetime
    first_provider_time: Optional[datetime] = None
    treatment_start_time: Optional[datetime] = None
    disposition_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    assigned_doctor_id: Optional[int] = None
    assigned_nurse_id: Optional[int] = None
    assigned_bed_id: Optional[int] = None
    disposition: Optional[str] = None
    pain_score_initial: Optional[int] = None
    pain_score_final: Optional[int] = None
    satisfaction_score: Optional[int] = None
    insurance_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TriageAssessmentBase(BaseModel):
    visit_id: int
    triage_level: TriageLevel
    airway_status: Optional[str] = None
    breathing_status: Optional[str] = None
    circulation_status: Optional[str] = None
    disability_status: Optional[str] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature: Optional[Decimal] = None
    oxygen_saturation: Optional[int] = None
    pain_score: Optional[int] = Field(None, ge=0, le=10)
    pain_location: Optional[str] = None
    glasgow_coma_scale: Optional[int] = Field(None, ge=3, le=15)
    mental_status: Optional[str] = None
    symptoms: Optional[List[str]] = None
    mechanism_of_injury: Optional[str] = None
    high_risk_factors: Optional[List[str]] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    medical_history: Optional[str] = None
    assessment_notes: Optional[str] = None
    red_flags: Optional[str] = None


class TriageAssessmentCreate(TriageAssessmentBase):
    assessor_id: int


class TriageAssessment(TriageAssessmentBase):
    id: int
    assessor_id: int
    assessment_time: datetime
    reassessment_required: bool = False
    reassessment_interval: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TriageUpdate(BaseModel):
    triage_level: TriageLevel
    triage_notes: Optional[str] = None
    reassessment_required: Optional[bool] = False
    updated_by_id: int


class VitalSignsBase(BaseModel):
    systolic_bp: Optional[int] = Field(None, ge=50, le=300)
    diastolic_bp: Optional[int] = Field(None, ge=30, le=200)
    heart_rate: Optional[int] = Field(None, ge=20, le=250)
    respiratory_rate: Optional[int] = Field(None, ge=5, le=100)
    temperature_celsius: Optional[Decimal] = Field(None, ge=30.0, le=50.0)
    oxygen_saturation: Optional[int] = Field(None, ge=50, le=100)
    weight_kg: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    pain_score: Optional[int] = Field(None, ge=0, le=10)
    pain_location: Optional[str] = None
    glasgow_coma_scale: Optional[int] = Field(None, ge=3, le=15)
    pupils_left: Optional[str] = None
    pupils_right: Optional[str] = None
    measurement_device: Optional[str] = None
    oxygen_delivery_method: Optional[str] = None
    oxygen_flow_rate: Optional[Decimal] = None
    position_during_measurement: Optional[str] = None
    notes: Optional[str] = None


class VitalSignsCreate(VitalSignsBase):
    recorded_by_id: int


class VitalSigns(VitalSignsBase):
    id: int
    visit_id: int
    recorded_by_id: int
    measurement_time: datetime
    mean_arterial_pressure: Optional[int] = None
    bmi: Optional[Decimal] = None
    activity_level: Optional[str] = None
    critical_values: bool = False
    alert_triggered: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class EmergencyAlertBase(BaseModel):
    alert_type: AlertType
    severity: str = Field(..., regex="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    room_number: Optional[str] = None
    affected_area: Optional[str] = None


class EmergencyAlertCreate(EmergencyAlertBase):
    visit_id: Optional[int] = None
    triggered_by_id: int
    response_required_by: Optional[datetime] = None


class EmergencyAlert(EmergencyAlertBase):
    id: int
    visit_id: Optional[int] = None
    alert_time: datetime
    response_required_by: Optional[datetime] = None
    resolved_time: Optional[datetime] = None
    is_active: bool = True
    acknowledged_by: Optional[List[int]] = None
    responded_by: Optional[List[int]] = None
    escalation_level: int = 1
    escalated_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolved_by_id: Optional[int] = None
    triggered_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledgment(BaseModel):
    acknowledged_by_id: int
    acknowledgment_notes: Optional[str] = None


class EmergencyBedBase(BaseModel):
    bed_number: str
    bed_type: Optional[str] = None
    location: Optional[str] = None
    room_number: Optional[str] = None
    zone: Optional[str] = None
    has_monitoring: bool = False
    has_ventilator: bool = False
    has_isolation: bool = False
    max_weight_kg: Optional[int] = None


class EmergencyBed(EmergencyBedBase):
    id: int
    is_available: bool = True
    is_operational: bool = True
    cleaning_status: Optional[str] = None
    assigned_patient_id: Optional[int] = None
    assigned_at: Optional[datetime] = None
    estimated_discharge: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance_due: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BedAssignment(BaseModel):
    patient_id: int
    assigned_by_id: int
    estimated_discharge: Optional[datetime] = None
    assignment_notes: Optional[str] = None


class EmergencyStaffBase(BaseModel):
    user_id: int
    role: str
    specialization: Optional[str] = None
    certification_level: Optional[str] = None
    can_triage: bool = False
    can_intubate: bool = False
    can_suture: bool = False
    max_patients: int = 4


class EmergencyStaff(EmergencyStaffBase):
    id: int
    is_on_duty: bool = False
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    break_start: Optional[datetime] = None
    break_end: Optional[datetime] = None
    assigned_zone: Optional[str] = None
    assigned_beds: Optional[List[int]] = None
    current_patient_count: int = 0
    procedures_certified: Optional[List[str]] = None
    is_available: bool = True
    last_break: Optional[datetime] = None
    overtime_hours: Optional[Decimal] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmergencyProtocolBase(BaseModel):
    name: str
    category: Optional[str] = None
    protocol_code: str
    version: str = "1.0"
    description: Optional[str] = None
    target_response_time: Optional[int] = None


class EmergencyProtocol(EmergencyProtocolBase):
    id: int
    activation_criteria: Optional[List[Dict[str, Any]]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    required_equipment: Optional[List[str]] = None
    required_medications: Optional[List[str]] = None
    required_staff_roles: Optional[List[str]] = None
    decision_points: Optional[List[Dict[str, Any]]] = None
    contraindications: Optional[List[str]] = None
    indications: Optional[str] = None
    procedure_notes: Optional[str] = None
    post_procedure_care: Optional[str] = None
    success_criteria: Optional[List[str]] = None
    key_performance_indicators: Optional[List[str]] = None
    regulatory_requirements: Optional[List[str]] = None
    training_requirements: Optional[List[str]] = None
    is_active: bool = True
    requires_physician_order: bool = False
    created_by_id: Optional[int] = None
    approved_by_id: Optional[int] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProtocolActivation(BaseModel):
    protocol_id: int
    visit_id: Optional[int] = None
    activated_by_id: int
    activation_reason: str
    response_team: Optional[List[int]] = None


class TriageDistribution(BaseModel):
    level_1: int = 0
    level_2: int = 0
    level_3: int = 0
    level_4: int = 0
    level_5: int = 0


class WaitTimeMetrics(BaseModel):
    average_wait_time: Optional[int] = None
    median_wait_time: Optional[int] = None
    percentile_90: Optional[int] = None
    door_to_triage_avg: Optional[int] = None
    door_to_provider_avg: Optional[int] = None


class PatientFlowMetrics(BaseModel):
    arrivals_per_hour: List[Dict[str, int]]
    departures_per_hour: List[Dict[str, int]]
    peak_census: int
    current_census: int
    bed_turnover_rate: Optional[Decimal] = None


class QualityMetrics(BaseModel):
    door_to_doctor_time: Optional[int] = None
    left_without_being_seen_rate: Optional[Decimal] = None
    patient_satisfaction_score: Optional[Decimal] = None
    readmission_rate_72h: Optional[Decimal] = None
    mortality_rate: Optional[Decimal] = None
    compliance_scores: Optional[Dict[str, Decimal]] = None
