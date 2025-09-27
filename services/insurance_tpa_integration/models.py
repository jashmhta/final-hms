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


class InsuranceProvider(Base):
    __tablename__ = "insurance_providers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    code = Column(String, unique=True)
    tpa_code = Column(String)
    api_endpoint = Column(String)
    api_key = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True)
    policy_number = Column(String)
    insurance_provider_id = Column(Integer, ForeignKey("insurance_providers.id"))
    group_number = Column(String)
    effective_date = Column(DateTime)
    expiration_date = Column(DateTime)
    coverage_details = Column(JSON)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    provider = relationship("InsuranceProvider")


class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"
    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String, unique=True)
    patient_id = Column(Integer, index=True)
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"))
    billing_id = Column(Integer, index=True)
    total_amount = Column(Float)
    approved_amount = Column(Float)
    status = Column(String)
    submission_date = Column(DateTime)
    approval_date = Column(DateTime, nullable=True)
    payment_date = Column(DateTime, nullable=True)
    denial_reason = Column(Text, nullable=True)
    resubmission_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    policy = relationship("InsurancePolicy")


class TPATransaction(Base):
    __tablename__ = "tpa_transactions"
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("insurance_claims.id"))
    tpa_reference = Column(String)
    transaction_type = Column(String)
    request_data = Column(JSON)
    response_data = Column(JSON)
    status_code = Column(Integer)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    claim = relationship("InsuranceClaim")


class PaymentRecord(Base):
    __tablename__ = "payment_records"
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("insurance_claims.id"))
    payment_amount = Column(Float)
    payment_date = Column(DateTime)
    payment_method = Column(String)
    reference_number = Column(String)
    adjustment_details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    claim = relationship("InsuranceClaim")
