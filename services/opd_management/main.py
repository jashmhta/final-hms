from datetime import datetime
from typing import List, Optional

import crud
import models
import schemas
from database import Base, engine, get_db
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OPD Management Service",
    description="Enterprise-grade OPD management for hospital outpatient departments",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {"message": "OPD Management Service is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# Patient endpoints
@app.post("/patients/", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    return crud.create_patient(db, patient)


@app.get("/patients/", response_model=List[schemas.Patient])
def read_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_patients(db, skip=skip, limit=limit)


@app.get("/patients/{patient_id}", response_model=schemas.Patient)
def read_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id=patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


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


# Appointment endpoints
@app.post("/appointments/", response_model=schemas.Appointment)
def create_appointment(
    appointment: schemas.AppointmentCreate, db: Session = Depends(get_db)
):
    return crud.create_appointment(db, appointment)


@app.get("/appointments/", response_model=List[schemas.Appointment])
def read_appointments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_appointments(db, skip=skip, limit=limit)


@app.get("/appointments/patient/{patient_id}", response_model=List[schemas.Appointment])
def read_patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    return crud.get_appointments_by_patient(db, patient_id)


@app.patch("/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int,
    status: schemas.AppointmentStatus,
    db: Session = Depends(get_db),
):
    return crud.update_appointment_status(db, appointment_id, status)


# Consultation endpoints
@app.post("/consultations/", response_model=schemas.Consultation)
def create_consultation(
    consultation: schemas.ConsultationCreate, db: Session = Depends(get_db)
):
    return crud.create_consultation(db, consultation)


@app.get(
    "/consultations/patient/{patient_id}", response_model=List[schemas.Consultation]
)
def read_patient_consultations(patient_id: int, db: Session = Depends(get_db)):
    return crud.get_consultations_by_patient(db, patient_id)


# Billing endpoints
@app.post("/bills/", response_model=schemas.OPDBill)
def create_bill(bill: schemas.OPDBillCreate, db: Session = Depends(get_db)):
    return crud.create_opd_bill(db, bill)


# Availability endpoints
@app.get("/availability/doctor/{doctor_id}")
def get_doctor_availability(
    doctor_id: int, date: datetime, db: Session = Depends(get_db)
):
    availability = crud.get_doctor_availability(db, doctor_id, date)
    if availability is None:
        raise HTTPException(status_code=404, detail="Doctor not found or not available")
    return availability


# Statistics endpoints
@app.get("/statistics")
def get_statistics(date: Optional[datetime] = None, db: Session = Depends(get_db)):
    if date is None:
        date = datetime.utcnow()
    return crud.get_opd_statistics(db, date)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8009)
