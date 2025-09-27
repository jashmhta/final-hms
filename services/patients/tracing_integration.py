"""
Distributed tracing integration for Patients Service
Example implementation for other services to follow
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from ..common.correlation_id import (
    CorrelationIDMiddleware,
    get_correlation_id,
    with_correlation_id,
)
from ..common.middleware import create_middleware_stack
from ..common.otel_config import get_meter, get_tracer, setup_otel, trace_async

logger = logging.getLogger(__name__)

# Service configuration
SERVICE_NAME = "patients-service"
SERVICE_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with OpenTelemetry setup"""
    # Setup OpenTelemetry
    otel_config = setup_otel(
        service_name=SERVICE_NAME,
        service_version=SERVICE_VERSION,
        environment=ENVIRONMENT,
        metrics_enabled=True,
        traces_enabled=True,
        logs_enabled=True,
    )

    # Get tracer and meter
    tracer = get_tracer("patients-service")
    meter = get_meter("patients-service")

    # Create custom metrics
    if meter:
        # Create counters for patient operations
        patient_operations_counter = meter.create_counter(
            "patient_operations_total", description="Total patient operations"
        )

        # Create histogram for patient query times
        patient_query_duration = meter.create_histogram(
            "patient_query_duration_seconds",
            description="Patient query duration",
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
        )

        # Store metrics in app state
        app.state.patient_operations_counter = patient_operations_counter
        app.state.patient_query_duration = patient_query_duration

    logger.info(f"{SERVICE_NAME} started with tracing enabled")

    yield

    logger.info(f"{SERVICE_NAME} shutting down")


