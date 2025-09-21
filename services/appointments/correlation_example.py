"""
Appointments Service - Complete correlation ID integration example
Demonstrates end-to-end tracing across HTTP, message queues, and database
"""

import os
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request, Response, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import aio_pika
import aiohttp
import redis.asyncio as redis

# Import common utilities
from ..common import (
    get_correlation_id,
    set_correlation_id,
    generate_correlation_id,
    CorrelationIDMiddleware,
    with_correlation_id,
    CorrelationIDContext,
    setup_otel,
    trace_async,
    get_tracer,
    get_meter,
    create_middleware_stack,
    RabbitMQCorrelationPublisher,
    RabbitMQCorrelationConsumer,
    RedisCorrelationPublisher,
    RedisCorrelationSubscriber,
    database_operation_context,
    with_database_correlation,
    add_correlation_to_message,
    message_processing_context
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service configuration
SERVICE_NAME = "appointments-service"
SERVICE_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Database connection pool
db_pool = None

# Redis client
redis_client = None

# RabbitMQ publisher
rabbitmq_publisher = None

# Models
class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    department_id: int
    appointment_date: datetime
    duration: int = 30  # minutes
    type: str = "consultation"
    notes: Optional[str] = None
    email_reminder: bool = True
    sms_reminder: bool = True

class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    department_id: int
    appointment_date: datetime
    duration: int
    type: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Database functions
async def get_db_pool():
    """Get database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            database=os.getenv("DB_NAME", "hms_appointments"),
            min_size=5,
            max_size=20
        )
    return db_pool

async def get_redis_client():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            decode_responses=True
        )
    return redis_client

async def get_rabbitmq_publisher():
    """Get RabbitMQ publisher"""
    global rabbitmq_publisher
    if rabbitmq_publisher is None:
        rabbitmq_publisher = RabbitMQCorrelationPublisher(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672"))
        )
        rabbitmq_publisher.connect()
    return rabbitmq_publisher

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with correlation setup"""
    # Setup OpenTelemetry
    otel_config = setup_otel(
        service_name=SERVICE_NAME,
        service_version=SERVICE_VERSION,
        environment=ENVIRONMENT,
        metrics_enabled=True,
        traces_enabled=True,
        logs_enabled=True
    )

    # Initialize connections
    await get_db_pool()
    await get_redis_client()
    await get_rabbitmq_publisher()

    # Get tracer and meter
    tracer = get_tracer(SERVICE_NAME)
    meter = get_meter(SERVICE_NAME)

    # Create custom metrics
    if meter:
        app.state.appointment_counter = meter.create_counter(
            "appointments_total",
            description="Total appointments processed"
        )
        app.state.appointment_duration = meter.create_histogram(
            "appointment_processing_duration_seconds",
            description="Appointment processing duration",
            buckets=[0.05, 0.1, 0.5, 1.0, 5.0]
        )

    logger.info(f"{SERVICE_NAME} started with correlation tracking")

    yield

    # Cleanup
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()
    if rabbitmq_publisher:
        rabbitmq_publisher.close()

    logger.info(f"{SERVICE_NAME} shut down")

# Create FastAPI app
app = FastAPI(
    title="HMS Appointments Service",
    description="Appointment scheduling microservice with correlation tracking",
    version=SERVICE_VERSION,
    lifespan=lifespan
)

# Add middleware
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
        "rate_limit": 500,  # requests per minute
        "window_size": 60,
        "strategies": ["ip", "user"]
    },
    enable_security_headers=True,
    enable_cache_control=True
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# API Endpoints
@app.get("/health")
@trace_async("health_check")
async def health_check(request: Request) -> Dict[str, Any]:
    """Health check with correlation ID"""
    correlation_id = get_correlation_id()
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "correlation_id": correlation_id
    }

