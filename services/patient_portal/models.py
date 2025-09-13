from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class PatientStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCHARGED = "discharged"
    DECEASED = "deceased"

class BloodGroup(enum.Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"

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
    blood_group = Column(Enum(BloodGroup), nullable=True)
    allergies = Column(JSON, nullable=True)
    medical_history = Column(JSON, nullable=True)
    insurance_details = Column(JSON, nullable=True)
    status = Column(Enum(PatientStatus), default=PatientStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PatientLogin(Base):
    __tablename__ = "patient_logins"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    username = Column(String, unique=True)
    password_hash = Column(String)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = relationship("Patient")

class PatientAppointment(Base):
    __tablename__ = "patient_appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    appointment_id = Column(String, unique=True)
    doctor_id = Column(Integer)
    appointment_date = Column(DateTime)
    status = Column(String)  # scheduled, confirmed, completed, cancelled
    reason_for_visit = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = relationship("Patient")

class PatientMedicalRecord(Base):
    __tablename__ = "patient_medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    record_id = Column(String, unique=True)
    record_type = Column(String)  # consultation, lab_result, prescription, etc.
    doctor_id = Column(Integer, nullable=True)
    date = Column(DateTime)
    diagnosis = Column(Text, nullable=True)
    treatment = Column(Text, nullable=True)
    medications = Column(JSON, nullable=True)
    lab_results = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = relationship("Patient")

class PatientFeedback(Base):
    __tablename__ = "patient_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    feedback_id = Column(String, unique=True)
    rating = Column(Integer)  # 1-5 scale
    feedback_text = Column(Text, nullable=True)
    service_type = Column(String)  # consultation, admission, billing, etc.
    doctor_id = Column(Integer, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = relationship("Patient")

class PatientNotification(Base):
    __tablename__ = "patient_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    notification_id = Column(String, unique=True)
    title = Column(String)
    message = Column(Text)
    notification_type = Column(String)  # appointment, reminder, result, etc.
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = relationship("Patient")