# Create FastAPI app
app = FastAPI(
    title="HMS Patients Service",
    description="Patients management microservice",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://hms.local"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add common middleware stack
app = create_middleware_stack(
    app,
    service_name=SERVICE_NAME,
    enable_rate_limit=True,
    rate_limit_config={
        "rate_limit": 1000,  # requests per minute
        "window_size": 60,
        "strategies": ["ip", "user"],
    },
    enable_security_headers=True,
    enable_cache_control=True,
    enable_body_logging=False,
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)


# Traced endpoint examples
@app.get("/health")
@trace_async("health_check")
async def health_check(request: Request) -> Dict[str, Any]:
    """Health check endpoint with tracing"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "correlation_id": get_correlation_id(),
    }


@app.get("/api/patients")
@trace_async("list_patients")
async def list_patients(
    request: Request, skip: int = 0, limit: int = 100, search: str = None
) -> Dict[str, Any]:
    """List patients with tracing and metrics"""
    tracer = get_tracer()
    if not tracer:
        return {"patients": [], "total": 0}

    with tracer.start_as_current_span("database_query") as span:
        span.set_attribute("db.statement", "SELECT * FROM patients LIMIT ? OFFSET ?")
        span.set_attribute("db.table", "patients")

        # Simulate database query
        import asyncio

        await asyncio.sleep(0.01)  # Simulate query time

        # Get metrics from app state
        if hasattr(request.app.state, "patient_operations_counter"):
            request.app.state.patient_operations_counter.add(
                1, attributes={"operation": "list", "status": "success"}
            )

        if hasattr(request.app.state, "patient_query_duration"):
            request.app.state.patient_query_duration.record(
                0.01, attributes={"operation": "list", "has_search": search is not None}
            )

        # Return dummy data
        return {
            "patients": [
                {"id": 1, "name": "John Doe", "age": 35},
                {"id": 2, "name": "Jane Smith", "age": 28},
            ],
            "total": 2,
            "skip": skip,
            "limit": limit,
        }


@app.get("/api/patients/{patient_id}")
@trace_async("get_patient")
async def get_patient(patient_id: int, request: Request) -> Dict[str, Any]:
    """Get patient by ID with detailed tracing"""
    tracer = get_tracer()
    if not tracer:
        return {"error": "Tracing not available"}

    correlation_id = get_correlation_id()

    with tracer.start_as_current_span("patient_lookup") as span:
        span.set_attribute("patient.id", patient_id)
        span.set_attribute("correlation.id", correlation_id)

        # Simulate database query
        import asyncio

        await asyncio.sleep(0.005)

        # Record metrics
        if hasattr(request.app.state, "patient_operations_counter"):
            request.app.state.patient_operations_counter.add(
                1, attributes={"operation": "get", "status": "success"}
            )

        # Check cache first
        with tracer.start_as_current_span("cache_check") as cache_span:
            cache_span.set_attribute("cache.key", f"patient:{patient_id}")
            await asyncio.sleep(0.001)  # Simulate cache check

            # Simulate cache miss
            cache_hit = False
            cache_span.set_attribute("cache.hit", cache_hit)

        if not cache_hit:
            # Database query
            with tracer.start_as_current_span("database_query") as db_span:
                db_span.set_attribute(
                    "db.statement", "SELECT * FROM patients WHERE id = ?"
                )
                db_span.set_attribute("db.table", "patients")
                await asyncio.sleep(0.01)

                # Simulate patient data
                patient_data = {
                    "id": patient_id,
                    "name": "John Doe",
                    "age": 35,
                    "medical_record_number": "MRN123456",
                    "admission_date": "2024-01-15",
                    "department": "Cardiology",
                }

                # Cache the result
                with tracer.start_as_current_span("cache_set") as cache_set_span:
                    cache_set_span.set_attribute("cache.key", f"patient:{patient_id}")
                    await asyncio.sleep(0.001)

            # Related data queries (demonstrating distributed tracing)
            await self._get_patient_appointments(patient_id, tracer)
            await self._get_patient_medications(patient_id, tracer)
            await self._get_patient_lab_results(patient_id, tracer)

            return patient_data

        return {"error": "Patient not found"}


@app.post("/api/patients")
@trace_async("create_patient")
async def create_patient(
    patient_data: Dict[str, Any], request: Request
) -> Dict[str, Any]:
    """Create new patient with tracing"""
    tracer = get_tracer()
    correlation_id = get_correlation_id()

    with tracer.start_as_current_span("patient_creation") as span:
        span.set_attribute("correlation.id", correlation_id)
        span.set_attribute("patient.name", patient_data.get("name"))
        span.set_attribute("patient.age", patient_data.get("age"))

        # Validate input
        with tracer.start_as_current_span("validation") as validation_span:
            await asyncio.sleep(0.001)
            validation_span.set_attribute("validation.status", "passed")

        # Create patient in database
        with tracer.start_as_current_span("database_insert") as db_span:
            db_span.set_attribute("db.table", "patients")
            db_span.set_attribute("db.operation", "INSERT")
            await asyncio.sleep(0.02)

            # Simulate patient ID generation
            patient_id = 12345

            # Record metrics
            if hasattr(request.app.state, "patient_operations_counter"):
                request.app.state.patient_operations_counter.add(
                    1, attributes={"operation": "create", "status": "success"}
                )

        # Trigger background tasks
        await self._create_patient_index(patient_id, tracer)
        await self._send_welcome_notification(patient_data.get("email"), tracer)

        return {"id": patient_id, "status": "created", "correlation_id": correlation_id}


@with_correlation_id
async def _get_patient_appointments(self, patient_id: int, tracer):
    """Get patient appointments (demonstrates child span)"""
    with tracer.start_as_current_span("get_appointments") as span:
        span.set_attribute("patient.id", patient_id)
        await asyncio.sleep(0.005)  # Simulate API call to appointments service

        # Simulate appointment data
        appointments = [
            {"id": 1, "date": "2024-01-20", "type": "Follow-up"},
            {"id": 2, "date": "2024-01-25", "type": "Lab test"},
        ]

        span.set_attribute("appointments.count", len(appointments))
        return appointments


@with_correlation_id
async def _get_patient_medications(self, patient_id: int, tracer):
    """Get patient medications"""
    with tracer.start_as_current_span("get_medications") as span:
        span.set_attribute("patient.id", patient_id)
        await asyncio.sleep(0.003)  # Simulate API call to pharmacy service
        return []


@with_correlation_id
async def _get_patient_lab_results(self, patient_id: int, tracer):
    """Get patient lab results"""
    with tracer.start_as_current_span("get_lab_results") as span:
        span.set_attribute("patient.id", patient_id)
        await asyncio.sleep(0.007)  # Simulate API call to lab service
        return []


@with_correlation_id
async def _create_patient_index(self, patient_id: int, tracer):
    """Create search index for patient"""
    with tracer.start_as_current_span("create_index") as span:
        span.set_attribute("patient.id", patient_id)
        span.set_attribute("index.type", "elasticsearch")
        await asyncio.sleep(0.01)  # Simulate indexing operation


@with_correlation_id
async def _send_welcome_notification(self, email: str, tracer):
    """Send welcome notification"""
    if not email:
        return

    with tracer.start_as_current_span("send_notification") as span:
        span.set_attribute("notification.type", "welcome_email")
        span.set_attribute("notification.recipient", email)
        await asyncio.sleep(0.02)  # Simulate email sending


# Error handling with tracing
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with tracing"""
    tracer = get_tracer()
    correlation_id = get_correlation_id()

    if tracer:
        with tracer.start_as_current_span("exception") as span:
            span.set_attribute("exception.type", type(exc).__name__)
            span.set_attribute("exception.message", str(exc))
            span.set_attribute("correlation.id", correlation_id)
            span.set_attribute("error", True)

    logger.error(
        "Unhandled exception",
        error=str(exc),
        correlation_id=correlation_id,
        path=request.url.path,
    )

    return JSONResponse(
        {"error": "Internal server error", "correlation_id": correlation_id},
        status_code=500,
    )


# Health check for Kubernetes
@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness probe"""
    return {"status": "ready", "service": SERVICE_NAME}


@app.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness probe"""
    return {"status": "alive", "service": SERVICE_NAME}


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics_endpoint() -> str:
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest

    return generate_latest()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("tracing_integration:app", host="0.0.0.0", port=8000, log_level="info")