@app.post("/api/appointments", response_model=AppointmentResponse)
@trace_async("create_appointment")
async def create_appointment(
    appointment: AppointmentCreate,
    request: Request,
    background_tasks: BackgroundTasks
) -> AppointmentResponse:
    """Create new appointment with end-to-end correlation"""
    correlation_id = get_correlation_id()
    tracer = get_tracer()

    with tracer.start_as_current_span("appointment_creation") as span:
        span.set_attribute("correlation.id", correlation_id)
        span.set_attribute("patient.id", appointment.patient_id)
        span.set_attribute("doctor.id", appointment.doctor_id)

        # Get database connection
        pool = await get_db_pool()

        # Create appointment with correlation tracking
        async with pool.acquire() as conn:
            with database_operation_context("create_appointment", correlation_id):
                # Check for conflicts
                with tracer.start_as_current_span("check_conflicts"):
                    conflict = await check_appointment_conflict(
                        conn, appointment.doctor_id, appointment.appointment_date, appointment.duration
                    )
                    if conflict:
                        span.set_attribute("conflict_detected", True)
                        raise HTTPException(
                            status_code=409,
                            detail="Time slot not available"
                        )

                # Create appointment
                with tracer.start_as_current_span("insert_appointment"):
                    result = await conn.fetchrow(
                        """
                        INSERT INTO appointments (
                            patient_id, doctor_id, department_id,
                            appointment_date, duration, type, status,
                            notes, email_reminder, sms_reminder,
                            created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, 'scheduled', $7, $8, $9, NOW(), NOW())
                        RETURNING *
                        """,
                        appointment.patient_id,
                        appointment.doctor_id,
                        appointment.department_id,
                        appointment.appointment_date,
                        appointment.duration,
                        appointment.type,
                        appointment.notes,
                        appointment.email_reminder,
                        appointment.sms_reminder
                    )

                    appointment_data = dict(result)
                    appointment_id = appointment_data['id']

        # Record metrics
        if hasattr(request.app.state, 'appointment_counter'):
            request.app.state.appointment_counter.add(
                1,
                attributes={
                    "operation": "create",
                    "type": appointment.type
                }
            )

        # Cache the appointment
        redis = await get_redis_client()
        await redis.setex(
            f"appointment:{appointment_id}",
            3600,  # 1 hour
            json.dumps(appointment_data)
        )

        # Publish appointment created event
        background_tasks.add_task(
            publish_appointment_event,
            "appointment.created",
            appointment_data
        )

        # Schedule reminders if needed
        if appointment.email_reminder or appointment.sms_reminder:
            background_tasks.add_task(
                schedule_reminders,
                appointment_id,
                appointment.appointment_date,
                appointment.email_reminder,
                appointment.sms_reminder
            )

        return AppointmentResponse(**appointment_data)

@app.get("/api/appointments/{appointment_id}")
@trace_async("get_appointment")
async def get_appointment(
    appointment_id: int,
    request: Request
) -> AppointmentResponse:
    """Get appointment by ID with correlation tracking"""
    correlation_id = get_correlation_id()
    tracer = get_tracer()

    with tracer.start_as_current_span("get_appointment") as span:
        span.set_attribute("correlation.id", correlation_id)
        span.set_attribute("appointment.id", appointment_id)

        # Check cache first
        redis = await get_redis_client()
        cached_data = await redis.get(f"appointment:{appointment_id}")

        if cached_data:
            span.set_attribute("cache.hit", True)
            appointment_data = json.loads(cached_data)
        else:
            span.set_attribute("cache.hit", False)
            # Get from database
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                with database_operation_context("get_appointment", correlation_id):
                    result = await conn.fetchrow(
                        "SELECT * FROM appointments WHERE id = $1",
                        appointment_id
                    )

                    if not result:
                        span.set_attribute("appointment.found", False)
                        raise HTTPException(status_code=404, detail="Appointment not found")

                    appointment_data = dict(result)
                    span.set_attribute("appointment.found", True)

                    # Cache the result
                    await redis.setex(
                        f"appointment:{appointment_id}",
                        3600,
                        json.dumps(appointment_data)
                    )

        # Get related data with correlation propagation
        with tracer.start_as_current_span("get_related_data"):
            # Call patients service
            patient_data = await call_patients_service(
                appointment_data['patient_id'],
                correlation_id
            )

            # Call doctors service
            doctor_data = await call_doctors_service(
                appointment_data['doctor_id'],
                correlation_id
            )

        # Record metrics
        if hasattr(request.app.state, 'appointment_counter'):
            request.app.state.appointment_counter.add(
                1,
                attributes={
                    "operation": "get",
                    "cache_hit": cached_data is not None
                }
            )

        return AppointmentResponse(**appointment_data)

