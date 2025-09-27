import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    generic_name = Column(String)
    dosage_form = Column(String)
    strength = Column(String)
    manufacturer = Column(String)
    ndc_code = Column(String, unique=True)
    is_controlled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True)
    doctor_id = Column(Integer, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"))
    prescription_number = Column(String, unique=True)
    dosage = Column(String)
    frequency = Column(String)
    duration = Column(Integer)
    quantity = Column(Integer)
    refills_allowed = Column(Integer, default=0)
    instructions = Column(Text)
    status = Column(String)
    issue_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    medication = relationship("Medication")


class Pharmacy(Base):
    __tablename__ = "pharmacies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    license_number = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PrescriptionDispatch(Base):
    __tablename__ = "prescription_dispatches"
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"))
    dispatch_status = Column(String)
    dispatch_date = Column(DateTime)
    expected_pickup_date = Column(DateTime)
    actual_pickup_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    prescription = relationship("Prescription")
    pharmacy = relationship("Pharmacy")


class DrugInteraction(Base):
    __tablename__ = "drug_interactions"
    id = Column(Integer, primary_key=True, index=True)
    medication1_id = Column(Integer, ForeignKey("medications.id"))
    medication2_id = Column(Integer, ForeignKey("medications.id"))
    interaction_level = Column(String)
    description = Column(Text)
    recommendations = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
