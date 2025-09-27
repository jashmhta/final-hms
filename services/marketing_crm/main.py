"""
main module
"""

from datetime import datetime
from typing import List, Optional

import crud
import models
import schemas
from database import Base, engine, get_db
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Marketing CRM Service",
    description="Enterprise-grade marketing and customer relationship management for hospitals",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {"message": "Marketing CRM Service is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/leads/", response_model=schemas.Lead)
def create_lead(lead: schemas.LeadCreate, db: Session = Depends(get_db)):
    return crud.create_lead(db, lead)


@app.get("/leads/", response_model=List[schemas.Lead])
def read_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_leads(db, skip=skip, limit=limit)


@app.get("/leads/{lead_id}", response_model=schemas.Lead)
def read_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = crud.get_lead(db, lead_id=lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.get("/leads/status/{status}", response_model=List[schemas.Lead])
def read_leads_by_status(status: schemas.LeadStatus, db: Session = Depends(get_db)):
    return crud.get_leads_by_status(db, status)


@app.get("/leads/source/{source}", response_model=List[schemas.Lead])
def read_leads_by_source(source: str, db: Session = Depends(get_db)):
    return crud.get_leads_by_source(db, source)


@app.get("/leads/assigned/{assigned_to}", response_model=List[schemas.Lead])
def read_leads_by_assigned_to(assigned_to: str, db: Session = Depends(get_db)):
    return crud.get_leads_by_assigned_to(db, assigned_to)


@app.patch("/leads/{lead_id}/status")
def update_lead_status(
    lead_id: int, status: schemas.LeadStatus, db: Session = Depends(get_db)
):
    return crud.update_lead_status(db, lead_id, status)


@app.post("/campaigns/", response_model=schemas.Campaign)
def create_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    return crud.create_campaign(db, campaign)


@app.get("/campaigns/", response_model=List[schemas.Campaign])
def read_campaigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_campaigns(db, skip=skip, limit=limit)


@app.get("/campaigns/{campaign_id}", response_model=schemas.Campaign)
def read_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = crud.get_campaign(db, campaign_id=campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@app.get("/campaigns/status/{status}", response_model=List[schemas.Campaign])
def read_campaigns_by_status(
    status: schemas.CampaignStatus, db: Session = Depends(get_db)
):
    return crud.get_campaigns_by_status(db, status)


@app.get("/campaigns/type/{campaign_type}", response_model=List[schemas.Campaign])
def read_campaigns_by_type(
    campaign_type: schemas.CampaignType, db: Session = Depends(get_db)
):
    return crud.get_campaigns_by_type(db, campaign_type)


@app.patch("/campaigns/{campaign_id}/status")
def update_campaign_status(
    campaign_id: int, status: schemas.CampaignStatus, db: Session = Depends(get_db)
):
    return crud.update_campaign_status(db, campaign_id, status)


@app.post("/campaigns/{campaign_id}/leads/{lead_id}")
def add_lead_to_campaign(campaign_id: int, lead_id: int, db: Session = Depends(get_db)):
    return crud.add_lead_to_campaign(db, campaign_id, lead_id)


@app.get("/campaigns/{campaign_id}/leads", response_model=List[schemas.CampaignLead])
def read_campaign_leads(campaign_id: int, db: Session = Depends(get_db)):
    return crud.get_campaign_leads(db, campaign_id)


@app.post("/interactions/", response_model=schemas.Interaction)
def create_interaction(
    interaction: schemas.InteractionCreate, db: Session = Depends(get_db)
):
    return crud.create_interaction(db, interaction)


@app.get("/interactions/{interaction_id}", response_model=schemas.Interaction)
def read_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = crud.get_interaction(db, interaction_id=interaction_id)
    if interaction is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@app.get("/interactions/lead/{lead_id}", response_model=List[schemas.Interaction])
def read_interactions_by_lead(lead_id: int, db: Session = Depends(get_db)):
    return crud.get_interactions_by_lead(db, lead_id)


@app.post("/customers/", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return crud.create_customer(db, customer)


@app.get("/customers/", response_model=List[schemas.Customer])
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_customers(db, skip=skip, limit=limit)


@app.get("/customers/{customer_id}", response_model=schemas.Customer)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = crud.get_customer(db, customer_id=customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.get("/customers/status/{status}", response_model=List[schemas.Customer])
def read_customers_by_status(status: str, db: Session = Depends(get_db)):
    return crud.get_customers_by_status(db, status)


@app.get("/customers/type/{customer_type}", response_model=List[schemas.Customer])
def read_customers_by_type(customer_type: str, db: Session = Depends(get_db)):
    return crud.get_customers_by_type(db, customer_type)


@app.patch("/customers/{customer_id}/value")
def update_customer_value(
    customer_id: int, additional_value: float, db: Session = Depends(get_db)
):
    return crud.update_customer_value(db, customer_id, additional_value)


@app.post("/opportunities/", response_model=schemas.Opportunity)
def create_opportunity(
    opportunity: schemas.OpportunityCreate, db: Session = Depends(get_db)
):
    return crud.create_opportunity(db, opportunity)


@app.get("/opportunities/", response_model=List[schemas.Opportunity])
def read_opportunities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_opportunities(db, skip=skip, limit=limit)


@app.get("/opportunities/{opportunity_id}", response_model=schemas.Opportunity)
def read_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opportunity = crud.get_opportunity(db, opportunity_id=opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity


@app.get(
    "/opportunities/customer/{customer_id}", response_model=List[schemas.Opportunity]
)
def read_opportunities_by_customer(customer_id: int, db: Session = Depends(get_db)):
    return crud.get_opportunities_by_customer(db, customer_id)


@app.get("/opportunities/stage/{stage}", response_model=List[schemas.Opportunity])
def read_opportunities_by_stage(stage: str, db: Session = Depends(get_db)):
    return crud.get_opportunities_by_stage(db, stage)


@app.get(
    "/opportunities/assigned/{assigned_to}", response_model=List[schemas.Opportunity]
)
def read_opportunities_by_assigned_to(assigned_to: str, db: Session = Depends(get_db)):
    return crud.get_opportunities_by_assigned_to(db, assigned_to)


@app.patch("/opportunities/{opportunity_id}/stage")
def update_opportunity_stage(
    opportunity_id: int, stage: str, probability: float, db: Session = Depends(get_db)
):
    return crud.update_opportunity_stage(db, opportunity_id, stage, probability)


@app.post("/activities/", response_model=schemas.MarketingActivity)
def create_marketing_activity(
    activity: schemas.MarketingActivityCreate, db: Session = Depends(get_db)
):
    return crud.create_marketing_activity(db, activity)


@app.get("/activities/", response_model=List[schemas.MarketingActivity])
def read_marketing_activities(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return crud.get_marketing_activities(db, skip=skip, limit=limit)


@app.get("/activities/{activity_id}", response_model=schemas.MarketingActivity)
def read_marketing_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = crud.get_marketing_activity(db, activity_id=activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Marketing activity not found")
    return activity


@app.get("/activities/status/{status}", response_model=List[schemas.MarketingActivity])
def read_activities_by_status(status: str, db: Session = Depends(get_db)):
    return crud.get_activities_by_status(db, status)


@app.get(
    "/activities/type/{activity_type}", response_model=List[schemas.MarketingActivity]
)
def read_activities_by_type(activity_type: str, db: Session = Depends(get_db)):
    return crud.get_activities_by_type(db, activity_type)


@app.patch("/activities/{activity_id}/metrics")
def update_activity_metrics(
    activity_id: int, metrics: dict, db: Session = Depends(get_db)
):
    return crud.update_activity_metrics(db, activity_id, metrics)


@app.get("/statistics", response_model=schemas.CRMStatistics)
def get_crm_statistics(db: Session = Depends(get_db)):
    return crud.get_crm_statistics(db)


@app.get("/dashboard", response_model=schemas.CRMDashboard)
def get_crm_dashboard(db: Session = Depends(get_db)):
    return crud.get_crm_dashboard(db)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9013)
