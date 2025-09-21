# CQRS API Implementation
# Enterprise-grade CQRS API for HMS microservices

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import logging

from .event_store import Event, EventType, EventStore, get_event_store
from .command_handler import Command, CommandResult, CommandPriority, dispatch_command, dispatch_command_async
from .query_handler import Query, QueryResult, QueryType, dispatch_query, initialize_read_model
from .projector import Projector, get_projector, initialize_projections

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HMS CQRS API",
    description="Enterprise-grade CQRS API for Hospital Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# WebSocket manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Request/Response Models
class PatientRegistrationRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[Dict[str, str]] = None
    emergency_contact: Optional[Dict[str, str]] = None
    medical_history: List[Dict[str, Any]] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    medications: List[Dict[str, Any]] = Field(default_factory=list)

class PatientUpdateRequest(BaseModel):
    patient_id: str
    updates: Dict[str, Any]

class PatientAdmissionRequest(BaseModel):
    patient_id: str
    admission_date: str
    department: str
    room_number: Optional[str] = None
    bed_number: Optional[str] = None
    admitting_physician: Optional[str] = None
    admission_reason: Optional[str] = None
    expected_stay: Optional[int] = None

class AppointmentCreationRequest(BaseModel):
    patient_id: str
    provider_id: str
    appointment_time: str
    duration: int = Field(..., gt=0)
    appointment_type: str = Field(default="general")
    location: Optional[str] = None
    notes: Optional[str] = None

class AppointmentUpdateRequest(BaseModel):
    appointment_id: str
    updates: Dict[str, Any]

class PatientQueryRequest(BaseModel):
    patient_id: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: Optional[str] = None
    search_term: Optional[str] = None

class AppointmentQueryRequest(BaseModel):
    appointment_id: Optional[str] = None
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

class AnalyticsQueryRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metric_type: Optional[str] = None

# Command Endpoints
@app.post("/commands/patient/register", response_model=Dict[str, Any])
async def register_patient(
    request: PatientRegistrationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Register a new patient"""
    try:
        command = Command(
            type="patient_register",
            data=request.dict(),
            user_id=credentials.credentials,
            metadata={
                "ip_address": "192.168.1.1",  # Would get from request
                "user_agent": "HMS CQRS API"
            },
            priority=CommandPriority.NORMAL
        )

        result = await dispatch_command(command)

        if result.status.value == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )

        return {
            "success": True,
            "command_id": result.command_id,
            "patient_id": result.result.get("patient_id"),
            "processing_time": result.processing_time
        }

    except Exception as e:
        logger.error(f"Error registering patient: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/commands/patient/update", response_model=Dict[str, Any])
async def update_patient(
    request: PatientUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update patient information"""
    try:
        command = Command(
            type="patient_update",
            data=request.dict(),
            user_id=credentials.credentials,
            metadata={
                "ip_address": "192.168.1.1",
                "user_agent": "HMS CQRS API"
            },
            priority=CommandPriority.NORMAL
        )

        result = await dispatch_command(command)

        if result.status.value == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )

        return {
            "success": True,
            "command_id": result.command_id,
            "patient_id": result.result.get("patient_id"),
            "processing_time": result.processing_time
        }

    except Exception as e:
        logger.error(f"Error updating patient: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/commands/patient/admit", response_model=Dict[str, Any])
async def admit_patient(
    request: PatientAdmissionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Admit a patient"""
    try:
        command = Command(
            type="patient_admit",
            data=request.dict(),
            user_id=credentials.credentials,
            metadata={
                "ip_address": "192.168.1.1",
                "user_agent": "HMS CQRS API"
            },
            priority=CommandPriority.HIGH
        )

        result = await dispatch_command(command)

        if result.status.value == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )

        return {
            "success": True,
            "command_id": result.command_id,
            "patient_id": result.result.get("patient_id"),
            "processing_time": result.processing_time
        }

    except Exception as e:
        logger.error(f"Error admitting patient: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/commands/appointment/create", response_model=Dict[str, Any])
async def create_appointment(
    request: AppointmentCreationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new appointment"""
    try:
        command = Command(
            type="appointment_create",
            data=request.dict(),
            user_id=credentials.credentials,
            metadata={
                "ip_address": "192.168.1.1",
                "user_agent": "HMS CQRS API"
            },
            priority=CommandPriority.NORMAL
        )

        result = await dispatch_command(command)

        if result.status.value == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )

        return {
            "success": True,
            "command_id": result.command_id,
            "appointment_id": result.result.get("appointment_id"),
            "processing_time": result.processing_time
        }

    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/commands/appointment/update", response_model=Dict[str, Any])
