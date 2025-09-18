from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import crud, schemas, models
from database import get_db, engine, Base
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Patient Portal Service",
    description="Enterprise-grade patient portal for hospital management",
    version="1.0.0"
)
@app.get("/")
async def root():
    return {"message": "Patient Portal Service is running"}
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
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
@app.patch("/patients/{patient_id}")
def update_patient(patient_id: int, patient_update: dict, db: Session = Depends(get_db)):
    return crud.update_patient(db, patient_id, patient_update)
@app.post("/auth/register", response_model=schemas.PatientLogin)
def register_patient(login: schemas.PatientLoginCreate, db: Session = Depends(get_db)):
    return crud.create_patient_login(db, login)
@app.post("/auth/login")
def login_patient(username: str, password: str, db: Session = Depends(get_db)):
    login = crud.authenticate_patient(db, username, password)
    if not login:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "patient_id": login.patient_id}
@app.post("/appointments/", response_model=schemas.PatientAppointment)
def create_patient_appointment(appointment: schemas.PatientAppointmentCreate, db: Session = Depends(get_db)):
    return crud.create_patient_appointment(db, appointment)
@app.get("/appointments/patient/{patient_id}", response_model=List[schemas.PatientAppointment])
def read_patient_appointments(patient_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_patient_appointments(db, patient_id, status)
@app.patch("/appointments/{appointment_id}/status")
def update_appointment_status(appointment_id: str, status: str, db: Session = Depends(get_db)):
    return crud.update_appointment_status(db, appointment_id, status)
@app.post("/medical-records/", response_model=schemas.PatientMedicalRecord)
def create_patient_medical_record(record: schemas.PatientMedicalRecordCreate, db: Session = Depends(get_db)):
    return crud.create_patient_medical_record(db, record)
@app.get("/medical-records/patient/{patient_id}", response_model=List[schemas.PatientMedicalRecord])
def read_patient_medical_records(patient_id: int, record_type: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_patient_medical_records(db, patient_id, record_type)
@app.post("/feedback/", response_model=schemas.PatientFeedback)
def create_patient_feedback(feedback: schemas.PatientFeedbackCreate, db: Session = Depends(get_db)):
    return crud.create_patient_feedback(db, feedback)
@app.get("/feedback/patient/{patient_id}", response_model=List[schemas.PatientFeedback])
def read_patient_feedback(patient_id: int, service_type: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_patient_feedback(db, patient_id, service_type)
@app.post("/notifications/", response_model=schemas.PatientNotification)
def create_patient_notification(notification: schemas.PatientNotificationCreate, db: Session = Depends(get_db)):
    return crud.create_patient_notification(db, notification)
@app.get("/notifications/patient/{patient_id}", response_model=List[schemas.PatientNotification])
def read_patient_notifications(patient_id: int, is_read: Optional[bool] = None, db: Session = Depends(get_db)):
    return crud.get_patient_notifications(db, patient_id, is_read)
@app.patch("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str, db: Session = Depends(get_db)):
    return crud.mark_notification_read(db, notification_id)
@app.get("/dashboard/patient/{patient_id}", response_model=schemas.PatientDashboard)
def get_patient_dashboard(patient_id: int, db: Session = Depends(get_db)):
    dashboard = crud.get_patient_dashboard(db, patient_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return dashboard
@app.get("/statistics", response_model=schemas.PatientStatistics)
def get_patient_statistics(db: Session = Depends(get_db)):
    return crud.get_patient_statistics(db)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9010)