import os
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "PHARMACY_DATABASE_URL", "postgresql+psycopg2://hms:hms@db:5432/hms"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class MedicationModel(Base):
    __tablename__ = "pharmacy_medication_ms"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    strength = Column(String(100), nullable=True)
    form = Column(String(100), nullable=True)
    stock_quantity = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=0)
    active = Column(Boolean, default=True)


class MedicationIn(BaseModel):
    name: str
    strength: Optional[str] = None
    form: Optional[str] = None
    stock_quantity: int = 0
    min_stock_level: int = 0
    active: bool = True


class MedicationOut(MedicationIn):
    id: int

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Pharmacy Service", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/pharmacy/medications", response_model=List[MedicationOut])
def list_medications(db: Session = Depends(get_db)):
    return db.query(MedicationModel).all()


@app.post("/api/pharmacy/medications", response_model=MedicationOut, status_code=201)
def create_medication(payload: MedicationIn, db: Session = Depends(get_db)):
    obj = MedicationModel(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/api/pharmacy/medications/low_stock", response_model=List[MedicationOut])
def low_stock(db: Session = Depends(get_db)):
    return (
        db.query(MedicationModel)
        .filter(MedicationModel.stock_quantity < MedicationModel.min_stock_level)
        .all()
    )
