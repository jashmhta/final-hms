import os
from typing import List, Optional
from core.auth.dependencies import get_current_user
from core.db.base import Base, TimestampMixin
from core.encryption.fields import EncryptedJSON, EncryptedString
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Session, relationship
DATABASE_URL = os.getenv(
    "HOUSEKEEPING_MAINTENANCE_DATABASE_URL", "postgresql+psycopg2://hms:hms@db:5432/hms"
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def ensure_role(claims: dict, allowed: set[str]):
    role = claims.get("role")
    if role not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden")
class HousekeepingTask(Base, TimestampMixin):
    __tablename__ = "housekeeping_tasks"
    id = Column(Integer, primary_key=True)
    room_number = Column(String(50), nullable=False, index=True)
    description = Column(EncryptedString, nullable=False)
    status = Column(String(50), default="pending", index=True)
    assigned_to = Column(String(100), nullable=True)
    priority = Column(String(50), default="normal")
    notes = Column(EncryptedText := EncryptedString, nullable=True)
class HousekeepingTaskIn(BaseModel):
    room_number: str
    description: str
    status: Optional[str] = "pending"
    assigned_to: Optional[str] = None
    priority: Optional[str] = "normal"
    notes: Optional[str] = None
class HousekeepingTaskOut(HousekeepingTaskIn):
    id: int
    class Config:
        from_attributes = True
app = FastAPI(title="Housekeeping Maintenance Service", version="1.0.0")
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
@app.get("/api/housekeeping/tasks", response_model=List[HousekeepingTaskOut])
def list_tasks(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    ensure_role(current_user, {"admin", "housekeeping_manager"})
    return db.query(HousekeepingTask).all()
@app.post(
    "/api/housekeeping/tasks", response_model=HousekeepingTaskOut, status_code=201
)
def create_task(
    payload: HousekeepingTaskIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_role(current_user, {"admin", "housekeeping_manager"})
    obj = HousekeepingTask(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
@app.put("/api/housekeeping/tasks/{task_id}", response_model=HousekeepingTaskOut)
def update_task(
    task_id: int,
    payload: HousekeepingTaskIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_role(current_user, {"admin", "housekeeping_manager"})
    obj = db.query(HousekeepingTask).get(task_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj
@app.delete("/api/housekeeping/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_role(current_user, {"admin"})
    obj = db.query(HousekeepingTask).get(task_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(obj)
    db.commit()
    return None