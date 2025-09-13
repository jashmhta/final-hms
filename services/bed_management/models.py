from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class BedStatus(enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"

class BedType(enum.Enum):
    GENERAL = "general"
    ICU = "icu"
    CCU = "ccu"
    PRIVATE = "private"
    SEMI_PRIVATE = "semi_private"

class Bed(Base):
    __tablename__ = "beds"
    
    id = Column(Integer, primary_key=True, index=True)
    bed_number = Column(String, unique=True)
    bed_type = Column(Enum(BedType))
    ward_id = Column(Integer, ForeignKey("wards.id"))
    floor_number = Column(Integer)
    room_number = Column(String)
    status = Column(Enum(BedStatus), default=BedStatus.AVAILABLE)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ward = relationship("Ward")

class Ward(Base):
    __tablename__ = "wards"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_name = Column(String)
    ward_type = Column(String)
    total_beds = Column(Integer)
    available_beds = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BedAssignment(Base):
    __tablename__ = "bed_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    bed_id = Column(Integer, ForeignKey("beds.id"))
    patient_id = Column(String)
    admission_id = Column(String)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    discharged_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    bed = relationship("Bed")

class BedMaintenance(Base):
    __tablename__ = "bed_maintenance"
    
    id = Column(Integer, primary_key=True, index=True)
    bed_id = Column(Integer, ForeignKey("beds.id"))
    maintenance_type = Column(String)
    description = Column(Text)
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime, nullable=True)
    status = Column(String)  # scheduled, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    bed = relationship("Bed")