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


class LeadStatus(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class CampaignType(enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    SOCIAL_MEDIA = "social_media"
    DIRECT_MAIL = "direct_mail"
    DIGITAL_ADS = "digital_ads"
    EVENTS = "events"


class CampaignStatus(enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    source = Column(String)
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    priority = Column(String)
    assigned_to = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    expected_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String, unique=True)
    campaign_name = Column(String)
    campaign_type = Column(Enum(CampaignType))
    description = Column(Text, nullable=True)
    target_audience = Column(JSON, nullable=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    budget = Column(Float, nullable=True)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.PLANNED)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CampaignLead(Base):
    __tablename__ = "campaign_leads"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"))
    added_date = Column(DateTime, default=datetime.utcnow)
    campaign = relationship("Campaign")
    lead = relationship("Lead")


class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(String, unique=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    interaction_type = Column(String)
    subject = Column(String)
    description = Column(Text)
    outcome = Column(String, nullable=True)
    next_action = Column(String, nullable=True)
    next_action_date = Column(DateTime, nullable=True)
    performed_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lead = relationship("Lead")


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    customer_type = Column(String)
    acquisition_date = Column(DateTime)
    last_contact_date = Column(DateTime, nullable=True)
    total_value = Column(Float, default=0)
    status = Column(String)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(String, unique=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    opportunity_name = Column(String)
    description = Column(Text, nullable=True)
    stage = Column(String)
    probability = Column(Float)
    expected_value = Column(Float)
    expected_close_date = Column(DateTime)
    assigned_to = Column(String)
    source = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    customer = relationship("Customer")


class MarketingActivity(Base):
    __tablename__ = "marketing_activities"
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(String, unique=True)
    activity_name = Column(String)
    activity_type = Column(String)
    description = Column(Text, nullable=True)
    target_audience = Column(JSON, nullable=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    budget = Column(Float, nullable=True)
    status = Column(String)
    metrics = Column(JSON, nullable=True)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
