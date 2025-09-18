from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
Base = declarative_base()
class DoctorSpecialization(enum.Enum):
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
class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    specialization = Column(Enum(DoctorSpecialization))
    qualification = Column(String)
    license_number = Column(String, unique=True)
    contact_number = Column(String)
    email = Column(String)
    consultation_fee = Column(Float)
    is_available = Column(Boolean, default=True)
    working_hours = Column(JSON)
    department_id = Column(Integer, ForeignKey("departments.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    department = relationship("Department")
class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String)
    department_code = Column(String, unique=True)
    head_doctor_id = Column(Integer, ForeignKey("doctors.id"))
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    day_of_week = Column(Integer)  
    start_time = Column(String)
    end_time = Column(String)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    doctor = relationship("Doctor")
class DoctorLeave(Base):
    __tablename__ = "doctor_leaves"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    leave_type = Column(String)  
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    reason = Column(Text, nullable=True)
    status = Column(String)  
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    doctor = relationship("Doctor")
class DoctorPerformance(Base):
    __tablename__ = "doctor_performance"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    date = Column(DateTime)
    patients_seen = Column(Integer, default=0)
    consultations_completed = Column(Integer, default=0)
    prescriptions_written = Column(Integer, default=0)
    revenue_generated = Column(Float, default=0)
    patient_satisfaction_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    doctor = relationship("Doctor")