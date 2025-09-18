import os
from datetime import datetime
from typing import List
from fastapi import Depends, FastAPI, Header, HTTPException
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
DATABASE_URL = os.getenv(
    "FEEDBACK_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./feedback.db")
)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
app = FastAPI(title="Feedback Service", version="1.2.0")
Instrumentator().instrument(app).expose(app)
class FeedbackModel(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, nullable=False, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
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
class FeedbackIn(BaseModel):
    hospital_id: int
    patient_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = ""
class Feedback(BaseModel):
    id: int
    hospital_id: int
    patient_id: int
    rating: int
    comment: str
    created_at: datetime
    class Config:
        from_attributes = True
@app.get("/health")
def health():
    return {"status": "ok"}
@app.get("/api/feedback/", response_model=List[Feedback])
def list_feedback(claims: dict = Depends(require_auth), db: Session = Depends(get_db)):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN"})
    rows = db.query(FeedbackModel).order_by(FeedbackModel.id.desc()).all()
    return rows
@app.post("/api/feedback/", response_model=Feedback)
def submit_feedback(
    payload: FeedbackIn,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(
        claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "RECEPTIONIST", "NURSE", "DOCTOR"}
    )
    row = FeedbackModel(
        hospital_id=payload.hospital_id,
        patient_id=payload.patient_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row