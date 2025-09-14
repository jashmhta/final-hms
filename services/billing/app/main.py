import os
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv(
    "BILLING_DATABASE_URL", "postgresql+psycopg2://hms:hms@db:5432/hms"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class BillModel(Base):
    __tablename__ = "billing_bill_ms"
    id = Column(Integer, primary_key=True)
    patient = Column(Integer, nullable=False)
    total_cents = Column(Integer, default=0)
    paid_cents = Column(Integer, default=0)
    status = Column(String(16), default="DUE")
    items = relationship(
        "BillItemModel", back_populates="bill", cascade="all, delete-orphan"
    )
    payments = relationship(
        "PaymentModel", back_populates="bill", cascade="all, delete-orphan"
    )


class BillItemModel(Base):
    __tablename__ = "billing_billitem_ms"
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("billing_bill_ms.id"))
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price_cents = Column(Integer, default=0)
    amount_cents = Column(Integer, default=0)
    bill = relationship("BillModel", back_populates="items")


class PaymentModel(Base):
    __tablename__ = "billing_payment_ms"
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("billing_bill_ms.id"))
    amount_cents = Column(Integer, nullable=False)
    method = Column(String(32), default="CASH")
    bill = relationship("BillModel", back_populates="payments")


class BillItemIn(BaseModel):
    description: str
    quantity: int = 1
    unit_price_cents: int = 0


class BillIn(BaseModel):
    patient: int
    items: Optional[List[BillItemIn]] = []


class PaymentIn(BaseModel):
    amount_cents: int
    method: Optional[str] = "CASH"


class BillItemOut(BillItemIn):
    id: int
    amount_cents: int

    class Config:
        from_attributes = True


class PaymentOut(PaymentIn):
    id: int

    class Config:
        from_attributes = True


class BillOut(BaseModel):
    id: int
    patient: int
    total_cents: int
    paid_cents: int
    status: str
    items: List[BillItemOut]
    payments: List[PaymentOut]

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def recalc(bill: BillModel, insurance_coverage_percent=0, discount_percent=0):
    """Recalculate bill totals with insurance and discounts"""
    subtotal = sum(i.quantity * i.unit_price_cents for i in bill.items)
    insurance_discount = int(subtotal * insurance_coverage_percent / 100)
    additional_discount = int((subtotal - insurance_discount) * discount_percent / 100)
    bill.total_cents = subtotal - insurance_discount - additional_discount
    bill.paid_cents = sum(p.amount_cents for p in bill.payments)

    if bill.total_cents > 0 and bill.paid_cents >= bill.total_cents:
        bill.status = "PAID"
    elif bill.paid_cents > 0:
        bill.status = "PARTIAL"
    else:
        bill.status = "DUE"


app = FastAPI(title="Billing Service", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/billing/bills", response_model=List[BillOut])
def list_bills(db: Session = Depends(get_db)):
    return db.query(BillModel).all()


@app.post("/api/billing/bills", response_model=BillOut, status_code=201)
def create_bill(payload: BillIn, db: Session = Depends(get_db)):
    bill = BillModel(patient=payload.patient)
    db.add(bill)
    db.flush()
    for item in payload.items or []:
        db.add(
            BillItemModel(
                bill=bill,
                description=item.description,
                quantity=item.quantity,
                unit_price_cents=item.unit_price_cents,
                amount_cents=item.quantity * item.unit_price_cents,
            )
        )
    recalc(bill, insurance_coverage_percent=0, discount_percent=0)
    db.commit()
    db.refresh(bill)
    return bill


@app.post("/api/billing/bills/{bill_id}/insurance", response_model=BillOut)
def apply_insurance(
    bill_id: int, insurance_percent: int, db: Session = Depends(get_db)
):
    """Apply insurance coverage to bill"""
    bill = db.query(BillModel).get(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    recalc(bill, insurance_coverage_percent=insurance_percent)
    db.commit()
    db.refresh(bill)
    return bill


@app.post("/api/billing/bills/{bill_id}/discount", response_model=BillOut)
def apply_discount(bill_id: int, discount_percent: int, db: Session = Depends(get_db)):
    """Apply discount to bill"""
    bill = db.query(BillModel).get(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    recalc(bill, discount_percent=discount_percent)
    db.commit()
    db.refresh(bill)
    return bill


@app.post("/api/billing/bills/{bill_id}/payments", response_model=BillOut)
def add_payment(bill_id: int, payload: PaymentIn, db: Session = Depends(get_db)):
    bill = db.query(BillModel).get(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    db.add(
        PaymentModel(
            bill=bill, amount_cents=payload.amount_cents, method=payload.method
        )
    )
    recalc(bill, insurance_coverage_percent=0, discount_percent=0)
    db.commit()
    db.refresh(bill)
    return bill
