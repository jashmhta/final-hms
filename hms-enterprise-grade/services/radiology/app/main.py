import os
from typing import List

import requests
from fastapi import Depends, FastAPI, Header, HTTPException
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "RADIOLOGY_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./radiology.db")
)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

app = FastAPI(title="Radiology Service", version="1.2.0")
Instrumentator().instrument(app).expose(app)


class OrderModel(Base):
    __tablename__ = "radiology_orders"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True, nullable=False)
    study_type = Column(String(100), nullable=False)
    priority = Column(String(20), default="ROUTINE")


class ReportModel(Base):
    __tablename__ = "radiology_reports"
    order_id = Column(Integer, primary_key=True)
    impression = Column(Text, nullable=False)


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


class RadiologyOrder(BaseModel):
    patient_id: int
    study_type: str
    priority: str = "ROUTINE"  # or STAT


class RadiologyReport(BaseModel):
    order_id: int
    impression: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/radiology/orders")
def create_order(
    payload: RadiologyOrder,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "RECEPTIONIST"})
    ensure_module_enabled(claims, "enable_diagnostics")
    row = OrderModel(
        patient_id=payload.patient_id,
        study_type=payload.study_type,
        priority=payload.priority,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "patient_id": row.patient_id,
        "study_type": row.study_type,
        "priority": row.priority,
    }


@app.get("/api/radiology/orders")
def list_orders(claims: dict = Depends(require_auth), db: Session = Depends(get_db)):
    ensure_role(
        claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH", "NURSE"}
    )
    ensure_module_enabled(claims, "enable_diagnostics")
    rows = db.query(OrderModel).order_by(OrderModel.id.desc()).all()
    return [
        {
            "id": r.id,
            "patient_id": r.patient_id,
            "study_type": r.study_type,
            "priority": r.priority,
        }
        for r in rows
    ]


@app.post("/api/radiology/report")
def submit_report(
    payload: RadiologyReport,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")
    exists = db.query(OrderModel).filter(OrderModel.id == payload.order_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Order not found")
    rep = ReportModel(order_id=payload.order_id, impression=payload.impression)
    db.merge(rep)
    db.commit()
    return {"status": "stored"}


@app.get("/api/radiology/kpi")
def kpi(claims: dict = Depends(require_auth), db: Session = Depends(get_db)):
    ensure_module_enabled(claims, "enable_diagnostics")
    opa = os.getenv("OPA_URL")
    if opa:
        try:
            d = requests.post(
                f"{opa}/v1/data/hms/allow",
                json={"input": {"path": "/api/radiology/kpi"}},
                timeout=2,
            )
            if d.ok and d.json().get("result") is False:
                raise HTTPException(status_code=403, detail="Policy denied")
        except Exception:
            pass
    total = db.query(OrderModel).count()
    stat = db.query(OrderModel).filter(OrderModel.priority == "STAT").count()
    return {"orders": int(total), "stat": int(stat)}