async def update_appointment(
    request: AppointmentUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update appointment information"""
    try:
        command = Command(
            type="appointment_update",
            data=request.dict(),
            user_id=credentials.credentials,
            metadata={
                "ip_address": "192.168.1.1",
                "user_agent": "HMS CQRS API"
            },
            priority=CommandPriority.NORMAL
        )

        result = await dispatch_command(command)

        if result.status.value == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )

        return {
            "success": True,
            "command_id": result.command_id,
            "appointment_id": result.result.get("appointment_id"),
            "processing_time": result.processing_time
        }

    except Exception as e:
        logger.error(f"Error updating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Query Endpoints
@app.post("/queries/patients", response_model=Dict[str, Any])
async def get_patients(
    request: PatientQueryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Query patients"""
    try:
        cache_key = f"patients:{hash(str(request.dict()))}"

        query = Query(
            id=f"query_{datetime.utcnow().timestamp()}",
            type=QueryType.GET_PATIENTS,
            parameters=request.dict(),
            user_id=credentials.credentials,
            cache_key=cache_key,
            cache_ttl=300  # 5 minutes
        )

        result = await dispatch_query(query)

        if result.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )

        return {
            "success": True,
            "query_id": result.query_id,
            "data": result.data,
            "cached": result.cached,
            "processing_time": result.processing_time,
            "total_count": result.total_count,
            "page": result.page,
            "page_size": result.page_size
        }

    except Exception as e:
        logger.error(f"Error querying patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/queries/patients/{patient_id}", response_model=Dict[str, Any])
async def get_patient(
    patient_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific patient"""
    try:
        cache_key = f"patient:{patient_id}"

        query = Query(
            id=f"query_{datetime.utcnow().timestamp()}",
            type=QueryType.GET_PATIENT,
            parameters={"patient_id": patient_id},
            user_id=credentials.credentials,
            cache_key=cache_key,
            cache_ttl=300  # 5 minutes
        )

        result = await dispatch_query(query)

        if result.error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error
            )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )

        return {
            "success": True,
            "query_id": result.query_id,
            "data": result.data,
            "cached": result.cached,
            "processing_time": result.processing_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/queries/appointments", response_model=Dict[str, Any])
async def get_appointments(
    request: AppointmentQueryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Query appointments"""
    try:
        cache_key = f"appointments:{hash(str(request.dict()))}"

        query = Query(
            id=f"query_{datetime.utcnow().timestamp()}",
            type=QueryType.GET_APPOINTMENTS,
            parameters=request.dict(),
            user_id=credentials.credentials,
            cache_key=cache_key,
            cache_ttl=300  # 5 minutes
        )

        result = await dispatch_query(query)

        if result.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )

        return {
            "success": True,
            "query_id": result.query_id,
            "data": result.data,
            "cached": result.cached,
            "processing_time": result.processing_time,
            "total_count": result.total_count,
            "page": result.page,
            "page_size": result.page_size
        }

    except Exception as e:
        logger.error(f"Error querying appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/queries/appointments/{appointment_id}", response_model=Dict[str, Any])
