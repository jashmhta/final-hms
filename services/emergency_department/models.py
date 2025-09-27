import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class TriageLevel(enum.Enum):
    LEVEL_1 = "LEVEL_1"
    LEVEL_2 = "LEVEL_2"
    LEVEL_3 = "LEVEL_3"
    LEVEL_4 = "LEVEL_4"
    LEVEL_5 = "LEVEL_5"


class VisitStatus(enum.Enum):
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


class AlertType(enum.Enum):
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


class EmergencyVisit(Base):
    __tablename__ = "emergency_visits"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    visit_number = Column(String(50), unique=True, nullable=False)
    arrival_time = Column(DateTime, default=func.now(), nullable=False)
    arrival_mode = Column(String(20))
    chief_complaint = Column(Text)
    triage_level = Column(Enum(TriageLevel), index=True)
    triage_time = Column(DateTime)
    triage_nurse_id = Column(Integer)
    triage_notes = Column(Text)
    status = Column(Enum(VisitStatus), default=VisitStatus.REGISTERED, index=True)
    registration_time = Column(DateTime, default=func.now())
    first_provider_time = Column(DateTime)
    treatment_start_time = Column(DateTime)
    disposition_time = Column(DateTime)
    departure_time = Column(DateTime)
    assigned_doctor_id = Column(Integer)
    assigned_nurse_id = Column(Integer)
    assigned_bed_id = Column(Integer)
    disposition = Column(String(50))
    disposition_destination = Column(String(200))
    discharge_instructions = Column(Text)
    pain_score_initial = Column(Integer)
    pain_score_final = Column(Integer)
    satisfaction_score = Column(Integer)
    insurance_verified = Column(Boolean, default=False)
    financial_clearance = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    vital_signs = relationship("VitalSigns", back_populates="visit")
    triage_assessments = relationship("TriageAssessment", back_populates="visit")
    emergency_alerts = relationship("EmergencyAlert", back_populates="visit")


class TriageAssessment(Base):
    __tablename__ = "triage_assessments"
    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("emergency_visits.id"), nullable=False)
    assessor_id = Column(Integer, nullable=False)
    assessment_time = Column(DateTime, default=func.now())
    triage_level = Column(Enum(TriageLevel), nullable=False)
    airway_status = Column(String(20))
    breathing_status = Column(String(20))
    circulation_status = Column(String(20))
    disability_status = Column(String(20))
    systolic_bp = Column(Integer)
    diastolic_bp = Column(Integer)
    heart_rate = Column(Integer)
    respiratory_rate = Column(Integer)
    temperature = Column(Numeric(4, 1))
    oxygen_saturation = Column(Integer)
    pain_score = Column(Integer)
    pain_location = Column(String(200))
    glasgow_coma_scale = Column(Integer)
    mental_status = Column(String(50))
    symptoms = Column(JSON)
    mechanism_of_injury = Column(Text)
    high_risk_factors = Column(JSON)
    allergies = Column(Text)
    current_medications = Column(Text)
    medical_history = Column(Text)
    reassessment_required = Column(Boolean, default=False)
    reassessment_interval = Column(Integer)
    assessment_notes = Column(Text)
    red_flags = Column(Text)
    created_at = Column(DateTime, default=func.now())
    visit = relationship("EmergencyVisit", back_populates="triage_assessments")


class VitalSigns(Base):
    __tablename__ = "vital_signs"
    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("emergency_visits.id"), nullable=False)
    recorded_by_id = Column(Integer, nullable=False)
    measurement_time = Column(DateTime, default=func.now())
    systolic_bp = Column(Integer)
    diastolic_bp = Column(Integer)
    mean_arterial_pressure = Column(Integer)
    heart_rate = Column(Integer)
    respiratory_rate = Column(Integer)
    temperature_celsius = Column(Numeric(4, 1))
    oxygen_saturation = Column(Integer)
    weight_kg = Column(Numeric(6, 2))
    height_cm = Column(Numeric(6, 2))
    bmi = Column(Numeric(5, 2))
    pain_score = Column(Integer)
    pain_location = Column(String(200))
    glasgow_coma_scale = Column(Integer)
    pupils_left = Column(String(20))
    pupils_right = Column(String(20))
    measurement_device = Column(String(100))
    oxygen_delivery_method = Column(String(50))
    oxygen_flow_rate = Column(Numeric(4, 1))
    position_during_measurement = Column(String(50))
    activity_level = Column(String(50))
    notes = Column(Text)
    critical_values = Column(Boolean, default=False)
    alert_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    visit = relationship("EmergencyVisit", back_populates="vital_signs")


class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"
    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("emergency_visits.id"), nullable=True)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(String(10))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    location = Column(String(100))
    room_number = Column(String(20))
    affected_area = Column(String(100))
    alert_time = Column(DateTime, default=func.now())
    response_required_by = Column(DateTime)
    resolved_time = Column(DateTime)
    is_active = Column(Boolean, default=True)
    acknowledged_by = Column(JSON)
    responded_by = Column(JSON)
    escalation_level = Column(Integer, default=1)
    auto_escalate = Column(Boolean, default=True)
    escalated_at = Column(DateTime)
    resolution_notes = Column(Text)
    resolved_by_id = Column(Integer)
    triggered_by_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    visit = relationship("EmergencyVisit", back_populates="emergency_alerts")


class EmergencyBed(Base):
    __tablename__ = "emergency_beds"
    id = Column(Integer, primary_key=True, index=True)
    bed_number = Column(String(20), unique=True, nullable=False)
    bed_type = Column(String(50))
    location = Column(String(100))
    room_number = Column(String(20))
    zone = Column(String(50))
    has_monitoring = Column(Boolean, default=False)
    has_ventilator = Column(Boolean, default=False)
    has_isolation = Column(Boolean, default=False)
    max_weight_kg = Column(Integer)
    is_available = Column(Boolean, default=True)
    is_operational = Column(Boolean, default=True)
    cleaning_status = Column(String(20))
    assigned_patient_id = Column(Integer)
    assigned_at = Column(DateTime)
    estimated_discharge = Column(DateTime)
    last_maintenance = Column(DateTime)
    next_maintenance_due = Column(DateTime)
    maintenance_notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class EmergencyStaff(Base):
    __tablename__ = "emergency_staff"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True)
    role = Column(String(50))
    specialization = Column(String(100))
    certification_level = Column(String(50))
    is_on_duty = Column(Boolean, default=False)
    shift_start = Column(DateTime)
    shift_end = Column(DateTime)
    break_start = Column(DateTime)
    break_end = Column(DateTime)
    assigned_zone = Column(String(50))
    assigned_beds = Column(JSON)
    max_patients = Column(Integer, default=4)
    current_patient_count = Column(Integer, default=0)
    can_triage = Column(Boolean, default=False)
    can_intubate = Column(Boolean, default=False)
    can_suture = Column(Boolean, default=False)
    procedures_certified = Column(JSON)
    is_available = Column(Boolean, default=True)
    last_break = Column(DateTime)
    overtime_hours = Column(Numeric(4, 1), default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class EmergencyProtocol(Base):
    __tablename__ = "emergency_protocols"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50))
    protocol_code = Column(String(20), unique=True)
    version = Column(String(10), default="1.0")
    activation_criteria = Column(JSON)
    target_response_time = Column(Integer)
    steps = Column(JSON)
    required_equipment = Column(JSON)
    required_medications = Column(JSON)
    required_staff_roles = Column(JSON)
    decision_points = Column(JSON)
    contraindications = Column(JSON)
    description = Column(Text)
    indications = Column(Text)
    procedure_notes = Column(Text)
    post_procedure_care = Column(Text)
    success_criteria = Column(JSON)
    key_performance_indicators = Column(JSON)
    regulatory_requirements = Column(JSON)
    training_requirements = Column(JSON)
    is_active = Column(Boolean, default=True)
    requires_physician_order = Column(Boolean, default=False)
    created_by_id = Column(Integer)
    approved_by_id = Column(Integer)
    effective_date = Column(DateTime)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProtocolActivation(Base):
    __tablename__ = "protocol_activations"
    id = Column(Integer, primary_key=True, index=True)
    protocol_id = Column(Integer, ForeignKey("emergency_protocols.id"), nullable=False)
    visit_id = Column(Integer, ForeignKey("emergency_visits.id"), nullable=True)
    activated_by_id = Column(Integer, nullable=False)
    activation_time = Column(DateTime, default=func.now())
    activation_reason = Column(Text)
    response_team = Column(JSON)
    response_start_time = Column(DateTime)
    response_end_time = Column(DateTime)
    protocol_completed = Column(Boolean, default=False)
    completion_time = Column(DateTime)
    success_achieved = Column(Boolean)
    steps_completed = Column(JSON)
    deviations_from_protocol = Column(Text)
    complications = Column(Text)
    outcome_notes = Column(Text)
    response_time_seconds = Column(Integer)
    door_to_intervention_time = Column(Integer)
    patient_outcome = Column(String(50))
    deactivated_at = Column(DateTime)
    deactivated_by_id = Column(Integer)
    deactivation_reason = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
