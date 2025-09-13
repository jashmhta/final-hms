import json
import os
from datetime import datetime, time, timedelta
from typing import List, Optional

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
    patient = Column(Integer, nullable=False)
    doctor = Column(Integer, nullable=False)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    status = Column(String(16), nullable=False, default="SCHEDULED")


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
def list_appointments(db: Session = Depends(get_db)):
    return db.query(AppointmentModel).all()


@app.post("/api/appointments", response_model=AppointmentOut, status_code=201)
def create_appointment(payload: AppointmentIn, db: Session = Depends(get_db)):
    # Basic overlap validation per doctor
    overlap = (
        db.query(AppointmentModel)
        .filter(
            AppointmentModel.doctor == payload.doctor,
            AppointmentModel.start_at < payload.end_at,
            AppointmentModel.end_at > payload.start_at,
            AppointmentModel.status.in_(
                ["SCHEDULED", "COMPLETED"]
            ),  # consider only active slots
        )
        .first()
    )
    if overlap:
        raise HTTPException(
            status_code=400, detail="Overlapping appointment for this doctor"
        )
    obj = AppointmentModel(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


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
            ),  # consider only active slots
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
        # fail silent to not break request
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
