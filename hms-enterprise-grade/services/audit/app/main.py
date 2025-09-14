import base64
import os
from datetime import datetime
from typing import List, Optional

import redis.asyncio as aioredis
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "AUDIT_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./audit.db")
)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
SERVICE_SHARED_KEY = os.getenv("SERVICE_SHARED_KEY", None)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")
AUDIT_PRIVATE_KEY_PATH = os.getenv("AUDIT_PRIVATE_KEY_PATH", None)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

app = FastAPI(title="Audit Service", version="1.2.0")
Instrumentator().instrument(app).expose(app)


class AuditEventModel(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True)
    service = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    detail = Column(Text, nullable=True)
    actor_user = Column(String(100), nullable=True)
    actor_role = Column(String(50), nullable=True)
    actor_hospital = Column(Integer, nullable=True)
    ip = Column(String(64), nullable=True)
    request_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def create_tables():
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
async def on_startup():
    create_tables()
    try:
        redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis)
    except Exception:
        pass


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_auth(
    authorization: str | None = Header(None), x_service_key: str | None = Header(None)
):
    # Allow shared key for service-to-service
    if SERVICE_SHARED_KEY and x_service_key == SERVICE_SHARED_KEY:
        return {"role": "SUPER_ADMIN", "svc": "backend"}
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


class AuditEventIn(BaseModel):
    service: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    detail: Optional[str] = None
    encrypted: Optional[bool] = False
    ciphertext_b64: Optional[str] = None


class AuditEventOut(BaseModel):
    id: int
    service: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    detail: Optional[str]
    actor_user: Optional[str]
    actor_role: Optional[str]
    actor_hospital: Optional[int]
    ip: Optional[str]
    request_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/api/audit/events",
    response_model=AuditEventOut,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
def create_event(
    payload: AuditEventIn,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
    x_real_ip: str | None = Header(None),
    x_request_id: str | None = Header(None),
):
    if payload.encrypted:
        if not AUDIT_PRIVATE_KEY_PATH or not os.path.exists(AUDIT_PRIVATE_KEY_PATH):
            raise HTTPException(status_code=400, detail="No private key configured")
        if not payload.ciphertext_b64:
            raise HTTPException(status_code=400, detail="Missing ciphertext")
        with open(AUDIT_PRIVATE_KEY_PATH, "rb") as f:
            priv = serialization.load_pem_private_key(f.read(), password=None)
        cipher = base64.b64decode(payload.ciphertext_b64)
        plaintext = priv.decrypt(
            cipher,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        import json as _json

        data = _json.loads(plaintext.decode("utf-8"))
        svc = data.get("service")
        act = data.get("action")
        rtype = data.get("resource_type")
        rid = data.get("resource_id")
        det = data.get("detail")
    else:
        svc = payload.service
        act = payload.action
        rtype = payload.resource_type
        rid = payload.resource_id
        det = payload.detail
    row = AuditEventModel(
        service=svc or "unknown",
        action=act or "unknown",
        resource_type=rtype or "unknown",
        resource_id=rid,
        detail=det,
        actor_user=str(claims.get("sub")) if claims.get("sub") is not None else None,
        actor_role=claims.get("role"),
        actor_hospital=claims.get("hospital"),
        ip=x_real_ip,
        request_id=x_request_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get(
    "/api/audit/events",
    response_model=List[AuditEventOut],
    dependencies=[Depends(RateLimiter(times=10, seconds=1))],
)
def list_events(
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
    service: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    # Only admins can view audit logs
    if claims.get("role") not in {"SUPER_ADMIN", "HOSPITAL_ADMIN"}:
        raise HTTPException(status_code=403, detail="Forbidden")
    q = db.query(AuditEventModel).order_by(AuditEventModel.id.desc())
    if service:
        q = q.filter(AuditEventModel.service == service)
    if action:
        q = q.filter(AuditEventModel.action == action)
    return q.limit(limit).all()
