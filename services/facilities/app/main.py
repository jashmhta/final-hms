"""
main module
"""

import os
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv(
    "FACILITIES_DATABASE_URL", "postgresql+psycopg2://hms:hms@db:5432/hms"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class WardModel(Base):
    __tablename__ = "fac_ward_ms"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    floor = Column(String(32), nullable=True)
    beds = relationship("BedModel", back_populates="ward", cascade="all, delete-orphan")


class BedModel(Base):
    __tablename__ = "fac_bed_ms"
    id = Column(Integer, primary_key=True)
    ward_id = Column(Integer, ForeignKey("fac_ward_ms.id"))
    number = Column(String(32), nullable=False)
    is_occupied = Column(Boolean, default=False)
    occupant = Column(Integer, nullable=True)
    ward = relationship("WardModel", back_populates="beds")


class WardIn(BaseModel):
    name: str
    floor: Optional[str] = None


class WardOut(WardIn):
    id: int

    class Config:
        from_attributes = True


class BedIn(BaseModel):
    ward_id: int
    number: str


class BedOut(BaseModel):
    id: int
    ward_id: int
    number: str
    is_occupied: bool
    occupant: Optional[int]

    class Config:
        from_attributes = True


class AssignIn(BaseModel):
    patient: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Facilities Service", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/facilities/wards", response_model=List[WardOut])
def list_wards(db: Session = Depends(get_db)):
    return db.query(WardModel).all()


@app.post("/api/facilities/wards", response_model=WardOut, status_code=201)
def create_ward(payload: WardIn, db: Session = Depends(get_db)):
    obj = WardModel(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/api/facilities/beds", response_model=List[BedOut])
def list_beds(db: Session = Depends(get_db)):
    return db.query(BedModel).all()


@app.post("/api/facilities/beds", response_model=BedOut, status_code=201)
def create_bed(payload: BedIn, db: Session = Depends(get_db)):
    ward = db.query(WardModel).get(payload.ward_id)
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    obj = BedModel(ward_id=payload.ward_id, number=payload.number)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.post("/api/facilities/beds/{bed_id}/assign", response_model=BedOut)
def assign_bed(bed_id: int, payload: AssignIn, db: Session = Depends(get_db)):
    bed = db.query(BedModel).get(bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if bed.is_occupied:
        raise HTTPException(status_code=400, detail="Bed already occupied")
    bed.is_occupied = True
    bed.occupant = payload.patient
    db.commit()
    db.refresh(bed)
    return bed


@app.post("/api/facilities/beds/{bed_id}/release", response_model=BedOut)
def release_bed(bed_id: int, db: Session = Depends(get_db)):
    bed = db.query(BedModel).get(bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    bed.is_occupied = False
    bed.occupant = None
    db.commit()
    db.refresh(bed)
    return bed
