from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import crud, schemas, models
from database import get_db, engine, Base
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Housekeeping & Maintenance Service",
    description="Enterprise-grade housekeeping and maintenance management for hospitals",
    version="1.0.0"
)
@app.get("/")
async def root():
    return {"message": "Housekeeping & Maintenance Service is running"}
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
@app.post("/tasks/", response_model=schemas.HousekeepingTask)
def create_housekeeping_task(task: schemas.HousekeepingTaskCreate, db: Session = Depends(get_db)):
    return crud.create_housekeeping_task(db, task)
@app.get("/tasks/", response_model=List[schemas.HousekeepingTask])
def read_housekeeping_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_housekeeping_tasks(db, skip=skip, limit=limit)
@app.get("/tasks/{task_id}", response_model=schemas.HousekeepingTask)
def read_housekeeping_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_housekeeping_task(db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
@app.get("/tasks/status/{status}", response_model=List[schemas.HousekeepingTask])
def read_tasks_by_status(status: str, db: Session = Depends(get_db)):
    return crud.get_tasks_by_status(db, status)
@app.get("/tasks/priority/{priority}", response_model=List[schemas.HousekeepingTask])
def read_tasks_by_priority(priority: schemas.TaskPriority, db: Session = Depends(get_db)):
    return crud.get_tasks_by_priority(db, priority)
@app.get("/tasks/staff/{staff_member}", response_model=List[schemas.HousekeepingTask])
def read_tasks_by_staff(staff_member: str, db: Session = Depends(get_db)):
    return crud.get_tasks_by_staff(db, staff_member)
@app.patch("/tasks/{task_id}/status")
def update_task_status(task_id: int, status: str, notes: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.update_task_status(db, task_id, status, notes)
@app.post("/requests/", response_model=schemas.MaintenanceRequest)
def create_maintenance_request(request: schemas.MaintenanceRequestCreate, db: Session = Depends(get_db)):
    return crud.create_maintenance_request(db, request)
@app.get("/requests/", response_model=List[schemas.MaintenanceRequest])
def read_maintenance_requests(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_maintenance_requests(db, skip=skip, limit=limit)
@app.get("/requests/{request_id}", response_model=schemas.MaintenanceRequest)
def read_maintenance_request(request_id: int, db: Session = Depends(get_db)):
    request = crud.get_maintenance_request(db, request_id=request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return request
@app.get("/requests/status/{status}", response_model=List[schemas.MaintenanceRequest])
def read_requests_by_status(status: schemas.MaintenanceStatus, db: Session = Depends(get_db)):
    return crud.get_requests_by_status(db, status)
@app.get("/requests/priority/{priority}", response_model=List[schemas.MaintenanceRequest])
def read_requests_by_priority(priority: schemas.TaskPriority, db: Session = Depends(get_db)):
    return crud.get_requests_by_priority(db, priority)
@app.patch("/requests/{request_id}/assign")
def assign_maintenance_request(request_id: int, assigned_to: str, scheduled_date: datetime, db: Session = Depends(get_db)):
    return crud.assign_maintenance_request(db, request_id, assigned_to, scheduled_date)
@app.patch("/requests/{request_id}/complete")
def complete_maintenance_request(request_id: int, actual_cost: Optional[float] = None, notes: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.complete_maintenance_request(db, request_id, actual_cost, notes)
@app.post("/equipment/", response_model=schemas.Equipment)
def create_equipment(equipment: schemas.EquipmentCreate, db: Session = Depends(get_db)):
    return crud.create_equipment(db, equipment)
@app.get("/equipment/", response_model=List[schemas.Equipment])
def read_equipment_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_equipment_list(db, skip=skip, limit=limit)
@app.get("/equipment/{equipment_id}", response_model=schemas.Equipment)
def read_equipment(equipment_id: int, db: Session = Depends(get_db)):
    equipment = crud.get_equipment(db, equipment_id=equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment
@app.get("/equipment/status/{status}", response_model=List[schemas.Equipment])
def read_equipment_by_status(status: str, db: Session = Depends(get_db)):
    return crud.get_equipment_by_status(db, status)
@app.get("/equipment/due-maintenance/", response_model=List[schemas.Equipment])
def read_equipment_due_maintenance(db: Session = Depends(get_db)):
    return crud.get_equipment_due_maintenance(db)
@app.patch("/equipment/{equipment_id}/maintenance")
def update_equipment_maintenance(equipment_id: int, last_maintenance_date: datetime, next_maintenance_date: datetime, db: Session = Depends(get_db)):
    return crud.update_equipment_maintenance(db, equipment_id, last_maintenance_date, next_maintenance_date)
@app.post("/staff/", response_model=schemas.Staff)
def create_staff(staff: schemas.StaffCreate, db: Session = Depends(get_db)):
    return crud.create_staff(db, staff)
@app.get("/staff/", response_model=List[schemas.Staff])
def read_staff_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_staff_list(db, skip=skip, limit=limit)
@app.get("/staff/{staff_id}", response_model=schemas.Staff)
def read_staff(staff_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff(db, staff_id=staff_id)
    if staff is None:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff
@app.get("/staff/role/{role}", response_model=List[schemas.Staff])
def read_staff_by_role(role: str, db: Session = Depends(get_db)):
    return crud.get_staff_by_role(db, role)
@app.post("/schedules/", response_model=schemas.CleaningSchedule)
def create_cleaning_schedule(schedule: schemas.CleaningScheduleCreate, db: Session = Depends(get_db)):
    return crud.create_cleaning_schedule(db, schedule)
@app.get("/schedules/", response_model=List[schemas.CleaningSchedule])
def read_cleaning_schedules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_cleaning_schedules(db, skip=skip, limit=limit)
@app.get("/schedules/{schedule_id}", response_model=schemas.CleaningSchedule)
def read_cleaning_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = crud.get_cleaning_schedule(db, schedule_id=schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule
@app.get("/schedules/area/{area}", response_model=List[schemas.CleaningSchedule])
def read_schedules_by_area(area: str, db: Session = Depends(get_db)):
    return crud.get_schedules_by_area(db, area)
@app.get("/statistics", response_model=schemas.MaintenanceStatistics)
def get_maintenance_statistics(db: Session = Depends(get_db)):
    return crud.get_maintenance_statistics(db)
@app.get("/dashboard", response_model=schemas.TaskDashboard)
def get_task_dashboard(db: Session = Depends(get_db)):
    return crud.get_task_dashboard(db)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9011)