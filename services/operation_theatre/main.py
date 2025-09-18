from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import models, schemas, crud
from database import SessionLocal, engine
import uvicorn
import logging
models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Operation Theatre Management Service",
    description="Enterprise-grade Operation Theatre scheduling and management system",
    version="1.0.0"
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
    return {"status": "healthy", "service": "operation_theatre"}
@app.post("/surgeries/", response_model=schemas.Surgery)
async def schedule_surgery(
    surgery: schemas.SurgeryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    new_surgery = crud.create_surgery(db=db, surgery=surgery)
    background_tasks.add_task(crud.check_resource_availability, db, new_surgery.id)
    background_tasks.add_task(crud.notify_surgical_team, new_surgery.id)
    return new_surgery
@app.get("/surgeries/", response_model=List[schemas.Surgery])
async def get_surgeries(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    theatre_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return crud.get_surgeries(db, skip=skip, limit=limit, status=status, 
                             date_from=date_from, date_to=date_to, theatre_id=theatre_id)
@app.get("/surgeries/{surgery_id}", response_model=schemas.Surgery)
async def get_surgery(surgery_id: int, db: Session = Depends(get_db)):
    surgery = crud.get_surgery(db, surgery_id)
    if not surgery:
        raise HTTPException(status_code=404, detail="Surgery not found")
    return surgery
@app.patch("/surgeries/{surgery_id}/status")
async def update_surgery_status(
    surgery_id: int,
    status_update: schemas.SurgeryStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    surgery = crud.update_surgery_status(db, surgery_id, status_update)
    if not surgery:
        raise HTTPException(status_code=404, detail="Surgery not found")
    background_tasks.add_task(crud.log_surgery_timeline, surgery_id, status_update)
    background_tasks.add_task(crud.notify_status_change, surgery_id, status_update.status)
    return {"message": "Surgery status updated successfully", "surgery": surgery}
@app.get("/theatres/", response_model=List[schemas.OperatingTheatre])
async def get_operating_theatres(
    available_only: bool = False,
    date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    return crud.get_operating_theatres(db, available_only=available_only, date=date)
@app.get("/theatres/{theatre_id}/schedule")
async def get_theatre_schedule(
    theatre_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    if not date_from:
        date_from = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if not date_to:
        date_to = date_from + timedelta(days=7)
    return crud.get_theatre_schedule(db, theatre_id, date_from, date_to)
@app.post("/theatres/{theatre_id}/block")
async def block_theatre_time(
    theatre_id: int,
    block_request: schemas.TheatreBlockRequest,
    db: Session = Depends(get_db)
):
    block = crud.create_theatre_block(db, theatre_id, block_request)
    if not block:
        raise HTTPException(status_code=400, detail="Unable to block theatre time")
    return {"message": "Theatre time blocked successfully", "block": block}
@app.get("/surgical-teams/", response_model=List[schemas.SurgicalTeam])
async def get_surgical_teams(
    specialty: Optional[str] = None,
    available_only: bool = False,
    db: Session = Depends(get_db)
):
    return crud.get_surgical_teams(db, specialty=specialty, available_only=available_only)
@app.post("/surgical-teams/", response_model=schemas.SurgicalTeam)
async def create_surgical_team(
    team: schemas.SurgicalTeamCreate,
    db: Session = Depends(get_db)
):
    return crud.create_surgical_team(db=db, team=team)
@app.get("/surgeries/{surgery_id}/team", response_model=schemas.SurgicalTeamAssignment)
async def get_surgery_team(surgery_id: int, db: Session = Depends(get_db)):
    team = crud.get_surgery_team_assignment(db, surgery_id)
    if not team:
        raise HTTPException(status_code=404, detail="No team assigned to this surgery")
    return team
@app.post("/surgeries/{surgery_id}/assign-team")
async def assign_surgical_team(
    surgery_id: int,
    assignment: schemas.SurgicalTeamAssignmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    team_assignment = crud.assign_surgical_team(db, surgery_id, assignment)
    if not team_assignment:
        raise HTTPException(status_code=400, detail="Unable to assign team")
    background_tasks.add_task(crud.notify_team_assignment, surgery_id, assignment.team_id)
    return {"message": "Surgical team assigned successfully", "assignment": team_assignment}
@app.get("/equipment/", response_model=List[schemas.SurgicalEquipment])
async def get_surgical_equipment(
    available_only: bool = False,
    equipment_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return crud.get_surgical_equipment(db, available_only=available_only, equipment_type=equipment_type)
@app.post("/surgeries/{surgery_id}/equipment")
async def assign_equipment(
    surgery_id: int,
    equipment_assignment: schemas.EquipmentAssignmentCreate,
    db: Session = Depends(get_db)
):
    assignment = crud.assign_equipment_to_surgery(db, surgery_id, equipment_assignment)
    if not assignment:
        raise HTTPException(status_code=400, detail="Equipment not available or not found")
    return {"message": "Equipment assigned successfully", "assignment": assignment}
@app.get("/surgeries/{surgery_id}/equipment", response_model=List[schemas.EquipmentAssignment])
async def get_surgery_equipment(surgery_id: int, db: Session = Depends(get_db)):
    return crud.get_surgery_equipment_assignments(db, surgery_id)
@app.post("/surgeries/{surgery_id}/preop-checklist")
async def create_preop_checklist(
    surgery_id: int,
    checklist: schemas.PreOpChecklistCreate,
    db: Session = Depends(get_db)
):
    preop = crud.create_preop_checklist(db, surgery_id, checklist)
    return {"message": "Pre-operative checklist created", "checklist": preop}
@app.get("/surgeries/{surgery_id}/preop-checklist", response_model=schemas.PreOpChecklist)
async def get_preop_checklist(surgery_id: int, db: Session = Depends(get_db)):
    checklist = crud.get_preop_checklist(db, surgery_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Pre-operative checklist not found")
    return checklist
@app.post("/surgeries/{surgery_id}/postop-notes")
async def create_postop_notes(
    surgery_id: int,
    notes: schemas.PostOpNotesCreate,
    db: Session = Depends(get_db)
):
    postop = crud.create_postop_notes(db, surgery_id, notes)
    return {"message": "Post-operative notes created", "notes": postop}
@app.get("/surgeries/{surgery_id}/postop-notes", response_model=schemas.PostOpNotes)
async def get_postop_notes(surgery_id: int, db: Session = Depends(get_db)):
    notes = crud.get_postop_notes(db, surgery_id)
    if not notes:
        raise HTTPException(status_code=404, detail="Post-operative notes not found")
    return notes
@app.get("/analytics/dashboard")
async def get_ot_dashboard(db: Session = Depends(get_db)):
    return {
        "surgeries_today": crud.get_surgeries_count_today(db),
        "surgeries_this_week": crud.get_surgeries_count_week(db),
        "theatre_utilization": crud.get_theatre_utilization(db),
        "average_surgery_duration": crud.get_average_surgery_duration(db),
        "cancelled_surgeries_rate": crud.get_cancelled_surgeries_rate(db),
        "on_time_start_rate": crud.get_on_time_start_rate(db),
        "equipment_utilization": crud.get_equipment_utilization(db),
        "upcoming_surgeries": crud.get_upcoming_surgeries(db, limit=10)
    }
@app.get("/analytics/utilization")
async def get_utilization_analytics(
    days: int = 30,
    theatre_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return crud.get_utilization_analytics(db, days, theatre_id)
@app.get("/analytics/performance")
async def get_performance_metrics(
    days: int = 30,
    surgeon_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return {
        "average_surgery_time": crud.get_average_surgery_time(db, days, surgeon_id),
        "case_volume": crud.get_case_volume(db, days, surgeon_id),
        "complication_rate": crud.get_complication_rate(db, days, surgeon_id),
        "turnaround_time": crud.get_turnaround_time(db, days),
        "first_case_delays": crud.get_first_case_delays(db, days)
    }
@app.post("/scheduling/optimize")
async def optimize_schedule(
    optimization_request: schemas.ScheduleOptimizationRequest,
    db: Session = Depends(get_db)
):
    optimized_schedule = crud.optimize_surgery_schedule(db, optimization_request)
    return {
        "message": "Schedule optimization completed",
        "optimized_schedule": optimized_schedule,
        "efficiency_gain": optimized_schedule.get("efficiency_gain", 0)
    }
@app.get("/scheduling/conflicts")
async def check_scheduling_conflicts(
    date_from: datetime,
    date_to: datetime,
    db: Session = Depends(get_db)
):
    conflicts = crud.check_scheduling_conflicts(db, date_from, date_to)
    return {
        "conflicts_found": len(conflicts) > 0,
        "conflicts": conflicts
    }
@app.post("/emergency/schedule")
async def schedule_emergency_surgery(
    emergency_surgery: schemas.EmergencySurgeryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    surgery = crud.schedule_emergency_surgery(db, emergency_surgery)
    if not surgery:
        raise HTTPException(status_code=400, detail="Unable to schedule emergency surgery")
    background_tasks.add_task(crud.send_emergency_notifications, surgery.id)
    background_tasks.add_task(crud.auto_assign_emergency_team, surgery.id)
    return {
        "message": "Emergency surgery scheduled successfully",
        "surgery": surgery,
        "estimated_start_time": surgery.scheduled_start_time
    }
@app.get("/quality/metrics")
async def get_quality_metrics(db: Session = Depends(get_db)):
    return {
        "surgical_site_infection_rate": crud.get_ssi_rate(db),
        "wrong_site_surgery_incidents": crud.get_wrong_site_incidents(db),
        "timeout_compliance": crud.get_timeout_compliance(db),
        "count_compliance": crud.get_count_compliance(db),
        "mortality_rate": crud.get_surgical_mortality_rate(db),
        "readmission_rate": crud.get_surgical_readmission_rate(db)
    }
@app.post("/quality/incident")
async def report_safety_incident(
    incident: schemas.SafetyIncidentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    new_incident = crud.create_safety_incident(db, incident)
    if incident.severity in ['HIGH', 'CRITICAL']:
        background_tasks.add_task(crud.send_safety_alert, new_incident.id)
    return {"message": "Safety incident reported successfully", "incident": new_incident}
@app.get("/inventory/consumables")
async def get_consumables_inventory(
    low_stock_only: bool = False,
    db: Session = Depends(get_db)
):
    return crud.get_consumables_inventory(db, low_stock_only)
@app.post("/surgeries/{surgery_id}/consumables")
async def log_consumables_usage(
    surgery_id: int,
    usage: schemas.ConsumablesUsageCreate,
    db: Session = Depends(get_db)
):
    usage_record = crud.log_consumables_usage(db, surgery_id, usage)
    return {"message": "Consumables usage logged", "usage": usage_record}
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9019)