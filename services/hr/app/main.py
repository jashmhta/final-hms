import os
from typing import List, Optional
from fastapi import Depends, FastAPI, Header, HTTPException
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import Column, Date, ForeignKey, Integer, String, Time, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
DATABASE_URL = os.getenv("HR_DATABASE_URL", "postgresql+psycopg2://hms:hms@db:5432/hms")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
class ShiftModel(Base):
    __tablename__ = "hr_shift_ms"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    start_time = Column(String(8), nullable=False)  
    end_time = Column(String(8), nullable=False)
class DutyRosterModel(Base):
    __tablename__ = "hr_dutyroster_ms"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    shift_id = Column(Integer, ForeignKey("hr_shift_ms.id"))
    shift = relationship("ShiftModel")
class LeaveRequestModel(Base):
    __tablename__ = "hr_leaverequest_ms"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=True)
    status = Column(String(16), default="PENDING")
class ShiftIn(BaseModel):
    name: str
    start_time: str
    end_time: str
class ShiftOut(ShiftIn):
    id: int
    class Config:
        from_attributes = True
class DutyRosterIn(BaseModel):
    user: int
    date: str
    shift_id: int
class DutyRosterOut(BaseModel):
    id: int
    user: int
    date: str
    shift_id: int
    class Config:
        from_attributes = True
class LeaveRequestIn(BaseModel):
    user: int
    start_date: str
    end_date: str
    reason: Optional[str] = None
class LeaveRequestOut(BaseModel):
    id: int
    user: int
    start_date: str
    end_date: str
    reason: Optional[str]
    status: str
    class Config:
        from_attributes = True
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
app = FastAPI(title="HR Service", version="1.1.0")
Instrumentator().instrument(app).expose(app)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
def require_auth(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
@app.get("/health")
def health():
    return {"status": "ok"}
@app.get("/api/hr/shifts", response_model=List[ShiftOut])
def list_shifts(_: dict = Depends(require_auth), db: Session = Depends(get_db)):
    return db.query(ShiftModel).all()
@app.post("/api/hr/shifts", response_model=ShiftOut, status_code=201)
def create_shift(
    payload: ShiftIn, _: dict = Depends(require_auth), db: Session = Depends(get_db)
):
    obj = ShiftModel(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
@app.get("/api/hr/roster", response_model=List[DutyRosterOut])
def list_roster(_: dict = Depends(require_auth), db: Session = Depends(get_db)):
    return db.query(DutyRosterModel).all()
@app.post("/api/hr/roster", response_model=DutyRosterOut, status_code=201)
def create_roster(
    payload: DutyRosterIn,
    _: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    obj = DutyRosterModel(
        user=payload.user, date=payload.date, shift_id=payload.shift_id
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
@app.get("/api/hr/leaves", response_model=List[LeaveRequestOut])
def list_leaves(_: dict = Depends(require_auth), db: Session = Depends(get_db)):
    return db.query(LeaveRequestModel).all()
@app.post("/api/hr/leaves", response_model=LeaveRequestOut, status_code=201)
def create_leave(
    payload: LeaveRequestIn,
    _: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    obj = LeaveRequestModel(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
class AutoRosterIn(BaseModel):
    users: List[int]
    start_date: str
    end_date: str
    shift_id: int
@app.post("/api/hr/roster/auto-generate", response_model=List[DutyRosterOut])
def auto_generate(
    payload: AutoRosterIn,
    _: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    from datetime import datetime, timedelta
    start = datetime.fromisoformat(payload.start_date).date()
    end = datetime.fromisoformat(payload.end_date).date()
    if end < start:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    created = []
    day = start
    user_idx = 0
    while day <= end:
        uid = payload.users[user_idx % len(payload.users)]
        obj = DutyRosterModel(user=uid, date=day, shift_id=payload.shift_id)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        created.append(obj)
        user_idx += 1
        day = day + timedelta(days=1)
    return created