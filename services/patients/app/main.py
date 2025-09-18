import os
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Date, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
DATABASE_URL = os.getenv(
    "PATIENTS_DATABASE_URL", "postgresql+psycopg2://hms:hms@db:5432/hms"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
class PatientModel(Base):
    __tablename__ = "patients_patient_ms"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    active = Column(Boolean, default=True)
class PatientIn(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = True
class PatientOut(PatientIn):
    id: int
    class Config:
        from_attributes = True
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
security = HTTPBearer()
def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    return {"user_id": 1, "role": "doctor", "hospital_id": 1}
app = FastAPI(
    title="Patients Service",
    version="1.0.0",
    description="Microservice for managing patient information in the HMS",
    openapi_tags=[
        {"name": "patients", "description": "Patient management operations"}
    ]
)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
@app.get("/api/patients", response_model=List[PatientOut], tags=["patients"])
def list_patients(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(PatientModel).all()
@app.post("/api/patients", response_model=PatientOut, status_code=201, tags=["patients"])
def create_patient(
    payload: PatientIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    obj = PatientModel(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
@app.get("/api/patients/{patient_id}", response_model=PatientOut, tags=["patients"])
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    obj = db.query(PatientModel).get(patient_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Patient not found")
    return obj
@app.put("/api/patients/{patient_id}", response_model=PatientOut, tags=["patients"])
def update_patient(
    patient_id: int,
    payload: PatientIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    obj = db.query(PatientModel).get(patient_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Patient not found")
    for k, v in payload.dict().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
@app.delete("/api/patients/{patient_id}", status_code=204, tags=["patients"])
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    obj = db.query(PatientModel).get(patient_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(obj)
    db.commit()
    return None