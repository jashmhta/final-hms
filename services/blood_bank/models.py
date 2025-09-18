import enum
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
Base = declarative_base()
class BloodType(enum.Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
class BloodComponent(enum.Enum):
    WHOLE_BLOOD = "whole_blood"
    RED_CELLS = "red_cells"
    PLATELETS = "platelets"
    PLASMA = "plasma"
    CRYOPRECIPITATE = "cryoprecipitate"
class Donor(Base):
    __tablename__ = "donors"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True)
    blood_type = Column(Enum(BloodType))
    last_donation_date = Column(DateTime)
    eligibility_status = Column(
        String, default="pending"
    )  
    eligibility_reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    donations = relationship("Donation", back_populates="donor")
class BloodBag(Base):
    __tablename__ = "blood_bags"
    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(Integer, ForeignKey("donations.id"))
    blood_type = Column(Enum(BloodType))
    component = Column(Enum(BloodComponent))
    volume_ml = Column(Integer)
    collection_date = Column(DateTime)
    expiration_date = Column(DateTime)
    storage_location = Column(String)
    status = Column(
        String, default="available"
    )  
    test_results = Column(String)  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    donation = relationship("Donation", back_populates="blood_bags")
    transfusions = relationship("Transfusion", back_populates="blood_bag")
class Donation(Base):
    __tablename__ = "donations"
    id = Column(Integer, primary_key=True, index=True)
    donor_id = Column(Integer, ForeignKey("donors.id"))
    donation_date = Column(DateTime, default=datetime.utcnow)
    volume_ml = Column(Integer)
    collection_staff_id = Column(Integer)
    collection_notes = Column(String)
    status = Column(
        String, default="collected"
    )  
    created_at = Column(DateTime, default=datetime.utcnow)
    donor = relationship("Donor", back_populates="donations")
    blood_bags = relationship("BloodBag", back_populates="donation")
class Transfusion(Base):
    __tablename__ = "transfusions"
    id = Column(Integer, primary_key=True, index=True)
    blood_bag_id = Column(Integer, ForeignKey("blood_bags.id"))
    patient_id = Column(Integer, index=True)
    doctor_id = Column(Integer, index=True)
    transfusion_date = Column(DateTime, default=datetime.utcnow)
    volume_ml = Column(Integer)
    vital_signs = Column(String)  
    adverse_reaction = Column(Boolean, default=False)
    reaction_details = Column(String)
    status = Column(
        String, default="completed"
    )  
    created_at = Column(DateTime, default=datetime.utcnow)
    blood_bag = relationship("BloodBag", back_populates="transfusions")
class BloodRequest(Base):
    __tablename__ = "blood_requests"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True)
    doctor_id = Column(Integer, index=True)
    blood_type = Column(Enum(BloodType))
    component = Column(Enum(BloodComponent))
    quantity = Column(Integer)
    urgency = Column(String)  
    status = Column(
        String, default="pending"
    )  
    approved_by = Column(Integer)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)