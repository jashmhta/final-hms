import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
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


class AdmissionStatus(enum.Enum):
    ADMITTED = "admitted"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"
    IN_PROGRESS = "in_progress"


class IPDAdmission(Base):
    __tablename__ = "ipd_admissions"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True)
    admission_date = Column(DateTime, default=datetime.utcnow)
    admission_type = Column(String)
    admitting_doctor = Column(Integer, index=True)
    primary_diagnosis = Column(String)
    estimated_stay = Column(Integer)
    actual_stay = Column(Integer, nullable=True)
    status = Column(String, default=AdmissionStatus.ADMITTED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    beds = relationship("IPDBed", back_populates="admission")
    nursing_care = relationship("NursingCare", back_populates="admission")


class IPDBed(Base):
    __tablename__ = "ipd_beds"
    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("ipd_admissions.id"))
    bed_number = Column(String)
    bed_type = Column(String)
    is_occupied = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    admission = relationship("IPDAdmission", back_populates="beds")


class NursingCare(Base):
    __tablename__ = "nursing_care"
    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("ipd_admissions.id"))
    nursing_notes = Column(Text)
    vital_signs = Column(String)
    medication_administered = Column(String)
    care_plan = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    admission = relationship("IPDAdmission", back_populates="nursing_care")


class DischargeSummary(Base):
    __tablename__ = "discharge_summaries"
    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("ipd_admissions.id"))
    discharge_date = Column(DateTime, default=datetime.utcnow)
    discharge_diagnosis = Column(String)
    followup_instructions = Column(Text)
    medications_prescribed = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    admission = relationship("IPDAdmission", back_populates="discharge_summaries")
