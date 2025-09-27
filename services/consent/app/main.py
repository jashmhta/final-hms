"""
main module
"""

import os
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "CONSENT_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./consent.db")
)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
app = FastAPI(title="Consent Service", version="1.2.0")
Instrumentator().instrument(app).expose(app)


class TemplateModel(Base):
    __tablename__ = "consent_templates"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    body = Column(Text, nullable=False)


class SignatureModel(Base):
    __tablename__ = "consent_signatures"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, nullable=False)
    template_id = Column(Integer, nullable=False)
    signer_name = Column(String(100), nullable=False)
    signer_phone = Column(String(50), nullable=False)
    signed_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def create_tables():
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup():
    create_tables()
    db = SessionLocal()
    try:
        if db.query(TemplateModel).count() == 0:
            db.add(
                TemplateModel(
                    name="General Consent",
                    body="I hereby consent to diagnosis and treatment.",
                )
            )
            db.commit()
    finally:
        db.close()


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


class TemplateIn(BaseModel):
    name: str
    body: str


class TemplateOut(BaseModel):
    id: int
    name: str
    body: str

    class Config:
        from_attributes = True


class SignIn(BaseModel):
    patient_id: int
    template_id: int
    signer_name: str
    signer_phone: str


class Signature(BaseModel):
    id: int
    patient_id: int
    template_id: int
    signer_name: str
    signer_phone: str
    signed_at: datetime

    class Config:
        from_attributes = True


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/consent/templates", response_model=List[TemplateOut])
def list_templates(claims: dict = Depends(require_auth), db: Session = Depends(get_db)):
    ensure_role(
        claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"}
    )
    rows = db.query(TemplateModel).order_by(TemplateModel.id.asc()).all()
    return rows


@app.post("/api/consent/templates", response_model=TemplateOut)
def create_template(
    payload: TemplateIn,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN"})
    row = TemplateModel(name=payload.name, body=payload.body)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.post("/api/consent/sign", response_model=Signature)
def sign(
    payload: SignIn, claims: dict = Depends(require_auth), db: Session = Depends(get_db)
):
    ensure_role(
        claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"}
    )
    exists = (
        db.query(TemplateModel).filter(TemplateModel.id == payload.template_id).first()
    )
    if not exists:
        raise HTTPException(status_code=404, detail="Template not found")
    sig = SignatureModel(
        patient_id=payload.patient_id,
        template_id=payload.template_id,
        signer_name=payload.signer_name,
        signer_phone=payload.signer_phone,
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return sig


@app.get("/api/consent/signatures", response_model=List[Signature])
def list_signatures(
    claims: dict = Depends(require_auth), db: Session = Depends(get_db)
):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN"})
    rows = db.query(SignatureModel).order_by(SignatureModel.id.desc()).all()
    return rows
