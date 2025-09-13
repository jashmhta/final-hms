import os
from typing import List, Optional

from core.auth.dependencies import get_current_user
from core.db.base import Base, TimestampMixin
from core.encryption.fields import EncryptedJSON, EncryptedString
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import Session

DATABASE_URL = os.getenv(
    "SERVICE_DATABASE_URL", "postgresql+psycopg2://hms:hms@db:5432/hms"
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


class Item(Base, TimestampMixin):
    __tablename__ = "service_items"
    id = Column(Integer, primary_key=True)
    name = Column(EncryptedString, nullable=False)
    description = Column(EncryptedString, nullable=True)
    active = Column(Boolean, default=True)


class ItemIn(BaseModel):
    name: str
    description: Optional[str] = None
    active: bool = True


class ItemOut(ItemIn):
    id: int

    class Config:
        from_attributes = True


app = FastAPI(title="Compliance Checklists Service", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/items", response_model=List[ItemOut])
def list_items(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    ensure_role(current_user, {"admin"})
    return db.query(Item).all()


@app.post("/api/items", response_model=ItemOut, status_code=201)
def create_item(
    payload: ItemIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_role(current_user, {"admin"})
    obj = Item(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
