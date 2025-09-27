from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class CampaignType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    SOCIAL_MEDIA = "social_media"
    DIRECT_MAIL = "direct_mail"
    DIGITAL_ADS = "digital_ads"
    EVENTS = "events"


class CampaignStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LeadBase(BaseModel):
    lead_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    source: str
    priority: str = "medium"
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    expected_value: Optional[float] = None


class LeadCreate(LeadBase):
    pass


class Lead(LeadBase):
    id: int
    status: LeadStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignBase(BaseModel):
    campaign_id: str
    campaign_name: str
    campaign_type: CampaignType
    description: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    created_by: str


class CampaignCreate(CampaignBase):
    pass


class Campaign(CampaignBase):
    id: int
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignLeadBase(BaseModel):
    campaign_id: int
    lead_id: int


class CampaignLeadCreate(CampaignLeadBase):
    pass


class CampaignLead(CampaignLeadBase):
    id: int
    added_date: datetime

    class Config:
        from_attributes = True


class InteractionBase(BaseModel):
    interaction_id: str
    lead_id: int
    interaction_type: str
    subject: str
    description: str
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None
    performed_by: str


class InteractionCreate(InteractionBase):
    pass


class Interaction(InteractionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    customer_type: str
    acquisition_date: datetime
    last_contact_date: Optional[datetime] = None
    total_value: float = 0
    status: str = "active"
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class Customer(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OpportunityBase(BaseModel):
    opportunity_id: str
    customer_id: int
    opportunity_name: str
    description: Optional[str] = None
    stage: str
    probability: float = Field(..., ge=0, le=100)
    expected_value: float
    expected_close_date: datetime
    assigned_to: str
    source: Optional[str] = None
    notes: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    pass


class Opportunity(OpportunityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MarketingActivityBase(BaseModel):
    activity_id: str
    activity_name: str
    activity_type: str
    description: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    status: str = "planned"
    metrics: Optional[Dict[str, Any]] = None
    created_by: str


class MarketingActivityCreate(MarketingActivityBase):
    pass


class MarketingActivity(MarketingActivityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CRMStatistics(BaseModel):
    total_leads: int
    new_leads: int
    qualified_leads: int
    total_customers: int
    active_customers: int
    total_opportunities: int
    open_opportunities: int
    total_campaigns: int
    active_campaigns: int
    conversion_rate: float
    average_deal_size: float


class CRMDashboard(BaseModel):
    lead_pipeline: Dict[str, int]
    opportunity_pipeline: Dict[str, int]
    recent_activities: int
    upcoming_tasks: int
    monthly_revenue: float
    lead_conversion_rate: float
