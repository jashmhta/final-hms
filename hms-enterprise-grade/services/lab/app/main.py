import os
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv(
    "LAB_DATABASE_URL", "postgresql+psycopg2://hms:hms@db:5432/hms"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class LabTestModel(Base):
    __tablename__ = "lab_labtest_ms"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    price_cents = Column(Integer, default=0)


class LabOrderModel(Base):
    __tablename__ = "lab_laborder_ms"
    id = Column(Integer, primary_key=True)
    patient = Column(Integer, nullable=False)
    doctor = Column(Integer, nullable=False)
    test_id = Column(Integer, ForeignKey("lab_labtest_ms.id"))
    ordered_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="PENDING")
    test = relationship("LabTestModel")
    result = relationship("LabResultModel", uselist=False, back_populates="order")


class LabResultModel(Base):
    __tablename__ = "lab_labresult_ms"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("lab_laborder_ms.id"))
    value = Column(String(255), nullable=False)
    unit = Column(String(64), nullable=True)
    observations = Column(String(255), nullable=True)
    reported_at = Column(DateTime, default=datetime.utcnow)
    order = relationship("LabOrderModel", back_populates="result")


class LabTestIn(BaseModel):
    name: str
    description: Optional[str] = None
    price_cents: int = 0


class LabTestOut(LabTestIn):
    id: int

    class Config:
        from_attributes = True


class LabOrderIn(BaseModel):
    patient: int
    doctor: int
    test_id: int


class LabOrderOut(BaseModel):
    id: int
    patient: int
    doctor: int
    test_id: int
    ordered_at: datetime
    status: str

    class Config:
        from_attributes = True


class LabResultIn(BaseModel):
    value: str
    unit: Optional[str] = None
    observations: Optional[str] = None


class LabResultOut(LabResultIn):
    id: int
    reported_at: datetime

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Lab Service", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/lab/tests", response_model=List[LabTestOut])
def list_tests(db: Session = Depends(get_db)):
    return db.query(LabTestModel).all()


@app.post("/api/lab/tests", response_model=LabTestOut, status_code=201)
def create_test(payload: LabTestIn, db: Session = Depends(get_db)):
    obj = LabTestModel(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.post("/api/lab/orders", response_model=LabOrderOut, status_code=201)
def create_order(payload: LabOrderIn, db: Session = Depends(get_db)):
    test = db.query(LabTestModel).get(payload.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    order = LabOrderModel(patient=payload.patient, doctor=payload.doctor, test=test)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@app.get("/api/lab/orders", response_model=List[LabOrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.query(LabOrderModel).all()


@app.post("/api/lab/orders/{order_id}/result", response_model=LabResultOut)
def add_result(order_id: int, payload: LabResultIn, db: Session = Depends(get_db)):
    order = db.query(LabOrderModel).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.result:
        raise HTTPException(status_code=400, detail="Result already exists")
    result = LabResultModel(order=order, **payload.dict())
    order.status = "COMPLETED"
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
