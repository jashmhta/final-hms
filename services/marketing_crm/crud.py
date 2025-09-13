from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import models
import schemas

def get_lead(db: Session, lead_id: int):
    return db.query(models.Lead).filter(models.Lead.id == lead_id).first()

def get_lead_by_lead_id(db: Session, lead_id_str: str):
    return db.query(models.Lead).filter(models.Lead.lead_id == lead_id_str).first()

def get_leads(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Lead).offset(skip).limit(limit).all()

def get_leads_by_status(db: Session, status: schemas.LeadStatus):
    return db.query(models.Lead).filter(models.Lead.status == status).all()

def get_leads_by_source(db: Session, source: str):
    return db.query(models.Lead).filter(models.Lead.source == source).all()

def get_leads_by_assigned_to(db: Session, assigned_to: str):
    return db.query(models.Lead).filter(models.Lead.assigned_to == assigned_to).all()

def create_lead(db: Session, lead: schemas.LeadCreate):
    db_lead = models.Lead(**lead.dict())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

def update_lead_status(db: Session, lead_id: int, status: schemas.LeadStatus):
    db_lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if db_lead:
        db_lead.status = status
        db_lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_lead)
    return db_lead

def get_campaign(db: Session, campaign_id: int):
    return db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()

def get_campaigns(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Campaign).offset(skip).limit(limit).all()

def get_campaigns_by_status(db: Session, status: schemas.CampaignStatus):
    return db.query(models.Campaign).filter(models.Campaign.status == status).all()

def get_campaigns_by_type(db: Session, campaign_type: schemas.CampaignType):
    return db.query(models.Campaign).filter(models.Campaign.campaign_type == campaign_type).all()

def create_campaign(db: Session, campaign: schemas.CampaignCreate):
    db_campaign = models.Campaign(**campaign.dict())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

def update_campaign_status(db: Session, campaign_id: int, status: schemas.CampaignStatus):
    db_campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if db_campaign:
        db_campaign.status = status
        db_campaign.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_campaign)
    return db_campaign

def add_lead_to_campaign(db: Session, campaign_id: int, lead_id: int):
    db_campaign_lead = models.CampaignLead(campaign_id=campaign_id, lead_id=lead_id)
    db.add(db_campaign_lead)
    db.commit()
    db.refresh(db_campaign_lead)
    return db_campaign_lead

def get_campaign_leads(db: Session, campaign_id: int):
    return db.query(models.CampaignLead).filter(models.CampaignLead.campaign_id == campaign_id).all()

def get_interaction(db: Session, interaction_id: int):
    return db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()

def get_interactions_by_lead(db: Session, lead_id: int):
    return db.query(models.Interaction).filter(models.Interaction.lead_id == lead_id).all()

def create_interaction(db: Session, interaction: schemas.InteractionCreate):
    db_interaction = models.Interaction(**interaction.dict())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_customer_by_customer_id(db: Session, customer_id_str: str):
    return db.query(models.Customer).filter(models.Customer.customer_id == customer_id_str).first()

def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()

def get_customers_by_status(db: Session, status: str):
    return db.query(models.Customer).filter(models.Customer.status == status).all()

def get_customers_by_type(db: Session, customer_type: str):
    return db.query(models.Customer).filter(models.Customer.customer_type == customer_type).all()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def update_customer_value(db: Session, customer_id: int, additional_value: float):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if db_customer:
        db_customer.total_value += additional_value
        db_customer.last_contact_date = datetime.utcnow()
        db_customer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_customer)
    return db_customer

def get_opportunity(db: Session, opportunity_id: int):
    return db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()

def get_opportunities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Opportunity).offset(skip).limit(limit).all()

def get_opportunities_by_customer(db: Session, customer_id: int):
    return db.query(models.Opportunity).filter(models.Opportunity.customer_id == customer_id).all()

def get_opportunities_by_stage(db: Session, stage: str):
    return db.query(models.Opportunity).filter(models.Opportunity.stage == stage).all()

def get_opportunities_by_assigned_to(db: Session, assigned_to: str):
    return db.query(models.Opportunity).filter(models.Opportunity.assigned_to == assigned_to).all()

def create_opportunity(db: Session, opportunity: schemas.OpportunityCreate):
    db_opportunity = models.Opportunity(**opportunity.dict())
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)
    return db_opportunity

def update_opportunity_stage(db: Session, opportunity_id: int, stage: str, probability: float):
    db_opportunity = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if db_opportunity:
        db_opportunity.stage = stage
        db_opportunity.probability = probability
        db_opportunity.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_opportunity)
    return db_opportunity

