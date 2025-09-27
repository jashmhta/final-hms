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
    title="Bed Management Service",
    description="Enterprise-grade bed management for hospital inpatient departments",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {"message": "Bed Management Service is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/beds/", response_model=schemas.Bed)
def create_bed(bed: schemas.BedCreate, db: Session = Depends(get_db)):
    return crud.create_bed(db, bed)


@app.get("/beds/", response_model=List[schemas.Bed])
def read_beds(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_beds(db, skip=skip, limit=limit)


@app.get("/beds/{bed_id}", response_model=schemas.Bed)
def read_bed(bed_id: int, db: Session = Depends(get_db)):
    bed = crud.get_bed(db, bed_id=bed_id)
    if bed is None:
        raise HTTPException(status_code=404, detail="Bed not found")
    return bed


@app.get("/beds/available/", response_model=List[schemas.Bed])
def read_available_beds(ward_id: Optional[int] = None, db: Session = Depends(get_db)):
    return crud.get_available_beds(db, ward_id)


@app.patch("/beds/{bed_id}/status")
def update_bed_status(
    bed_id: int, status: schemas.BedStatus, db: Session = Depends(get_db)
):
    return crud.update_bed_status(db, bed_id, status)


@app.post("/wards/", response_model=schemas.Ward)
def create_ward(ward: schemas.WardCreate, db: Session = Depends(get_db)):
    return crud.create_ward(db, ward)


@app.get("/wards/", response_model=List[schemas.Ward])
def read_wards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_wards(db, skip=skip, limit=limit)


@app.get("/wards/{ward_id}", response_model=schemas.Ward)
def read_ward(ward_id: int, db: Session = Depends(get_db)):
    ward = crud.get_ward(db, ward_id=ward_id)
    if ward is None:
        raise HTTPException(status_code=404, detail="Ward not found")
    return ward


@app.post("/assignments/", response_model=schemas.BedAssignment)
def create_bed_assignment(
    assignment: schemas.BedAssignmentCreate, db: Session = Depends(get_db)
):
    return crud.create_bed_assignment(db, assignment)


@app.get("/assignments/", response_model=List[schemas.BedAssignment])
def read_bed_assignments(
    patient_id: Optional[str] = None, db: Session = Depends(get_db)
):
    return crud.get_active_bed_assignments(db, patient_id)


@app.patch("/assignments/{assignment_id}/discharge")
def discharge_patient(assignment_id: int, db: Session = Depends(get_db)):
    return crud.discharge_patient(db, assignment_id)


@app.post("/maintenance/", response_model=schemas.BedMaintenance)
def create_bed_maintenance(
    maintenance: schemas.BedMaintenanceCreate, db: Session = Depends(get_db)
):
    return crud.create_bed_maintenance(db, maintenance)


@app.get("/maintenance/", response_model=List[schemas.BedMaintenance])
def read_pending_maintenance(db: Session = Depends(get_db)):
    return crud.get_pending_maintenance(db)


@app.patch("/maintenance/{maintenance_id}/complete")
def complete_maintenance(maintenance_id: int, db: Session = Depends(get_db)):
    return crud.complete_maintenance(db, maintenance_id)


@app.get("/availability/", response_model=List[schemas.BedAvailability])
def get_bed_availability(ward_id: Optional[int] = None, db: Session = Depends(get_db)):
    return crud.get_bed_availability(db, ward_id)


@app.get("/statistics", response_model=schemas.BedStatistics)
def get_bed_statistics(db: Session = Depends(get_db)):
    return crud.get_bed_statistics(db)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9008)
