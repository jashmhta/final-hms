"""
Patient Service - Microservice for Patient Management

This service handles patient registration, demographic management, and patient search.
It's built with FastAPI for high performance and includes HIPAA compliance features.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, date

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
import asyncpg
from cryptography.fernet import Fernet
from redis.asyncio import Redis
import jwt

# Configuration
from .config import (
    DATABASE_URL, REDIS_URL, JWT_SECRET_KEY,
    SERVICE_NAME, SERVICE_VERSION, ENCRYPTION_KEY,
    JAEGER_AGENT_HOST, JAEGER_AGENT_PORT
)

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name=JAEGER_AGENT_HOST,
    agent_port=JAEGER_AGENT_PORT,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
tracer = trace.get_tracer(__name__)

# Database setup
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis = Redis.from_url(REDIS_URL, decode_responses=True)

# Encryption setup
fernet = Fernet(ENCRYPTION_KEY)

# JWT Setup
security = HTTPBearer()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database Models
class Patient(Base):
    __tablename__ = 'patients'

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, nullable=False)
    medical_record_number = Column(String, unique=True, index=True, nullable=False)
    external_id = Column(String, index=True, nullable=True)

    # Encrypted PII fields
    first_name_encrypted = Column(Text, nullable=False)
    last_name_encrypted = Column(Text, nullable=False)
    middle_name_encrypted = Column(Text, nullable=True)
    email_encrypted = Column(Text, nullable=True)
    phone_primary_encrypted = Column(Text, nullable=True)
    phone_secondary_encrypted = Column(Text, nullable=True)
    address_encrypted = Column(Text, nullable=True)

    # Non-encrypted fields
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String, nullable=False)
    blood_type = Column(String, nullable=True)
    status = Column(String, default='ACTIVE')

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # Flags
    is_vip = Column(Boolean, default=False)
    is_confidential = Column(Boolean, default=False)
    organ_donor = Column(Boolean, default=False)
    advance_directive_on_file = Column(Boolean, default=False)

# Pydantic Models for API
class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: date
    gender: str = Field(..., description="MALE, FEMALE, OTHER, PREFER_NOT_TO_SAY")
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    blood_type: Optional[str] = Field(None, max_length=10)
    is_vip: bool = False
    is_confidential: bool = False
    organ_donor: bool = False
    advance_directive_on_file: bool = False

class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    blood_type: Optional[str] = Field(None, max_length=10)
    status: Optional[str] = None
    is_vip: Optional[bool] = None
    is_confidential: Optional[bool] = None
    organ_donor: Optional[bool] = None
    advance_directive_on_file: Optional[bool] = None

class PatientResponse(BaseModel):
    id: int
    uuid: str
    medical_record_number: str
    first_name: str
    last_name: str
    middle_name: Optional[str]
    date_of_birth: date
    gender: str
    email: Optional[str]
    phone_primary: Optional[str]
    phone_secondary: Optional[str]
    address: Optional[str]
    blood_type: Optional[str]
    status: str
    is_vip: bool
    is_confidential: bool
    organ_donor: bool
    advance_directive_on_file: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PatientSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)

# Utility functions
def encrypt_field(value: str) -> str:
    """Encrypt a field value using Fernet encryption"""
    if not value:
        return value
    return fernet.encrypt(value.encode()).decode()

def decrypt_field(encrypted_value: str) -> str:
    """Decrypt a field value using Fernet encryption"""
    if not encrypted_value:
        return encrypted_value
    return fernet.decrypt(encrypted_value.encode()).decode()

def generate_medical_record_number() -> str:
    """Generate a unique medical record number"""
    timestamp = int(datetime.utcnow().timestamp())
    return f"MRN{timestamp:08d}"

async def verify_jwt_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Event publishing
async def publish_patient_event(event_type: str, patient_data: dict):
    """Publish patient events to Kafka via Redis pub/sub"""
    event = {
        "event_type": event_type,
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "data": patient_data
    }
    await redis.publish("patient_events", str(event))
    logger.info(f"Published event: {event_type}")

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    yield
    # Shutdown
    logger.info(f"Shutting down {SERVICE_NAME}")

app = FastAPI(
    title="Patient Service",
    description="Enterprise-grade Patient Management Service",
    version=SERVICE_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check database connection
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")

        # Check Redis connection
        await redis.ping()

        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )

@app.post("/api/patients", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_jwt_token)
):
    """Create a new patient"""
    with tracer.start_as_current_span("create_patient") as span:
        span.set_attribute("user_id", token_data.get("sub"))

        # Generate medical record number
        mrn = generate_medical_record_number()

        # Create patient record
        patient = Patient(
            uuid=str(uuid.uuid4()),
            medical_record_number=mrn,
            first_name_encrypted=encrypt_field(patient_data.first_name),
            last_name_encrypted=encrypt_field(patient_data.last_name),
            middle_name_encrypted=encrypt_field(patient_data.middle_name) if patient_data.middle_name else None,
            email_encrypted=encrypt_field(patient_data.email) if patient_data.email else None,
            phone_primary_encrypted=encrypt_field(patient_data.phone_primary) if patient_data.phone_primary else None,
            phone_secondary_encrypted=encrypt_field(patient_data.phone_secondary) if patient_data.phone_secondary else None,
            address_encrypted=encrypt_field(patient_data.address) if patient_data.address else None,
            date_of_birth=patient_data.date_of_birth,
            gender=patient_data.gender,
            blood_type=patient_data.blood_type,
            is_vip=patient_data.is_vip,
            is_confidential=patient_data.is_confidential,
            organ_donor=patient_data.organ_donor,
            advance_directive_on_file=patient_data.advance_directive_on_file,
            created_by=token_data.get("sub")
        )

        db.add(patient)
        db.commit()
        db.refresh(patient)

        # Publish event
        background_tasks.add_task(
            publish_patient_event,
            "patient_created",
            {
                "patient_id": patient.id,
                "uuid": patient.uuid,
                "medical_record_number": patient.medical_record_number,
                "created_by": token_data.get("sub")
            }
        )

        span.set_attribute("patient_id", patient.id)
        logger.info(f"Created patient {patient.uuid}")

        return PatientResponse(
            id=patient.id,
            uuid=patient.uuid,
            medical_record_number=patient.medical_record_number,
            first_name=patient_data.first_name,
            last_name=patient_data.last_name,
            middle_name=patient_data.middle_name,
            date_of_birth=patient_data.date_of_birth,
            gender=patient_data.gender,
            email=patient_data.email,
            phone_primary=patient_data.phone_primary,
            phone_secondary=patient_data.phone_secondary,
            address=patient_data.address,
            blood_type=patient_data.blood_type,
            status=patient.status,
            is_vip=patient.is_vip,
            is_confidential=patient.is_confidential,
            organ_donor=patient.organ_donor,
            advance_directive_on_file=patient.advance_directive_on_file,
            created_at=patient.created_at,
            updated_at=patient.updated_at
        )

@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_jwt_token)
):
    """Get patient by ID"""
    with tracer.start_as_current_span("get_patient") as span:
        span.set_attribute("patient_id", patient_id)
        span.set_attribute("user_id", token_data.get("sub"))

        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        return PatientResponse(
            id=patient.id,
            uuid=patient.uuid,
            medical_record_number=patient.medical_record_number,
            first_name=decrypt_field(patient.first_name_encrypted),
            last_name=decrypt_field(patient.last_name_encrypted),
            middle_name=decrypt_field(patient.middle_name_encrypted) if patient.middle_name_encrypted else None,
            email=decrypt_field(patient.email_encrypted) if patient.email_encrypted else None,
            phone_primary=decrypt_field(patient.phone_primary_encrypted) if patient.phone_primary_encrypted else None,
            phone_secondary=decrypt_field(patient.phone_secondary_encrypted) if patient.phone_secondary_encrypted else None,
            address=decrypt_field(patient.address_encrypted) if patient.address_encrypted else None,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            blood_type=patient.blood_type,
            status=patient.status,
            is_vip=patient.is_vip,
            is_confidential=patient.is_confidential,
            organ_donor=patient.organ_donor,
            advance_directive_on_file=patient.advance_directive_on_file,
            created_at=patient.created_at,
            updated_at=patient.updated_at
        )

@app.put("/api/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_jwt_token)
):
    """Update patient information"""
    with tracer.start_as_current_span("update_patient") as span:
        span.set_attribute("patient_id", patient_id)
        span.set_attribute("user_id", token_data.get("sub"))

        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Update fields
        if patient_data.first_name:
            patient.first_name_encrypted = encrypt_field(patient_data.first_name)
        if patient_data.last_name:
            patient.last_name_encrypted = encrypt_field(patient_data.last_name)
        if patient_data.middle_name:
            patient.middle_name_encrypted = encrypt_field(patient_data.middle_name)
        if patient_data.email:
            patient.email_encrypted = encrypt_field(patient_data.email)
        if patient_data.phone_primary:
            patient.phone_primary_encrypted = encrypt_field(patient_data.phone_primary)
        if patient_data.phone_secondary:
            patient.phone_secondary_encrypted = encrypt_field(patient_data.phone_secondary)
        if patient_data.address:
            patient.address_encrypted = encrypt_field(patient_data.address)
        if patient_data.blood_type:
            patient.blood_type = patient_data.blood_type
        if patient_data.status:
            patient.status = patient_data.status
        if patient_data.is_vip is not None:
            patient.is_vip = patient_data.is_vip
        if patient_data.is_confidential is not None:
            patient.is_confidential = patient_data.is_confidential
        if patient_data.organ_donor is not None:
            patient.organ_donor = patient_data.organ_donor
        if patient_data.advance_directive_on_file is not None:
            patient.advance_directive_on_file = patient_data.advance_directive_on_file

        patient.updated_by = token_data.get("sub")
        patient.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(patient)

        # Publish event
        background_tasks.add_task(
            publish_patient_event,
            "patient_updated",
            {
                "patient_id": patient.id,
                "uuid": patient.uuid,
                "updated_by": token_data.get("sub"),
                "fields_updated": [k for k, v in patient_data.dict(exclude_unset=True).items()]
            }
        )

        logger.info(f"Updated patient {patient.uuid}")

        return PatientResponse(
            id=patient.id,
            uuid=patient.uuid,
            medical_record_number=patient.medical_record_number,
            first_name=decrypt_field(patient.first_name_encrypted),
            last_name=decrypt_field(patient.last_name_encrypted),
            middle_name=decrypt_field(patient.middle_name_encrypted) if patient.middle_name_encrypted else None,
            email=decrypt_field(patient.email_encrypted) if patient.email_encrypted else None,
            phone_primary=decrypt_field(patient.phone_primary_encrypted) if patient.phone_primary_encrypted else None,
            phone_secondary=decrypt_field(patient.phone_secondary_encrypted) if patient.phone_secondary_encrypted else None,
            address=decrypt_field(patient.address_encrypted) if patient.address_encrypted else None,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            blood_type=patient.blood_type,
            status=patient.status,
            is_vip=patient.is_vip,
            is_confidential=patient.is_confidential,
            organ_donor=patient.organ_donor,
            advance_directive_on_file=patient.advance_directive_on_file,
            created_at=patient.created_at,
            updated_at=patient.updated_at
        )

@app.post("/api/patients/search")
async def search_patients(
    search_request: PatientSearchRequest,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_jwt_token)
):
    """Search patients by name, MRN, or other identifiers"""
    with tracer.start_as_current_span("search_patients") as span:
        span.set_attribute("query", search_request.query)
        span.set_attribute("limit", search_request.limit)
        span.set_attribute("user_id", token_data.get("sub"))

        query = db.query(Patient)

        # Search in encrypted fields (this is a simplified approach)
        # In production, you might want to use a search index or separate search service
        search_term = f"%{search_request.query}%"

        # Try to find by medical record number first
        patients = query.filter(
            Patient.medical_record_number.ilike(search_term)
        ).offset(search_request.offset).limit(search_request.limit).all()

        if not patients:
            # If no match by MRN, search in other fields
            patients = query.filter(
                (Patient.first_name_encrypted.like(search_term)) |
                (Patient.last_name_encrypted.like(search_term)) |
                (Patient.email_encrypted.like(search_term))
            ).offset(search_request.offset).limit(search_request.limit).all()

        results = []
        for patient in patients:
            results.append(PatientResponse(
                id=patient.id,
                uuid=patient.uuid,
                medical_record_number=patient.medical_record_number,
                first_name=decrypt_field(patient.first_name_encrypted),
                last_name=decrypt_field(patient.last_name_encrypted),
                middle_name=decrypt_field(patient.middle_name_encrypted) if patient.middle_name_encrypted else None,
                email=decrypt_field(patient.email_encrypted) if patient.email_encrypted else None,
                phone_primary=decrypt_field(patient.phone_primary_encrypted) if patient.phone_primary_encrypted else None,
                phone_secondary=decrypt_field(patient.phone_secondary_encrypted) if patient.phone_secondary_encrypted else None,
                address=decrypt_field(patient.address_encrypted) if patient.address_encrypted else None,
                date_of_birth=patient.date_of_birth,
                gender=patient.gender,
                blood_type=patient.blood_type,
                status=patient.status,
                is_vip=patient.is_vip,
                is_confidential=patient.is_confidential,
                organ_donor=patient.organ_donor,
                advance_directive_on_file=patient.advance_directive_on_file,
                created_at=patient.created_at,
                updated_at=patient.updated_at
            ))

        return {"patients": results, "total": len(results)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )