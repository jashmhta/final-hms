import json
import os
from datetime import datetime, time, timedelta
from typing import List, Optional
from abc import ABC, abstractmethod
import pika
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
DATABASE_URL = os.getenv(
    "APPOINTMENTS_DATABASE_URL", "postgresql+psycopg2://hms:hms@db:5432/hms"
)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
class AppointmentModel(Base):
    __tablename__ = "appointments_appointment_ms"
    id = Column(Integer, primary_key=True, index=True)
    patient = Column(Integer, nullable=False, index=True)
    doctor = Column(Integer, nullable=False, index=True)
    start_at = Column(DateTime, nullable=False, index=True)
    end_at = Column(DateTime, nullable=False)
    status = Column(String(16), nullable=False, default="SCHEDULED", index=True)
class EventModel(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    aggregate_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    event_data = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
class ConflictResolutionModel(Base):
    __tablename__ = "conflict_resolutions"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, nullable=False)
    conflict_type = Column(String(50), nullable=False)  
    resolution_action = Column(String(100), nullable=False)
    resolved_at = Column(DateTime, default=datetime.utcnow)
    resolved_by = Column(Integer, nullable=False)
class ChecklistModel(Base):
    __tablename__ = "checklists"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, nullable=False)
    checklist_type = Column(String(50), nullable=False)  
    items = Column(Text, nullable=False)  
    completed_items = Column(Text, nullable=True)  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
class AppointmentIn(BaseModel):
    patient: int
    doctor: int
    start_at: datetime
    end_at: datetime
    status: Optional[str] = "SCHEDULED"
class AppointmentOut(AppointmentIn):
    id: int
    class Config:
        from_attributes = True
class SlotOut(BaseModel):
    start_at: datetime
    end_at: datetime
class ConflictResolutionIn(BaseModel):
    appointment_id: int
    conflict_type: str
    resolution_action: str
    resolved_by: int
class ConflictResolutionOut(ConflictResolutionIn):
    id: int
    resolved_at: datetime
    class Config:
        from_attributes = True
class ChecklistIn(BaseModel):
    appointment_id: int
    checklist_type: str
    items: str  
class ChecklistOut(ChecklistIn):
    id: int
    completed_items: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class Command(ABC):
    @abstractmethod
    def execute(self, db: Session):
        pass
class Query(ABC):
    @abstractmethod
    def execute(self, db: Session):
        pass
class CreateAppointmentCommand(Command):
    def __init__(self, appointment_data: AppointmentIn):
        self.appointment_data = appointment_data
    def execute(self, db: Session):
        db_appointment = AppointmentModel(**self.appointment_data.dict())
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        event = EventModel(
            aggregate_id=db_appointment.id,
            event_type="AppointmentCreated",
            event_data=json.dumps(self.appointment_data.dict()),
        )
        db.add(event)
        db.commit()
        return db_appointment
class GetAppointmentsQuery(Query):
    def __init__(
        self, patient_id: Optional[int] = None, doctor_id: Optional[int] = None
    ):
        self.patient_id = patient_id
        self.doctor_id = doctor_id
    def execute(self, db: Session):
        query = db.query(AppointmentModel)
        if self.patient_id:
            query = query.filter(AppointmentModel.patient == self.patient_id)
        if self.doctor_id:
            query = query.filter(AppointmentModel.doctor == self.doctor_id)
        return query.all()
