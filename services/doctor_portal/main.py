from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import crud, schemas, models
from database import get_db, engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Doctor Portal Service",
    description="Enterprise-grade doctor portal for hospital management",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Doctor Portal Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Doctor endpoints
@app.post("/doctors/", response_model=schemas.Doctor)
def create_doctor(doctor: schemas.DoctorCreate, db: Session = Depends(get_db)):
    return crud.create_doctor(db, doctor)

@app.get("/doctors/", response_model=List[schemas.Doctor])
def read_doctors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_doctors(db, skip=skip, limit=limit)

@app.get("/doctors/{doctor_id}", response_model=schemas.Doctor)
def read_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = crud.get_doctor(db, doctor_id=doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@app.get("/doctors/specialization/{specialization}", response_model=List[schemas.Doctor])
def read_doctors_by_specialization(specialization: schemas.DoctorSpecialization, db: Session = Depends(get_db)):
    return crud.get_doctors_by_specialization(db, specialization)

@app.get("/doctors/available/", response_model=List[schemas.Doctor])
def read_available_doctors(specialization: Optional[schemas.DoctorSpecialization] = None, db: Session = Depends(get_db)):
    return crud.get_available_doctors(db, specialization)

@app.patch("/doctors/{doctor_id}")
def update_doctor(doctor_id: int, doctor_update: dict, db: Session = Depends(get_db)):
    return crud.update_doctor(db, doctor_id, doctor_update)

# Department endpoints
@app.post("/departments/", response_model=schemas.Department)
def create_department(department: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    return crud.create_department(db, department)

@app.get("/departments/", response_model=List[schemas.Department])
def read_departments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_departments(db, skip=skip, limit=limit)

@app.get("/departments/{department_id}", response_model=schemas.Department)
def read_department(department_id: int, db: Session = Depends(get_db)):
    department = crud.get_department(db, department_id=department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return department

# Schedule endpoints
@app.post("/schedules/", response_model=schemas.DoctorSchedule)
def create_doctor_schedule(schedule: schemas.DoctorScheduleCreate, db: Session = Depends(get_db)):
    return crud.create_doctor_schedule(db, schedule)

@app.get("/schedules/doctor/{doctor_id}", response_model=List[schemas.DoctorSchedule])
def read_doctor_schedule(doctor_id: int, day_of_week: Optional[int] = None, db: Session = Depends(get_db)):
    return crud.get_doctor_schedule(db, doctor_id, day_of_week)

# Leave endpoints
@app.post("/leaves/", response_model=schemas.DoctorLeave)
def create_doctor_leave(leave: schemas.DoctorLeaveCreate, db: Session = Depends(get_db)):
    return crud.create_doctor_leave(db, leave)

@app.get("/leaves/doctor/{doctor_id}", response_model=List[schemas.DoctorLeave])
def read_doctor_leaves(doctor_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_doctor_leaves(db, doctor_id, status)

@app.patch("/leaves/{leave_id}/approve")
def approve_doctor_leave(leave_id: int, approved_by: str, db: Session = Depends(get_db)):
    return crud.approve_doctor_leave(db, leave_id, approved_by)

# Performance endpoints
@app.post("/performance/", response_model=schemas.DoctorPerformance)
def create_doctor_performance(performance: schemas.DoctorPerformanceCreate, db: Session = Depends(get_db)):
    return crud.create_doctor_performance(db, performance)

@app.get("/performance/doctor/{doctor_id}", response_model=List[schemas.DoctorPerformance])
def read_doctor_performance(doctor_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, db: Session = Depends(get_db)):
    return crud.get_doctor_performance(db, doctor_id, start_date, end_date)

# Dashboard endpoints
@app.get("/dashboard/doctor/{doctor_id}", response_model=schemas.DoctorDashboard)
def get_doctor_dashboard(doctor_id: int, db: Session = Depends(get_db)):
    dashboard = crud.get_doctor_dashboard(db, doctor_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return dashboard

# Statistics endpoints
@app.get("/statistics", response_model=schemas.DoctorStatistics)
def get_doctor_statistics(db: Session = Depends(get_db)):
    return crud.get_doctor_statistics(db)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9009)