def get_marketing_activity(db: Session, activity_id: int):
    return db.query(models.MarketingActivity).filter(models.MarketingActivity.id == activity_id).first()

def get_marketing_activities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.MarketingActivity).offset(skip).limit(limit).all()

def get_activities_by_status(db: Session, status: str):
    return db.query(models.MarketingActivity).filter(models.MarketingActivity.status == status).all()

def get_activities_by_type(db: Session, activity_type: str):
    return db.query(models.MarketingActivity).filter(models.MarketingActivity.activity_type == activity_type).all()

def create_marketing_activity(db: Session, activity: schemas.MarketingActivityCreate):
    db_activity = models.MarketingActivity(**activity.dict())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

def update_activity_metrics(db: Session, activity_id: int, metrics: Dict[str, Any]):
    db_activity = db.query(models.MarketingActivity).filter(models.MarketingActivity.id == activity_id).first()
    if db_activity:
        db_activity.metrics = metrics
        db_activity.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_activity)
    return db_activity

def get_crm_statistics(db: Session):
    total_leads = db.query(models.Lead).count()
    new_leads = db.query(models.Lead).filter(models.Lead.status == models.LeadStatus.NEW).count()
    qualified_leads = db.query(models.Lead).filter(models.Lead.status == models.LeadStatus.QUALIFIED).count()
    
    total_customers = db.query(models.Customer).count()
    active_customers = db.query(models.Customer).filter(models.Customer.status == "active").count()
    
    total_opportunities = db.query(models.Opportunity).count()
    open_opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.stage.in_(["prospecting", "qualification", "proposal", "negotiation"])
    ).count()
    
    total_campaigns = db.query(models.Campaign).count()
    active_campaigns = db.query(models.Campaign).filter(models.Campaign.status == models.CampaignStatus.ACTIVE).count()
    
    # Conversion rate (leads to customers)
    converted_leads = db.query(models.Lead).filter(models.Lead.status == models.LeadStatus.CLOSED_WON).count()
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0
    
    # Average deal size
    opportunities = db.query(models.Opportunity).all()
    average_deal_size = sum(o.expected_value for o in opportunities) / len(opportunities) if opportunities else 0.0
    
    return {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "qualified_leads": qualified_leads,
        "total_customers": total_customers,
        "active_customers": active_customers,
        "total_opportunities": total_opportunities,
        "open_opportunities": open_opportunities,
        "total_campaigns": total_campaigns,
        "active_campaigns": active_campaigns,
        "conversion_rate": conversion_rate,
        "average_deal_size": average_deal_size
    }

def get_crm_dashboard(db: Session):
    # Lead pipeline
    lead_pipeline = {}
    for status in models.LeadStatus:
        count = db.query(models.Lead).filter(models.Lead.status == status).count()
        lead_pipeline[status.value] = count
    
    # Opportunity pipeline
    opportunity_pipeline = {}
    stages = ["prospecting", "qualification", "proposal", "negotiation", "closed"]
    for stage in stages:
        count = db.query(models.Opportunity).filter(models.Opportunity.stage == stage).count()
        opportunity_pipeline[stage] = count
    
    # Recent activities (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_activities = db.query(models.Interaction).filter(
        models.Interaction.created_at >= week_ago
    ).count()
    
    # Upcoming tasks (interactions with next_action_date in next 7 days)
    next_week = datetime.utcnow() + timedelta(days=7)
    upcoming_tasks = db.query(models.Interaction).filter(
        models.Interaction.next_action_date <= next_week,
        models.Interaction.next_action_date >= datetime.utcnow()
    ).count()
    
    # Monthly revenue (opportunities closed this month)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    monthly_opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.stage == "closed",
        models.Opportunity.updated_at >= month_start
    ).all()
    monthly_revenue = sum(o.expected_value for o in monthly_opportunities)
    
    # Lead conversion rate
    total_leads = db.query(models.Lead).count()
    converted_leads = db.query(models.Lead).filter(models.Lead.status == models.LeadStatus.CLOSED_WON).count()
    lead_conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0
    
    return {
        "lead_pipeline": lead_pipeline,
        "opportunity_pipeline": opportunity_pipeline,
        "recent_activities": recent_activities,
        "upcoming_tasks": upcoming_tasks,
        "monthly_revenue": monthly_revenue,
        "lead_conversion_rate": lead_conversion_rate
    }