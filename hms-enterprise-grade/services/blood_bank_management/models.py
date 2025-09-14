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


class BloodType(enum.Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class BloodUnit(Base):
    __tablename__ = "blood_units"

    id = Column(Integer, primary_key=True, index=True)
    unit_number = Column(String, unique=True)
    blood_type = Column(Enum(BloodType))
    rh_factor = Column(String)  # Positive, Negative
    collection_date = Column(DateTime)
    expiration_date = Column(DateTime)
    volume_ml = Column(Integer)
    donor_id = Column(Integer, ForeignKey("donors.id"))
    test_results = Column(JSON)  # HIV, Hepatitis, etc.
    status = Column(String)  # available, reserved, transfused, expired, discarded
    storage_location = Column(String)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    donor = relationship("Donor")


class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, index=True)
    donor_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    date_of_birth = Column(DateTime)
    gender = Column(String)
    blood_type = Column(Enum(BloodType))
    rh_factor = Column(String)
    contact_number = Column(String)
    email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    eligibility_status = Column(
        String
    )  # eligible, temporary_deferral, permanent_deferral
    last_donation_date = Column(DateTime, nullable=True)
    total_donations = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(String, unique=True)
    donor_id = Column(Integer, ForeignKey("donors.id"))
    donation_date = Column(DateTime)
    volume_ml = Column(Integer)
    collection_method = Column(String)  # whole_blood, plateletpheresis, etc.
    collection_staff = Column(String)
    test_results = Column(JSON)
    status = Column(String)  # collected, tested, approved, rejected
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    donor = relationship("Donor")


class TransfusionRequest(Base):
    __tablename__ = "transfusion_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True)
    patient_id = Column(Integer)
    patient_blood_type = Column(Enum(BloodType))
    patient_rh_factor = Column(String)
    requested_blood_type = Column(Enum(BloodType))
    requested_rh_factor = Column(String)
    units_requested = Column(Integer)
    urgency = Column(String)  # emergency, urgent, routine
    requested_by = Column(String)
    request_date = Column(DateTime)
    status = Column(String)  # pending, approved, fulfilled, cancelled
    approved_units = Column(Integer, default=0)
    fulfilled_units = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transfusion(Base):
    __tablename__ = "transfusions"

    id = Column(Integer, primary_key=True, index=True)
    transfusion_id = Column(String, unique=True)
    request_id = Column(Integer, ForeignKey("transfusion_requests.id"))
    blood_unit_id = Column(Integer, ForeignKey("blood_units.id"))
    patient_id = Column(Integer)
    transfusion_date = Column(DateTime)
    administered_by = Column(String)
    vital_signs = Column(JSON)  # pre and post transfusion vitals
    adverse_reactions = Column(JSON, nullable=True)
    outcome = Column(String)  # successful, partial, adverse_reaction
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    blood_unit = relationship("BloodUnit")
    request = relationship("TransfusionRequest")


class BloodTest(Base):
    __tablename__ = "blood_tests"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String, unique=True)
    blood_unit_id = Column(Integer, ForeignKey("blood_units.id"))
    test_type = Column(String)  # HIV, Hepatitis_B, Hepatitis_C, Syphilis, etc.
    test_date = Column(DateTime)
    result = Column(String)  # positive, negative, indeterminate
    performed_by = Column(String)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    blood_unit = relationship("BloodUnit")


class InventoryAlert(Base):
    __tablename__ = "inventory_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String)  # low_stock, expiration, critical_stock
    blood_type = Column(Enum(BloodType))
    rh_factor = Column(String)
    current_quantity = Column(Integer)
    threshold = Column(Integer)
    alert_message = Column(Text)
    severity = Column(String)  # low, medium, high, critical
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
