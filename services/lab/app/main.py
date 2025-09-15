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
    is_abnormal = Column(Boolean, default=False)
    reference_range = Column(String(100), nullable=True)
    automated_interpretation = Column(Text, nullable=True)
    order = relationship("LabOrderModel", back_populates="result")


class SpecimenModel(Base):
    __tablename__ = "lab_specimens"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("lab_laborder_ms.id"))
    specimen_type = Column(String(100), nullable=False)
    collection_time = Column(DateTime, default=datetime.utcnow)
    received_time = Column(DateTime, nullable=True)
    processed_time = Column(DateTime, nullable=True)
    status = Column(String(32), default="COLLECTED")
    barcode = Column(String(50), unique=True, nullable=True)


class QualityControlModel(Base):
    __tablename__ = "lab_quality_control"
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("lab_labtest_ms.id"))
    control_lot = Column(String(100), nullable=False)
    target_value = Column(String(50), nullable=False)
    tolerance = Column(String(50), nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow)
    result_value = Column(String(50), nullable=False)
    is_within_range = Column(Boolean, default=True)


class LISConfig(Base):
    __tablename__ = "lis_config"
    id = Column(Integer, primary_key=True)
    lis_url = Column(String(200), nullable=False)
    api_key = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True)


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
    is_abnormal: bool
    reference_range: Optional[str] = None
    automated_interpretation: Optional[str] = None

    class Config:
        from_attributes = True


class SpecimenIn(BaseModel):
    specimen_type: str
    barcode: Optional[str] = None


class SpecimenOut(BaseModel):
    id: int
    order_id: int
    specimen_type: str
    collection_time: datetime
    received_time: Optional[datetime] = None
    processed_time: Optional[datetime] = None
    status: str
    barcode: Optional[str] = None

    class Config:
        from_attributes = True


class QualityControlIn(BaseModel):
    test_id: int
    control_lot: str
    target_value: str
    tolerance: str
    result_value: str


class QualityControlOut(QualityControlIn):
    id: int
    performed_at: datetime
    is_within_range: bool

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

    # Automated interpretation
    interpretation = generate_automated_interpretation(payload.value, order.test.name)
    is_abnormal = check_abnormality(payload.value, order.test.name)

    result = LabResultModel(
        order=order,
        **payload.dict(),
        automated_interpretation=interpretation,
        is_abnormal=is_abnormal,
        reference_range=get_reference_range(order.test.name)
    )
    order.status = "COMPLETED"
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@app.post("/api/lab/specimens", response_model=SpecimenOut, status_code=201)
def create_specimen(order_id: int, payload: SpecimenIn, db: Session = Depends(get_db)):
    order = db.query(LabOrderModel).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    specimen = SpecimenModel(order_id=order_id, **payload.dict())
    db.add(specimen)
    db.commit()
    db.refresh(specimen)
    return specimen


@app.put("/api/lab/specimens/{specimen_id}/receive")
def receive_specimen(specimen_id: int, db: Session = Depends(get_db)):
    specimen = db.query(SpecimenModel).get(specimen_id)
    if not specimen:
        raise HTTPException(status_code=404, detail="Specimen not found")
    specimen.status = "RECEIVED"
    specimen.received_time = datetime.utcnow()
    db.commit()
    return {"status": "received"}


@app.post("/api/lab/quality_control", response_model=QualityControlOut, status_code=201)
def add_quality_control(payload: QualityControlIn, db: Session = Depends(get_db)):
    test = db.query(LabTestModel).get(payload.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Check if within range (simplified)
    is_within = abs(float(payload.result_value) - float(payload.target_value)) <= float(payload.tolerance)

    qc = QualityControlModel(
        test_id=payload.test_id,
        control_lot=payload.control_lot,
        target_value=payload.target_value,
        tolerance=payload.tolerance,
        result_value=payload.result_value,
        is_within_range=is_within
    )
    db.add(qc)
    db.commit()
    db.refresh(qc)
    return qc


@app.post("/api/lab/lis/sync")
def sync_with_lis(db: Session = Depends(get_db)):
    # Placeholder for LIS integration
    lis_config = db.query(LISConfig).filter(LISConfig.enabled == True).first()
    if not lis_config:
        raise HTTPException(status_code=500, detail="LIS not configured")

    # Simulate syncing orders/results with LIS
    return {"message": "LIS sync placeholder", "synced_orders": 0, "synced_results": 0}


def generate_automated_interpretation(value: str, test_name: str) -> str:
    # Placeholder for automated interpretation logic
    if test_name.lower().startswith("glucose"):
        val = float(value)
        if val < 70:
            return "Hypoglycemia detected"
        elif val > 140:
            return "Hyperglycemia detected"
    return "Within normal range"


def check_abnormality(value: str, test_name: str) -> bool:
    # Placeholder for abnormality check
    try:
        val = float(value)
        if test_name.lower().startswith("glucose"):
            return not (70 <= val <= 140)
    except ValueError:
        pass
    return False


def get_reference_range(test_name: str) -> str:
    # Placeholder for reference ranges
    if test_name.lower().startswith("glucose"):
        return "70-140 mg/dL"
    return "Not specified"