@app.get("/api/appointments")
@trace_async("list_appointments")
async def list_appointments(
    request: Request,
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    """List appointments with filters and correlation tracking"""
    correlation_id = get_correlation_id()
    tracer = get_tracer()

    with tracer.start_as_current_span("list_appointments") as span:
        span.set_attribute("correlation.id", correlation_id)
        span.set_attribute("skip", skip)
        span.set_attribute("limit", limit)

        # Build query
        conditions = []
        params = []
        param_count = 0

        if patient_id:
            param_count += 1
            conditions.append(f"patient_id = ${param_count}")
            params.append(patient_id)
            span.set_attribute("filter.patient_id", patient_id)

        if doctor_id:
            param_count += 1
            conditions.append(f"doctor_id = ${param_count}")
            params.append(doctor_id)
            span.set_attribute("filter.doctor_id", doctor_id)

        if date_from:
            param_count += 1
            conditions.append(f"appointment_date >= ${param_count}")
            params.append(date_from)
            span.set_attribute("filter.date_from", date_from.isoformat())

        if date_to:
            param_count += 1
            conditions.append(f"appointment_date <= ${param_count}")
            params.append(date_to)
            span.set_attribute("filter.date_to", date_to.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Add pagination
        param_count += 1
        params.append(limit)
        param_count += 1
        params.append(skip)

        query = f"""
        SELECT * FROM appointments
        WHERE {where_clause}
        ORDER BY appointment_date
        LIMIT ${param_count-1} OFFSET ${param_count}
        """

        # Get count
        count_query = f"SELECT COUNT(*) FROM appointments WHERE {where_clause}"

        # Execute queries
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            with database_operation_context("list_appointments", correlation_id):
                # Get appointments
                results = await conn.fetch(query, *params)
                appointments = [dict(row) for row in results]

                # Get total count
                total = await conn.fetchval(count_query, *params[:-2])

        span.set_attribute("appointments.count", len(appointments))
        span.set_attribute("appointments.total", total)

        # Record metrics
        if hasattr(request.app.state, 'appointment_counter'):
            request.app.state.appointment_counter.add(
                1,
                attributes={
                    "operation": "list",
                    "results_count": len(appointments)
                }
            )

        return {
            "appointments": appointments,
            "total": total,
            "skip": skip,
            "limit": limit
        }

# Helper functions
@trace_async("check_appointment_conflict")
async def check_appointment_conflict(
    conn: asyncpg.Connection,
    doctor_id: int,
    appointment_date: datetime,
    duration: int
) -> bool:
    """Check for appointment conflicts"""
    end_time = appointment_date + timedelta(minutes=duration)

    conflict = await conn.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM appointments
            WHERE doctor_id = $1
            AND status IN ('scheduled', 'confirmed')
            AND (
                (appointment_date <= $2 AND appointment_date + (duration || ' minutes')::interval > $2)
                OR (appointment_date < $3 AND appointment_date + (duration || ' minutes')::interval >= $3)
                OR (appointment_date >= $2 AND appointment_date + (duration || ' minutes')::interval <= $3)
            )
        )
        """,
        doctor_id,
        appointment_date,
        end_time
    )

    return conflict

@with_correlation_id
async def publish_appointment_event(event_type: str, appointment_data: Dict[str, Any]):
    """Publish appointment event with correlation ID"""
    correlation_id = get_correlation_id()
    tracer = get_tracer()

    with tracer.start_as_current_span("publish_event") as span:
        span.set_attribute("correlation.id", correlation_id)
        span.set_attribute("event.type", event_type)

        # Get RabbitMQ publisher
        publisher = await get_rabbitmq_publisher()

        # Prepare event
        event = {
            "event_type": event_type,
            "appointment": appointment_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Publish to RabbitMQ
        publisher.publish(
            exchange="appointments",
            routing_key=f"appointment.{event_type}",
            body=event,
            correlation_id=correlation_id,
            message_type=event_type
        )

        # Also publish to Redis pub/sub for real-time updates
        redis_publisher = RedisCorrelationPublisher()
        redis_publisher.publish(
            channel=f"appointment_updates:{appointment_data['patient_id']}",
            message=event,
            correlation_id=correlation_id
        )

        logger.info(
            f"Published appointment event: {event_type}",
            correlation_id=correlation_id,
            appointment_id=appointment_data['id']
        )

@with_correlation_id
async def schedule_reminders(
    appointment_id: int,
    appointment_date: datetime,
    email_reminder: bool,
    sms_reminder: bool
):
    """Schedule appointment reminders"""
    correlation_id = get_correlation_id()
    tracer = get_tracer()

    with tracer.start_as_current_span("schedule_reminders") as span:
        span.set_attribute("correlation.id", correlation_id)
        span.set_attribute("appointment.id", appointment_id)

        # Calculate reminder times
        reminder_time = appointment_date - timedelta(hours=24)  # 24 hours before

        # Create reminder tasks
        reminder_tasks = []

        if email_reminder:
            reminder_tasks.append({
                "type": "email",
                "appointment_id": appointment_id,
                "scheduled_at": reminder_time.isoformat()
            })

        if sms_reminder:
            reminder_tasks.append({
                "type": "sms",
                "appointment_id": appointment_id,
                "scheduled_at": reminder_time.isoformat()
            })

        # Publish reminder tasks
        publisher = await get_rabbitmq_publisher()
        for task in reminder_tasks:
            publisher.publish(
                exchange="reminders",
                routing_key="reminder.schedule",
                body=task,
                correlation_id=correlation_id,
                message_type="reminder_task"
            )

        logger.info(
            f"Scheduled {len(reminder_tasks)} reminders",
            correlation_id=correlation_id,
            appointment_id=appointment_id
        )

@with_correlation_id
async def call_patients_service(patient_id: int, correlation_id: str) -> Dict[str, Any]:
    """Call patients service with correlation propagation"""
    tracer = get_tracer()

    with tracer.start_as_current_span("call_patients_service") as span:
        span.set_attribute("correlation.id", correlation_id)
        span.set_attribute("patient.id", patient_id)

        # Make HTTP call with correlation ID
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-correlation-id": correlation_id,
                "content-type": "application/json"
            }

            try:
                async with session.get(
                    f"http://patients-service:8000/api/patients/{patient_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        patient_data = await response.json()
                        span.set_attribute("service.status", "success")
                        return patient_data
                    else:
                        span.set_attribute("service.status", "error")
                        span.set_attribute("service.error_code", response.status)
                        return {"id": patient_id, "name": "Unknown Patient"}
            except Exception as e:
                span.set_attribute("service.status", "failed")
                span.set_attribute("service.error", str(e))
                return {"id": patient_id, "name": "Unknown Patient"}

@with_correlation_id
async def call_doctors_service(doctor_id: int, correlation_id: str) -> Dict[str, Any]:
    """Call doctors service with correlation propagation"""
    tracer = get_tracer()

    with tracer.start_as_current_span("call_doctors_service") as span:
        span.set_attribute("correlation.id", correlation_id)
        span.set_attribute("doctor.id", doctor_id)

        # Make HTTP call with correlation ID
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-correlation-id": correlation_id,
                "content-type": "application/json"
            }

            try:
                async with session.get(
                    f"http://doctors-service:8000/api/doctors/{doctor_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        doctor_data = await response.json()
                        span.set_attribute("service.status", "success")
                        return doctor_data
                    else:
                        span.set_attribute("service.status", "error")
                        span.set_attribute("service.error_code", response.status)
                        return {"id": doctor_id, "name": "Unknown Doctor"}
            except Exception as e:
                span.set_attribute("service.status", "failed")
                span.set_attribute("service.error", str(e))
                return {"id": doctor_id, "name": "Unknown Doctor"}

# Message consumer example
@with_message_correlation
async def handle_appointment_events(message: Dict[str, Any]):
    """Handle appointment events from message queue"""
    correlation_id = extract_correlation_from_message(message)
    tracer = get_tracer()

    with tracer.start_as_current_span("handle_appointment_event") as span:
        span.set_attribute("correlation.id", correlation_id)

        event_type = message.get('event_type')
        appointment = message.get('appointment')

        if event_type == 'appointment.created':
            # Send confirmation
            await send_confirmation_email(appointment)
            span.set_attribute("action", "confirmation_sent")

        elif event_type == 'appointment.cancelled':
            # Handle cancellation
            await handle_cancellation(appointment)
            span.set_attribute("action", "cancellation_handled")

        elif event_type == 'appointment.rescheduled':
            # Handle rescheduling
            await handle_rescheduling(appointment)
            span.set_attribute("action", "rescheduling_handled")

@with_correlation_id
async def send_confirmation_email(appointment: Dict[str, Any]):
    """Send confirmation email with correlation tracking"""
    correlation_id = get_correlation_id()
    tracer = get_tracer()

    with tracer.start_as_current_span("send_confirmation_email") as span:
        span.set_attribute("correlation.id", correlation_id)
        span.set_attribute("appointment.id", appointment['id'])

        # Get patient details
        patient_data = await call_patients_service(
            appointment['patient_id'],
            correlation_id
        )

        # Send email (mock implementation)
        logger.info(
            "Sending confirmation email",
            correlation_id=correlation_id,
            appointment_id=appointment['id'],
            patient_email=patient_data.get('email')
        )

        # Record email sent
        redis = await get_redis_client()
        await redis.setex(
            f"email_sent:{appointment['id']}",
            86400,  # 24 hours
            json.dumps({
                "sent_at": datetime.utcnow().isoformat(),
                "correlation_id": correlation_id
            })
        )

# Example consumer setup
async def setup_message_consumers():
    """Setup message queue consumers"""
    # RabbitMQ consumer
    consumer = RabbitMQCorrelationConsumer()
    consumer.register_handler("appointment.created", handle_appointment_events)
    consumer.register_handler("appointment.cancelled", handle_appointment_events)
    consumer.register_handler("appointment.rescheduled", handle_appointment_events)

    # Start consuming in background
    import asyncio
    asyncio.create_task(consumer.start_consuming("appointments_queue"))

    # Redis subscriber
    redis_subscriber = RedisCorrelationSubscriber()
    redis_subscriber.register_handler(
        f"appointment_updates:*",
        handle_realtime_updates
    )

    # Start listening in background
    asyncio.create_task(redis_subscriber.start_listening(["appointment_updates:*"]))

@with_correlation_id
async def handle_realtime_updates(message: Dict[str, Any]):
    """Handle real-time updates via Redis pub/sub"""
    correlation_id = get_correlation_id()
    logger.info(
        "Received real-time update",
        correlation_id=correlation_id,
        event_type=message.get('event_type')
    )

    # Push to WebSocket clients if connected
    # This would integrate with your WebSocket implementation

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "correlation_example:app",
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )