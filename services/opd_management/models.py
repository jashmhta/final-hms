import enum
from datetime import datetime
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
Base = declarative_base()
class AppointmentStatus(enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
class ConsultationType(enum.Enum):
    GENERAL = "general"
    SPECIALIST = "specialist"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    date_of_birth = Column(DateTime)
    gender = Column(String)
    contact_number = Column(String)
    email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(String, nullable=True)
    blood_group = Column(String, nullable=True)
    allergies = Column(JSON, nullable=True)
    medical_history = Column(JSON, nullable=True)
    insurance_details = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    specialization = Column(String)
    qualification = Column(String)
    contact_number = Column(String)
    email = Column(String)
    consultation_fee = Column(Float)
    is_available = Column(Boolean, default=True)
    working_hours = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(String, unique=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    appointment_date = Column(DateTime)
    duration_minutes = Column(Integer, default=30)
    status = Column(Enum(AppointmentStatus))
    consultation_type = Column(Enum(ConsultationType))
    reason_for_visit = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    patient = relationship("Patient")
    doctor = relationship("Doctor")
class Consultation(Base):
    __tablename__ = "consultations"
    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(String, unique=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    consultation_date = Column(DateTime)
    vital_signs = Column(JSON, nullable=True)
    symptoms = Column(JSON)
    diagnosis = Column(Text)
    treatment_plan = Column(Text)
    prescriptions = Column(JSON, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    appointment = relationship("Appointment")
    patient = relationship("Patient")
    doctor = relationship("Doctor")
class OPDBill(Base):
    __tablename__ = "opd_bills"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(String, unique=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    total_amount = Column(Float)
    discount = Column(Float, default=0)
    tax_amount = Column(Float)
    final_amount = Column(Float)
    payment_status = Column(String)  
    payment_method = Column(String, nullable=True)
    insurance_claim_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    consultation = relationship("Consultation")
    patient = relationship("Patient")