async def get_appointment(
    appointment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific appointment"""
    try:
        cache_key = f"appointment:{appointment_id}"

        query = Query(
            id=f"query_{datetime.utcnow().timestamp()}",
            type=QueryType.GET_APPOINTMENT,
            parameters={"appointment_id": appointment_id},
            user_id=credentials.credentials,
            cache_key=cache_key,
            cache_ttl=300  # 5 minutes
        )

        result = await dispatch_query(query)

        if result.error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error
            )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )

        return {
            "success": True,
            "query_id": result.query_id,
            "data": result.data,
            "cached": result.cached,
            "processing_time": result.processing_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/queries/analytics", response_model=Dict[str, Any])
async def get_analytics(
    request: AnalyticsQueryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get analytics data"""
    try:
        cache_key = f"analytics:{hash(str(request.dict()))}"

        query = Query(
            id=f"query_{datetime.utcnow().timestamp()}",
            type=QueryType.GET_SYSTEM_METRICS,
            parameters=request.dict(),
            user_id=credentials.credentials,
            cache_key=cache_key,
            cache_ttl=60  # 1 minute for analytics
        )

        result = await dispatch_query(query)

        if result.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )

        return {
            "success": True,
            "query_id": result.query_id,
            "data": result.data,
            "cached": result.cached,
            "processing_time": result.processing_time
        }

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# WebSocket endpoints
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle WebSocket messages if needed
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check if event store is available
        event_store = await get_event_store()

        # Check if projector is available
        projector_instance = await get_projector()

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "event_store": "connected",
            "projector": "connected"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    try:
        # Get basic metrics
        cache_key = f"metrics:system"
        query = Query(
            id=f"query_{datetime.utcnow().timestamp()}",
            type=QueryType.GET_SYSTEM_METRICS,
            parameters={},
            cache_key=cache_key,
            cache_ttl=60
        )

        result = await dispatch_query(query)

        return {
            "success": True,
            "metrics": result.data,
            "cached": result.cached,
            "processing_time": result.processing_time
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Event subscription endpoint
@app.post("/events/subscribe")
async def subscribe_to_events(
    event_types: List[str] = [],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Subscribe to specific event types"""
    try:
        # This would set up event subscriptions for the user
        return {
            "success": True,
            "message": f"Subscribed to {len(event_types)} event types",
            "event_types": event_types
        }
    except Exception as e:
        logger.error(f"Error subscribing to events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Projection management endpoints
@app.post("/projections/rebuild")
async def rebuild_projections(
    projection_type: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Rebuild projections"""
    try:
        projector_instance = await get_projector()

        if projection_type:
            # Rebuild specific projection type
            from .projector import ProjectionType
            try:
                proj_type = ProjectionType(projection_type)
                projections = await projector_instance.get_projections_by_type(proj_type)
                for projection in projections:
                    await projector_instance.rebuild_projection(projection.id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid projection type: {projection_type}"
                )
        else:
            # Rebuild all projections
            projections = await projector_instance.get_projections_by_type(None)
            for projection in projections:
                await projector_instance.rebuild_projection(projection.id)

        return {
            "success": True,
            "message": f"Projections rebuilt successfully"
        }
    except Exception as e:
        logger.error(f"Error rebuilding projections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/projections")
async def get_projections(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all projections"""
    try:
        projector_instance = await get_projector()

        # Get all projections
        projections = []
        for projection_type in [
            "patient_projection",
            "appointment_projection",
            "clinical_projection",
            "billing_projection",
            "analytics_projection"
        ]:
            try:
                type_projections = await projector_instance.get_projections_by_type(
                    projector_instance.ProjectionType(projection_type)
                )
                projections.extend(type_projections)
            except ValueError:
                continue

        return {
            "success": True,
            "projections": [
                {
                    "id": proj.id,
                    "type": proj.type.value,
                    "name": proj.name,
                    "description": proj.description,
                    "state": proj.state.value,
                    "last_processed_event_id": proj.last_processed_event_id,
                    "last_processed_event_timestamp": proj.last_processed_event_timestamp.isoformat() if proj.last_processed_event_timestamp else None,
                    "error_message": proj.error_message,
                    "version": proj.version
                }
                for proj in projections
            ]
        }
    except Exception as e:
        logger.error(f"Error getting projections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize CQRS components on startup"""
    try:
        # Initialize read model
        await initialize_read_model()

        # Initialize projections
        await initialize_projections()

        logger.info("CQRS API started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup CQRS components on shutdown"""
    try:
        # Cleanup connections
        logger.info("CQRS API shutdown successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)