class UpdateAppointmentCommand(Command):
    def __init__(self, appointment_id: int, update_data: dict):
        self.appointment_id = appointment_id
        self.update_data = update_data
    def execute(self, db: Session):
        appointment = (
            db.query(AppointmentModel)
            .filter(AppointmentModel.id == self.appointment_id)
            .first()
        )
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        for key, value in self.update_data.items():
            setattr(appointment, key, value)
        db.commit()
        db.refresh(appointment)
        return appointment
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
app = FastAPI(title="Appointments Service", version="1.0.0")
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
@app.get("/api/appointments", response_model=List[AppointmentOut])
def list_appointments(
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = GetAppointmentsQuery(patient_id=patient_id, doctor_id=doctor_id)
    return query.execute(db)
@app.post("/api/appointments", response_model=AppointmentOut, status_code=201)
def create_appointment(payload: AppointmentIn, db: Session = Depends(get_db)):
    overlap = (
        db.query(AppointmentModel)
        .filter(
            AppointmentModel.doctor == payload.doctor,
            AppointmentModel.start_at < payload.end_at,
            AppointmentModel.end_at > payload.start_at,
            AppointmentModel.status.in_(
                ["SCHEDULED", "COMPLETED"]
            ),  
        )
        .first()
    )
    if overlap:
        raise HTTPException(
            status_code=400, detail="Overlapping appointment for this doctor"
        )
    command = CreateAppointmentCommand(payload)
    return command.execute(db)
@app.get("/api/appointments/available_slots", response_model=List[SlotOut])
def available_slots(
    doctor: int = Query(...),
    date: str = Query(...),
    slot_minutes: int = 30,
    db: Session = Depends(get_db),
):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date")
    start_t = time(9, 0)
    end_t = time(17, 0)
    start_dt = datetime.combine(target_date, start_t)
    end_dt = datetime.combine(target_date, end_t)
    existing = (
        db.query(AppointmentModel)
        .filter(
            AppointmentModel.doctor == doctor,
            AppointmentModel.start_at >= start_dt,
            AppointmentModel.end_at <= end_dt,
            AppointmentModel.status.in_(
                ["SCHEDULED", "COMPLETED"]
            ),  
        )
        .all()
    )
    slots: List[SlotOut] = []
    current = start_dt
    while current + timedelta(minutes=slot_minutes) <= end_dt:
        next_dt = current + timedelta(minutes=slot_minutes)
        overlap = False
        for a in existing:
            if a.start_at < next_dt and a.end_at > current:
                overlap = True
                break
        if not overlap and current > datetime.utcnow():
            slots.append(SlotOut(start_at=current, end_at=next_dt))
        current = next_dt
    return slots
def publish_event(routing_key: str, payload: dict):
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.exchange_declare(
            exchange="hms.events", exchange_type="topic", durable=True
        )
        channel.basic_publish(
            exchange="hms.events",
            routing_key=routing_key,
            body=json.dumps(payload).encode("utf-8"),
        )
        connection.close()
    except Exception:
        pass
@app.post("/api/appointments/{appointment_id}/complete", response_model=AppointmentOut)
def complete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = db.query(AppointmentModel).get(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = "COMPLETED"
    db.commit()
    db.refresh(appt)
    publish_event(
        "appointment.completed",
        {"appointment_id": appt.id, "patient": appt.patient, "doctor": appt.doctor},
    )
    return appt
@app.post("/api/appointments/conflict_resolution", response_model=ConflictResolutionOut, status_code=201)
def resolve_conflict(payload: ConflictResolutionIn, db: Session = Depends(get_db)):
    resolution = ConflictResolutionModel(**payload.dict())
    db.add(resolution)
    db.commit()
    db.refresh(resolution)
    return resolution
@app.get("/api/appointments/{appointment_id}/conflicts")
def get_conflicts(appointment_id: int, db: Session = Depends(get_db)):
    appt = db.query(AppointmentModel).get(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    overlaps = (
        db.query(AppointmentModel)
        .filter(
            AppointmentModel.doctor == appt.doctor,
            AppointmentModel.start_at < appt.end_at,
            AppointmentModel.end_at > appt.start_at,
            AppointmentModel.id != appointment_id,
            AppointmentModel.status.in_(["SCHEDULED", "COMPLETED"]),
        )
        .all()
    )
    return [{"id": o.id, "start_at": o.start_at, "end_at": o.end_at, "status": o.status} for o in overlaps]
@app.post("/api/appointments/checklists", response_model=ChecklistOut, status_code=201)
def create_checklist(payload: ChecklistIn, db: Session = Depends(get_db)):
    checklist = ChecklistModel(**payload.dict())
    db.add(checklist)
    db.commit()
    db.refresh(checklist)
    return checklist
@app.put("/api/appointments/checklists/{checklist_id}/complete")
def complete_checklist_item(checklist_id: int, item: str, db: Session = Depends(get_db)):
    checklist = db.query(ChecklistModel).get(checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    completed = checklist.completed_items or "[]"
    import json
    completed_list = json.loads(completed)
    if item not in completed_list:
        completed_list.append(item)
    checklist.completed_items = json.dumps(completed_list)
    checklist.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "item completed"}
@app.get("/api/appointments/{appointment_id}/checklists")
def get_checklists(appointment_id: int, db: Session = Depends(get_db)):
    checklists = db.query(ChecklistModel).filter(ChecklistModel.appointment_id == appointment_id).all()
    return [
        {
            "id": c.id,
            "checklist_type": c.checklist_type,
            "items": c.items,
            "completed_items": c.completed_items,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        }
        for c in checklists
    ]
@app.post("/api/appointments/{appointment_id}/sync_ehr")
def sync_with_ehr(appointment_id: int, db: Session = Depends(get_db)):
    return {"message": "EHR sync placeholder", "appointment_id": appointment_id}