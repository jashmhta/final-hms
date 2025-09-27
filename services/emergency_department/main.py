"""
main module
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

import crud
import models
import schemas
import uvicorn
from database import SessionLocal, engine
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Emergency Department Service",
    description="Enterprise-grade Emergency Department management with advanced triage system",
    version="1.0.0",
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "emergency_department"}


@app.post("/visits/", response_model=schemas.EmergencyVisit)
async def create_emergency_visit(
    visit: schemas.EmergencyVisitCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    new_visit = crud.create_emergency_visit(db=db, visit=visit)
    background_tasks.add_task(crud.perform_automatic_triage, db, new_visit.id)
    if new_visit.triage_level in ["LEVEL_1", "LEVEL_2"]:
        background_tasks.add_task(crud.send_critical_alert, new_visit.id)
    return new_visit


@app.get("/visits/", response_model=List[schemas.EmergencyVisit])
async def get_emergency_visits(
    skip: int = 0,
    limit: int = 100,
    triage_level: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return crud.get_emergency_visits(
        db, skip=skip, limit=limit, triage_level=triage_level, status=status
    )


@app.get("/visits/{visit_id}", response_model=schemas.EmergencyVisit)
async def get_emergency_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = crud.get_emergency_visit(db, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Emergency visit not found")
    return visit


@app.patch("/visits/{visit_id}/triage")
async def update_triage(
    visit_id: int,
    triage_update: schemas.TriageUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    visit = crud.update_triage_assessment(db, visit_id, triage_update)
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    if triage_update.triage_level in ["LEVEL_1", "LEVEL_2"]:
        background_tasks.add_task(crud.send_triage_change_alert, visit_id)
    return {"message": "Triage updated successfully", "visit": visit}


@app.post("/visits/{visit_id}/vitals", response_model=schemas.VitalSigns)
async def record_vital_signs(
    visit_id: int, vitals: schemas.VitalSignsCreate, db: Session = Depends(get_db)
):
    return crud.create_vital_signs(db=db, visit_id=visit_id, vitals=vitals)


@app.get("/visits/{visit_id}/vitals", response_model=List[schemas.VitalSigns])
async def get_vital_signs(visit_id: int, db: Session = Depends(get_db)):
    return crud.get_vital_signs_by_visit(db, visit_id)


@app.post("/triage/assess", response_model=schemas.TriageAssessment)
async def create_triage_assessment(
    assessment: schemas.TriageAssessmentCreate, db: Session = Depends(get_db)
):
    return crud.create_triage_assessment(db=db, assessment=assessment)


@app.get("/triage/queue", response_model=List[schemas.EmergencyVisit])
async def get_triage_queue(db: Session = Depends(get_db)):
    return crud.get_triage_queue(db)


@app.get("/triage/priority-queue", response_model=List[schemas.EmergencyVisit])
async def get_priority_queue(db: Session = Depends(get_db)):
    return crud.get_priority_queue(db)


@app.post("/alerts/", response_model=schemas.EmergencyAlert)
async def create_emergency_alert(
    alert: schemas.EmergencyAlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    new_alert = crud.create_emergency_alert(db=db, alert=alert)
    background_tasks.add_task(crud.broadcast_alert, new_alert.id)
    return new_alert


@app.get("/alerts/active", response_model=List[schemas.EmergencyAlert])
async def get_active_alerts(db: Session = Depends(get_db)):
    return crud.get_active_alerts(db)


@app.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    acknowledgment: schemas.AlertAcknowledgment,
    db: Session = Depends(get_db),
):
    alert = crud.acknowledge_alert(db, alert_id, acknowledgment)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert acknowledged successfully"}


@app.get("/resources/beds", response_model=List[schemas.EmergencyBed])
async def get_emergency_beds(
    available_only: bool = False, db: Session = Depends(get_db)
):
    return crud.get_emergency_beds(db, available_only=available_only)


@app.patch("/resources/beds/{bed_id}/assign")
async def assign_bed(
    bed_id: int, assignment: schemas.BedAssignment, db: Session = Depends(get_db)
):
    bed = crud.assign_bed(db, bed_id, assignment)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found or unavailable")
    return {"message": "Bed assigned successfully", "bed": bed}


@app.get("/resources/staff", response_model=List[schemas.EmergencyStaff])
async def get_emergency_staff(
    on_duty_only: bool = False, db: Session = Depends(get_db)
):
    return crud.get_emergency_staff(db, on_duty_only=on_duty_only)


@app.get("/analytics/dashboard")
async def get_emergency_dashboard(db: Session = Depends(get_db)):
    return {
        "total_visits_today": crud.get_visits_count_today(db),
        "waiting_patients": crud.get_waiting_patients_count(db),
        "critical_patients": crud.get_critical_patients_count(db),
        "average_wait_time": crud.get_average_wait_time(db),
        "bed_occupancy": crud.get_bed_occupancy_rate(db),
        "staff_on_duty": crud.get_staff_on_duty_count(db),
        "active_alerts": crud.get_active_alerts_count(db),
        "triage_distribution": crud.get_triage_level_distribution(db),
    }


@app.get("/analytics/wait-times")
async def get_wait_time_analytics(days: int = 7, db: Session = Depends(get_db)):
    return crud.get_wait_time_analytics(db, days)


@app.get("/analytics/patient-flow")
async def get_patient_flow_analytics(hours: int = 24, db: Session = Depends(get_db)):
    return crud.get_patient_flow_analytics(db, hours)


@app.get("/quality/metrics")
async def get_quality_metrics(db: Session = Depends(get_db)):
    return {
        "door_to_doctor_time": crud.get_door_to_doctor_metric(db),
        "left_without_being_seen_rate": crud.get_lwbs_rate(db),
        "patient_satisfaction_score": crud.get_patient_satisfaction(db),
        "readmission_rate_72h": crud.get_readmission_rate(db),
        "mortality_rate": crud.get_mortality_rate(db),
        "compliance_scores": crud.get_compliance_scores(db),
    }


@app.get("/protocols/", response_model=List[schemas.EmergencyProtocol])
async def get_emergency_protocols(
    category: Optional[str] = None, db: Session = Depends(get_db)
):
    return crud.get_emergency_protocols(db, category=category)


@app.get("/protocols/{protocol_id}", response_model=schemas.EmergencyProtocol)
async def get_emergency_protocol(protocol_id: int, db: Session = Depends(get_db)):
    protocol = crud.get_emergency_protocol(db, protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol


@app.post("/protocols/{protocol_id}/activate")
async def activate_protocol(
    protocol_id: int,
    activation: schemas.ProtocolActivation,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    protocol_instance = crud.activate_protocol(db, protocol_id, activation)
    if not protocol_instance:
        raise HTTPException(status_code=404, detail="Protocol not found")
    background_tasks.add_task(crud.send_protocol_activation_alert, protocol_instance.id)
    return {"message": "Protocol activated successfully", "instance": protocol_instance}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9018)
