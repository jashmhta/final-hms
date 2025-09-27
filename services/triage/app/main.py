"""
main module
"""

import os
from datetime import datetime, timezone

import requests
from fastapi import Depends, FastAPI, Header, HTTPException
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

app = FastAPI(title="Triage Service", version="1.2.0")
Instrumentator().instrument(app).expose(app)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
DATABASE_URL = os.getenv(
    "TRIAGE_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./triage.db")
)
OPA_URL = os.getenv("OPA_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class TriageInput(BaseModel):
    age: int
    heart_rate: int
    systolic_bp: int
    spo2: int
    temperature_c: float


class TriageResult(BaseModel):
    score: int
    priority: str


class TriageRecord(Base):
    __tablename__ = "triage_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id = Column(Integer, index=True)
    age = Column(Integer)
    heart_rate = Column(Integer)
    systolic_bp = Column(Integer)
    spo2 = Column(Integer)
    temperature_c = Column(Integer)
    score = Column(Integer)
    priority = Column(String)
    created_at = Column(DateTime, default=datetime.now(tz=timezone.utc))


def require_auth(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def ensure_module_enabled(claims: dict, flag: str):
    if claims is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    enabled = claims.get(flag, True)
    if not enabled:
        raise HTTPException(status_code=403, detail=f"Module disabled: {flag}")


@app.get("/health")
def health():
    return {"status": "ok"}


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/api/triage/score", response_model=TriageResult)
def score(
    payload: TriageInput,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_module_enabled(claims, "enable_opd")
    if OPA_URL:
        try:
            decision = requests.post(
                f"{OPA_URL}/v1/data/hms/allow",
                json={
                    "input": {"role": claims.get("role"), "path": "/api/triage/score"}
                },
                timeout=2,
            )
            if decision.ok and decision.json().get("result") is False:
                raise HTTPException(status_code=403, detail="Policy denied")
        except Exception:
            pass
    score = 0
    if payload.heart_rate > 120 or payload.heart_rate < 40:
        score += 2
    if payload.systolic_bp < 90:
        score += 3
    if payload.spo2 < 92:
        score += 3
    if payload.temperature_c > 38.5 or payload.temperature_c < 35:
        score += 2
    if payload.age > 75:
        score += 1
    priority = "LOW"
    if score >= 6:
        priority = "CRITICAL"
    elif score >= 3:
        priority = "HIGH"
    try:
        hospital_id = int(claims.get("hospital") or 0)
    except Exception:
        hospital_id = 0
    rec = TriageRecord(
        hospital_id=hospital_id,
        age=payload.age,
        heart_rate=payload.heart_rate,
        systolic_bp=payload.systolic_bp,
        spo2=payload.spo2,
        temperature_c=int(payload.temperature_c),
        score=score,
        priority=priority,
    )
    db.add(rec)
    db.commit()
    return TriageResult(score=score, priority=priority)
