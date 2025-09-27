"""
main module
"""

import os
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
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
    generic_name = Column(String(255), nullable=True)
    drug_class = Column(String(100), nullable=True)
    controlled_substance = Column(Boolean, default=False)
    dea_schedule = Column(String(10), nullable=True)


class DrugInteractionModel(Base):
    __tablename__ = "drug_interactions"
    id = Column(Integer, primary_key=True)
    drug1_id = Column(Integer, ForeignKey("pharmacy_medication_ms.id"))
    drug2_id = Column(Integer, ForeignKey("pharmacy_medication_ms.id"))
    interaction_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)


class DispensingModel(Base):
    __tablename__ = "pharmacy_dispensing"
    id = Column(Integer, primary_key=True)
    medication_id = Column(Integer, ForeignKey("pharmacy_medication_ms.id"))
    patient_id = Column(Integer, nullable=False)
    prescription_id = Column(Integer, nullable=True)
    quantity_dispensed = Column(Integer, nullable=False)
    dispensed_at = Column(DateTime, default=datetime.utcnow)
    dispensed_by = Column(Integer, nullable=False)
    instructions = Column(Text, nullable=True)


class CompoundingModel(Base):
    __tablename__ = "pharmacy_compounding"
    id = Column(Integer, primary_key=True)
    prescription_id = Column(Integer, nullable=False)
    ingredients = Column(Text, nullable=False)
    preparation_method = Column(Text, nullable=True)
    quantity_prepared = Column(String(50), nullable=False)
    prepared_at = Column(DateTime, default=datetime.utcnow)
    prepared_by = Column(Integer, nullable=False)
    expiration_date = Column(DateTime, nullable=True)
    quality_checked = Column(Boolean, default=False)


class MedicationIn(BaseModel):
    name: str
    strength: Optional[str] = None
    form: Optional[str] = None
    stock_quantity: int = 0
    min_stock_level: int = 0
    active: bool = True


class MedicationOut(MedicationIn):
    id: int
    generic_name: Optional[str] = None
    drug_class: Optional[str] = None
    controlled_substance: bool
    dea_schedule: Optional[str] = None

    class Config:
        from_attributes = True


class DrugInteractionIn(BaseModel):
    drug1_id: int
    drug2_id: int
    interaction_type: str
    description: str
    severity: str


class DrugInteractionOut(DrugInteractionIn):
    id: int

    class Config:
        from_attributes = True


class DispensingIn(BaseModel):
    medication_id: int
    patient_id: int
    prescription_id: Optional[int] = None
    quantity_dispensed: int
    dispensed_by: int
    instructions: Optional[str] = None


class DispensingOut(DispensingIn):
    id: int
    dispensed_at: datetime

    class Config:
        from_attributes = True


class CompoundingIn(BaseModel):
    prescription_id: int
    ingredients: str
    preparation_method: Optional[str] = None
    quantity_prepared: str
    prepared_by: int
    expiration_date: Optional[datetime] = None


class CompoundingOut(CompoundingIn):
    id: int
    prepared_at: datetime
    quality_checked: bool

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


@app.post(
    "/api/pharmacy/drug_interactions",
    response_model=DrugInteractionOut,
    status_code=201,
)
def create_drug_interaction(payload: DrugInteractionIn, db: Session = Depends(get_db)):
    drug1 = db.query(MedicationModel).get(payload.drug1_id)
    drug2 = db.query(MedicationModel).get(payload.drug2_id)
    if not drug1 or not drug2:
        raise HTTPException(status_code=404, detail="Medication not found")
    interaction = DrugInteractionModel(**payload.dict())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@app.get("/api/pharmacy/drug_interactions/{drug_id}")
def check_interactions(drug_id: int, db: Session = Depends(get_db)):
    interactions = (
        db.query(DrugInteractionModel)
        .filter(
            (DrugInteractionModel.drug1_id == drug_id)
            | (DrugInteractionModel.drug2_id == drug_id)
        )
        .all()
    )
    return [
        {
            "id": i.id,
            "drug1_id": i.drug1_id,
            "drug2_id": i.drug2_id,
            "interaction_type": i.interaction_type,
            "description": i.description,
            "severity": i.severity,
        }
        for i in interactions
    ]


@app.post("/api/pharmacy/dispensing", response_model=DispensingOut, status_code=201)
def dispense_medication(payload: DispensingIn, db: Session = Depends(get_db)):
    medication = db.query(MedicationModel).get(payload.medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    if medication.stock_quantity < payload.quantity_dispensed:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    if payload.prescription_id:
        interactions = check_interactions_for_prescription(payload.prescription_id, db)
        if interactions:
            return {
                "warning": "Potential drug interactions detected",
                "interactions": interactions,
            }
    dispensing = DispensingModel(**payload.dict())
    medication.stock_quantity -= payload.quantity_dispensed
    db.add(dispensing)
    db.commit()
    db.refresh(dispensing)
    return dispensing


@app.post("/api/pharmacy/compounding", response_model=CompoundingOut, status_code=201)
def create_compounding(payload: CompoundingIn, db: Session = Depends(get_db)):
    compounding = CompoundingModel(**payload.dict())
    db.add(compounding)
    db.commit()
    db.refresh(compounding)
    return compounding


@app.put("/api/pharmacy/compounding/{compounding_id}/quality_check")
def quality_check_compounding(compounding_id: int, db: Session = Depends(get_db)):
    compounding = db.query(CompoundingModel).get(compounding_id)
    if not compounding:
        raise HTTPException(status_code=404, detail="Compounding record not found")
    compounding.quality_checked = True
    db.commit()
    return {"status": "quality checked"}


@app.get("/api/pharmacy/controlled_substances")
def get_controlled_substances(db: Session = Depends(get_db)):
    return (
        db.query(MedicationModel)
        .filter(MedicationModel.controlled_substance == True)
        .all()
    )


def check_interactions_for_prescription(prescription_id: int, db: Session) -> list:
    return []
