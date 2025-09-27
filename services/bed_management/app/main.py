"""
main module
"""

import os
from typing import Dict

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "BED_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./bed.db")
)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
app = FastAPI(title="Bed Management Service", version="1.2.0")
Instrumentator().instrument(app).expose(app)


class BedStat(Base):
    __tablename__ = "bed_stats"
    hospital_id = Column(String, primary_key=True)
    total = Column(Integer, default=100)
    available = Column(Integer, default=90)
    occupied = Column(Integer, default=10)


def create_tables():
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup():
    create_tables()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_auth(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def ensure_role(claims: dict, allowed: set[str]):
    role = claims.get("role")
    if role not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden")


def ensure_module_enabled(claims: dict, flag: str):
    if claims is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    enabled = claims.get(flag, True)
    if not enabled:
        raise HTTPException(status_code=403, detail=f"Module disabled: {flag}")


class AssignPayload(BaseModel):
    patient_id: str
    bed_id: str
    hospital_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/bed/availability")
def availability(
    hospital_id: str = Query(...),
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(
        claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "NURSE", "RECEPTIONIST", "DOCTOR"}
    )
    ensure_module_enabled(claims, "enable_ipd")
    data = db.query(BedStat).filter(BedStat.hospital_id == hospital_id).first()
    if not data:
        data = BedStat(hospital_id=hospital_id)
        db.add(data)
        db.commit()
        db.refresh(data)
    return {"total": data.total, "available": data.available, "occupied": data.occupied}


@app.post("/api/bed/assign")
def assign(
    payload: AssignPayload,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "NURSE", "RECEPTIONIST"})
    ensure_module_enabled(claims, "enable_ipd")
    data = db.query(BedStat).filter(BedStat.hospital_id == payload.hospital_id).first()
    if not data:
        data = BedStat(hospital_id=payload.hospital_id)
    if data.available <= 0:
        raise HTTPException(status_code=400, detail="No available beds")
    data.available -= 1
    data.occupied += 1
    db.merge(data)
    db.commit()
    return {
        "status": "assigned",
        "bed_id": payload.bed_id,
        "patient_id": payload.patient_id,
    }


@app.get("/api/bed/kpi")
def kpi(
    hospital_id: str = Query(...),
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(
        claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "NURSE", "RECEPTIONIST", "DOCTOR"}
    )
    ensure_module_enabled(claims, "enable_ipd")
    data = db.query(BedStat).filter(BedStat.hospital_id == hospital_id).first()
    if not data:
        data = BedStat(hospital_id=hospital_id)
        db.add(data)
        db.commit()
        db.refresh(data)
    occupancy_rate = (data.occupied / data.total) if data.total else 0.0
    return {
        "total": data.total,
        "available": data.available,
        "occupied": data.occupied,
        "occupancy_rate": occupancy_rate,
    }
