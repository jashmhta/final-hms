import os
from datetime import datetime
from typing import List, Optional

import requests
from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile, File
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, create_engine
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
    findings = Column(Text, nullable=True)
    critical_findings = Column(Boolean, default=False)
    template_used = Column(String(100), nullable=True)


class ImageModel(Base):
    __tablename__ = "radiology_images"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, index=True, nullable=False)
    dicom_uid = Column(String(100), unique=True, nullable=False)
    image_path = Column(String(500), nullable=False)
    modality = Column(String(50), nullable=False)
    body_part = Column(String(100), nullable=True)
    series_description = Column(String(200), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class PACSConfig(Base):
    __tablename__ = "pacs_config"
    id = Column(Integer, primary_key=True)
    pacs_url = Column(String(200), nullable=False)
    pacs_ae_title = Column(String(50), nullable=False)
    local_ae_title = Column(String(50), nullable=False)
    enabled = Column(Boolean, default=True)


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
    findings: Optional[str] = None
    critical_findings: bool = False
    template_used: Optional[str] = None


class RadiologyImage(BaseModel):
    order_id: int
    dicom_uid: str
    modality: str
    body_part: Optional[str] = None
    series_description: Optional[str] = None


class PACSConfigModel(BaseModel):
    pacs_url: str
    pacs_ae_title: str
    local_ae_title: str
    enabled: bool = True


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
    rep = ReportModel(
        order_id=payload.order_id,
        impression=payload.impression,
        findings=payload.findings,
        critical_findings=payload.critical_findings,
        template_used=payload.template_used
    )
    db.merge(rep)
    db.commit()
    # Send critical findings alert if needed
    if payload.critical_findings:
        send_critical_alert(payload.order_id, db)
    return {"status": "stored"}


@app.post("/api/radiology/upload_dicom")
def upload_dicom(
    order_id: int,
    file: UploadFile = File(...),
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")
    exists = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Order not found")

    # Save file (simplified - in real implementation, use proper DICOM parsing)
    file_path = f"/storage/dicom/{order_id}/{file.filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Extract DICOM metadata (placeholder)
    dicom_uid = f"1.2.3.{order_id}.{int(datetime.utcnow().timestamp())}"
    image = ImageModel(
        order_id=order_id,
        dicom_uid=dicom_uid,
        image_path=file_path,
        modality="CT",  # Extract from DICOM
        body_part="HEAD",  # Extract from DICOM
        series_description="CT Head"
    )
    db.add(image)
    db.commit()
    return {"dicom_uid": dicom_uid, "status": "uploaded"}


@app.get("/api/radiology/images/{order_id}")
def get_images(order_id: int, claims: dict = Depends(require_auth), db: Session = Depends(get_db)):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH", "NURSE"})
    ensure_module_enabled(claims, "enable_diagnostics")
    images = db.query(ImageModel).filter(ImageModel.order_id == order_id).all()
    return [
        {
            "id": img.id,
            "dicom_uid": img.dicom_uid,
            "modality": img.modality,
            "body_part": img.body_part,
            "series_description": img.series_description,
            "uploaded_at": img.uploaded_at
        }
        for img in images
    ]


@app.post("/api/radiology/pacs/query")
def pacs_query(
    patient_id: int,
    study_date: str,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")
    # Placeholder for PACS C-FIND query
    pacs_config = db.query(PACSConfig).filter(PACSConfig.enabled == True).first()
    if not pacs_config:
        raise HTTPException(status_code=500, detail="PACS not configured")

    # Simulate PACS query
    return {"studies": [], "message": "PACS integration placeholder"}


def send_critical_alert(order_id: int, db: Session):
    # Placeholder for sending critical findings alert
    # Could integrate with notifications service
    pass


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
