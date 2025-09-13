from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import crud, schemas, models
from database import get_db, engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Biomedical Equipment Service",
    description="Enterprise-grade biomedical equipment management for hospitals",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Biomedical Equipment Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Equipment endpoints
@app.post("/equipment/", response_model=schemas.BiomedicalEquipment)
def create_equipment(equipment: schemas.BiomedicalEquipmentCreate, db: Session = Depends(get_db)):
    return crud.create_equipment(db, equipment)

@app.get("/equipment/", response_model=List[schemas.BiomedicalEquipment])
def read_equipment_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_equipment_list(db, skip=skip, limit=limit)

@app.get("/equipment/{equipment_id}", response_model=schemas.BiomedicalEquipment)
def read_equipment(equipment_id: int, db: Session = Depends(get_db)):
    equipment = crud.get_equipment(db, equipment_id=equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment

@app.get("/equipment/status/{status}", response_model=List[schemas.BiomedicalEquipment])
def read_equipment_by_status(status: schemas.EquipmentStatus, db: Session = Depends(get_db)):
    return crud.get_equipment_by_status(db, status)

@app.get("/equipment/category/{category}", response_model=List[schemas.BiomedicalEquipment])
def read_equipment_by_category(category: schemas.EquipmentCategory, db: Session = Depends(get_db)):
    return crud.get_equipment_by_category(db, category)

@app.get("/equipment/department/{department}", response_model=List[schemas.BiomedicalEquipment])
def read_equipment_by_department(department: str, db: Session = Depends(get_db)):
    return crud.get_equipment_by_department(db, department)

@app.patch("/equipment/{equipment_id}/status")
def update_equipment_status(equipment_id: int, status: schemas.EquipmentStatus, db: Session = Depends(get_db)):
    return crud.update_equipment_status(db, equipment_id, status)

# Maintenance endpoints
@app.post("/maintenance/", response_model=schemas.EquipmentMaintenance)
def create_maintenance(maintenance: schemas.EquipmentMaintenanceCreate, db: Session = Depends(get_db)):
    return crud.create_maintenance(db, maintenance)

@app.get("/maintenance/{maintenance_id}", response_model=schemas.EquipmentMaintenance)
def read_maintenance(maintenance_id: int, db: Session = Depends(get_db)):
    maintenance = crud.get_maintenance(db, maintenance_id=maintenance_id)
    if maintenance is None:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return maintenance

@app.get("/maintenance/equipment/{equipment_id}", response_model=List[schemas.EquipmentMaintenance])
def read_maintenance_by_equipment(equipment_id: int, db: Session = Depends(get_db)):
    return crud.get_maintenance_by_equipment(db, equipment_id)

@app.get("/maintenance/upcoming/", response_model=List[schemas.EquipmentMaintenance])
def read_upcoming_maintenance(days_ahead: int = 30, db: Session = Depends(get_db)):
    return crud.get_upcoming_maintenance(db, days_ahead)

@app.get("/maintenance/overdue/", response_model=List[schemas.EquipmentMaintenance])
def read_overdue_maintenance(db: Session = Depends(get_db)):
    return crud.get_overdue_maintenance(db)

@app.patch("/maintenance/{maintenance_id}/complete")
def complete_maintenance(maintenance_id: int, findings: str, actions_taken: str, next_maintenance_date: Optional[datetime] = None, db: Session = Depends(get_db)):
    return crud.complete_maintenance(db, maintenance_id, findings, actions_taken, next_maintenance_date)

# Calibration endpoints
@app.post("/calibration/", response_model=schemas.EquipmentCalibration)
def create_calibration(calibration: schemas.EquipmentCalibrationCreate, db: Session = Depends(get_db)):
    return crud.create_calibration(db, calibration)

@app.get("/calibration/{calibration_id}", response_model=schemas.EquipmentCalibration)
def read_calibration(calibration_id: int, db: Session = Depends(get_db)):
    calibration = crud.get_calibration(db, calibration_id=calibration_id)
    if calibration is None:
        raise HTTPException(status_code=404, detail="Calibration record not found")
    return calibration

@app.get("/calibration/equipment/{equipment_id}", response_model=List[schemas.EquipmentCalibration])
def read_calibration_by_equipment(equipment_id: int, db: Session = Depends(get_db)):
    return crud.get_calibration_by_equipment(db, equipment_id)

@app.get("/calibration/overdue/", response_model=List[schemas.EquipmentCalibration])
def read_overdue_calibrations(db: Session = Depends(get_db)):
    return crud.get_overdue_calibrations(db)

# Incident endpoints
@app.post("/incidents/", response_model=schemas.EquipmentIncident)
def create_incident(incident: schemas.EquipmentIncidentCreate, db: Session = Depends(get_db)):
    return crud.create_incident(db, incident)

@app.get("/incidents/{incident_id}", response_model=schemas.EquipmentIncident)
def read_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = crud.get_incident(db, incident_id=incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@app.get("/incidents/equipment/{equipment_id}", response_model=List[schemas.EquipmentIncident])
def read_incidents_by_equipment(equipment_id: int, db: Session = Depends(get_db)):
    return crud.get_incidents_by_equipment(db, equipment_id)

@app.get("/incidents/open/", response_model=List[schemas.EquipmentIncident])
def read_open_incidents(db: Session = Depends(get_db)):
    return crud.get_open_incidents(db)

@app.patch("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: int, resolution: str, db: Session = Depends(get_db)):
    return crud.resolve_incident(db, incident_id, resolution)

# Training endpoints
@app.post("/training/", response_model=schemas.EquipmentTraining)
def create_training(training: schemas.EquipmentTrainingCreate, db: Session = Depends(get_db)):
    return crud.create_training(db, training)

@app.get("/training/{training_id}", response_model=schemas.EquipmentTraining)
def read_training(training_id: int, db: Session = Depends(get_db)):
    training = crud.get_training(db, training_id=training_id)
    if training is None:
        raise HTTPException(status_code=404, detail="Training record not found")
    return training

@app.get("/training/equipment/{equipment_id}", response_model=List[schemas.EquipmentTraining])
def read_training_by_equipment(equipment_id: int, db: Session = Depends(get_db)):
    return crud.get_training_by_equipment(db, equipment_id)

@app.get("/training/staff/{staff_member}", response_model=List[schemas.EquipmentTraining])
def read_training_by_staff(staff_member: str, db: Session = Depends(get_db)):
    return crud.get_training_by_staff(db, staff_member)

# Vendor endpoints
@app.post("/vendors/", response_model=schemas.Vendor)
def create_vendor(vendor: schemas.VendorCreate, db: Session = Depends(get_db)):
    return crud.create_vendor(db, vendor)

@app.get("/vendors/", response_model=List[schemas.Vendor])
def read_vendors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_vendors(db, skip=skip, limit=limit)

@app.get("/vendors/{vendor_id}", response_model=schemas.Vendor)
def read_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = crud.get_vendor(db, vendor_id=vendor_id)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

# Statistics endpoints
@app.get("/statistics", response_model=schemas.EquipmentStatistics)
def get_equipment_statistics(db: Session = Depends(get_db)):
    return crud.get_equipment_statistics(db)

@app.get("/dashboard", response_model=schemas.EquipmentDashboard)
def get_equipment_dashboard(db: Session = Depends(get_db)):
    return crud.get_equipment_dashboard(db)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9012)