# Projector Implementation
# Enterprise-grade event projection for HMS microservices

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import asyncpg
from redis.asyncio import Redis
import logging
import uuid

from .event_store import Event, EventType, EventStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectionType(Enum):
    """Types of projections"""
    PATIENT_PROJECTION = "patient_projection"
    APPOINTMENT_PROJECTION = "appointment_projection"
    CLINICAL_PROJECTION = "clinical_projection"
    BILLING_PROJECTION = "billing_projection"
    ANALYTICS_PROJECTION = "analytics_projection"
    AUDIT_PROJECTION = "audit_projection"

class ProjectionState(Enum):
    """Projection states"""
    IDLE = "idle"
    BUILDING = "building"
    RUNNING = "running"
    ERROR = "error"
    CATCHING_UP = "catching_up"

class Projection(BaseModel):
    """Base projection model"""
    id: str
    type: ProjectionType
    name: str
    description: str
    version: int = 1
    last_processed_event_id: Optional[str] = None
    last_processed_event_timestamp: Optional[datetime] = None
    state: ProjectionState = ProjectionState.IDLE
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Projector:
    """Base projector class for building read models from events"""

    def __init__(self, postgres_url: str, redis_url: str):
        self.postgres_url = postgres_url
        self.redis_url = redis_url
        self.postgres_pool = None
        self.redis_client = None
        self.projections: Dict[str, Projection] = {}
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.running = False

    async def initialize(self):
        """Initialize the projector"""
        self.postgres_pool = await asyncpg.create_pool(self.postgres_url)
        self.redis_client = Redis.from_url(self.redis_url, decode_responses=True)

        await self._create_projection_tables()
        await self._register_event_handlers()

    async def _create_projection_tables(self):
        """Create projection tracking tables"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS projections (
                    id UUID PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    version INTEGER DEFAULT 1,
                    last_processed_event_id UUID,
                    last_processed_event_timestamp TIMESTAMP,
                    state TEXT DEFAULT 'idle',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS projection_errors (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    projection_id UUID NOT NULL,
                    event_id UUID NOT NULL,
                    error_message TEXT NOT NULL,
                    error_details JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (projection_id) REFERENCES projections(id)
                );
            ''')

            # Create indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_projections_type ON projections(type);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_projections_state ON projections(state);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_projection_errors_projection_id ON projection_errors(projection_id);')

    async def _register_event_handlers(self):
        """Register event handlers for all projection types"""
        # Patient projection handlers
        self._register_event_handler(EventType.PATIENT_REGISTERED, self._handle_patient_registered)
        self._register_event_handler(EventType.PATIENT_UPDATED, self._handle_patient_updated)
        self._register_event_handler(EventType.PATIENT_DELETED, self._handle_patient_deleted)
        self._register_event_handler(EventType.PATIENT_ADMITTED, self._handle_patient_admitted)
        self._register_event_handler(EventType.PATIENT_DISCHARGED, self._handle_patient_discharged)

        # Appointment projection handlers
        self._register_event_handler(EventType.APPOINTMENT_CREATED, self._handle_appointment_created)
        self._register_event_handler(EventType.APPOINTMENT_UPDATED, self._handle_appointment_updated)
        self._register_event_handler(EventType.APPOINTMENT_CANCELLED, self._handle_appointment_cancelled)
        self._register_event_handler(EventType.APPOINTMENT_COMPLETED, self._handle_appointment_completed)

        # Clinical projection handlers
        self._register_event_handler(EventType.CLINICAL_NOTE_CREATED, self._handle_clinical_note_created)
        self._register_event_handler(EventType.PRESCRIPTION_CREATED, self._handle_prescription_created)
        self._register_event_handler(EventType.PRESCRIPTION_UPDATED, self._handle_prescription_updated)
        self._register_event_handler(EventType.PRESCRIPTION_CANCELLED, self._handle_prescription_cancelled)

        # Billing projection handlers
        self._register_event_handler(EventType.BILL_CREATED, self._handle_bill_created)
        self._register_event_handler(EventType.BILL_UPDATED, self._handle_bill_updated)
        self._register_event_handler(EventType.BILL_PAID, self._handle_bill_paid)
        self._register_event_handler(EventType.BILL_CANCELLED, self._handle_bill_cancelled)

    def _register_event_handler(self, event_type: EventType, handler: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def create_projection(self, projection_type: ProjectionType, name: str, description: str) -> Projection:
        """Create a new projection"""
        projection_id = str(uuid.uuid4())
        projection = Projection(
            id=projection_id,
            type=projection_type,
            name=name,
            description=description
        )

        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO projections (id, type, name, description, version, state)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', projection.id, projection.type.value, projection.name, projection.description,
                projection.version, projection.state.value)

        self.projections[projection_id] = projection
        return projection

    async def get_projection(self, projection_id: str) -> Optional[Projection]:
        """Get a projection by ID"""
        async with self.postgres_pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM projections WHERE id = $1
            ''', projection_id)

            if not row:
                return None

            return Projection(
                id=str(row['id']),
                type=ProjectionType(row['type']),
                name=row['name'],
                description=row['description'],
                version=row['version'],
                last_processed_event_id=str(row['last_processed_event_id']) if row['last_processed_event_id'] else None,
                last_processed_event_timestamp=row['last_processed_event_timestamp'],
                state=ProjectionState(row['state']),
                error_message=row['error_message'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )

    async def get_projections_by_type(self, projection_type: ProjectionType) -> List[Projection]:
        """Get all projections of a specific type"""
        async with self.postgres_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM projections WHERE type = $1
            ''', projection_type.value)

            return [
                Projection(
                    id=str(row['id']),
                    type=ProjectionType(row['type']),
                    name=row['name'],
                    description=row['description'],
                    version=row['version'],
                    last_processed_event_id=str(row['last_processed_event_id']) if row['last_processed_event_id'] else None,
                    last_processed_event_timestamp=row['last_processed_event_timestamp'],
                    state=ProjectionState(row['state']),
                    error_message=row['error_message'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ) for row in rows
            ]

    async def update_projection_state(self, projection_id: str, state: ProjectionState, event_id: Optional[str] = None, error_message: Optional[str] = None):
        """Update projection state"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                UPDATE projections
                SET state = $1, last_processed_event_id = $2, error_message = $3, updated_at = NOW()
                WHERE id = $4
            ''', state.value, event_id, error_message, projection_id)

        if projection_id in self.projections:
            self.projections[projection_id].state = state
            self.projections[projection_id].last_processed_event_id = event_id
            self.projections[projection_id].error_message = error_message
            self.projections[projection_id].updated_at = datetime.utcnow()

    async def process_event(self, event: Event):
        """Process a single event through all projections"""
        if event.type not in self.event_handlers:
            return

        for handler in self.event_handlers[event.type]:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error processing event {event.id} with handler {handler.__name__}: {e}")
                await self._log_projection_error(event.id, str(e), {"handler": handler.__name__})

    async def process_events_batch(self, events: List[Event]):
        """Process a batch of events"""
        for event in events:
            await self.process_event(event)

    async def start_projection(self, projection_id: str):
        """Start a projection"""
        projection = await self.get_projection(projection_id)
        if not projection:
            raise ValueError(f"Projection {projection_id} not found")

        await self.update_projection_state(projection_id, ProjectionState.RUNNING)

        # Start processing events from where we left off
        event_store = EventStore(self.postgres_url, self.redis_url)
        await event_store.initialize()

        # Get events since last processed
        events = await event_store.get_events_by_time_range(
            projection.last_processed_event_timestamp or datetime.min,
            datetime.utcnow()
        )

        await self.process_events_batch(events)

        # Update projection state
        if events:
            last_event = events[-1]
            await self.update_projection_state(
                projection_id,
                ProjectionState.RUNNING,
                last_event.id,
                last_event.timestamp
            )

    async def rebuild_projection(self, projection_id: str):
        """Rebuild a projection from scratch"""
        projection = await self.get_projection(projection_id)
        if not projection:
            raise ValueError(f"Projection {projection_id} not found")

        await self.update_projection_state(projection_id, ProjectionState.BUILDING)

        # Clear existing data for this projection type
        await self._clear_projection_data(projection.type)

        # Get all events
        event_store = EventStore(self.postgres_url, self.redis_url)
        await event_store.initialize()

        # Get all events for the projection type
        relevant_event_types = self._get_relevant_event_types(projection.type)
        events = []

        for event_type in relevant_event_types:
            type_events = await event_store.get_events_by_type(event_type)
            events.extend(type_events)

        # Sort events by timestamp
        events.sort(key=lambda x: x.timestamp)

        # Process events
        await self.process_events_batch(events)

        # Update projection state
        if events:
            last_event = events[-1]
            await self.update_projection_state(
                projection_id,
                ProjectionState.RUNNING,
                last_event.id,
                last_event.timestamp
            )

    async def _clear_projection_data(self, projection_type: ProjectionType):
        """Clear existing data for a projection type"""
        async with self.postgres_pool.acquire() as conn:
            if projection_type == ProjectionType.PATIENT_PROJECTION:
                await conn.execute('TRUNCATE TABLE patient_read_model CASCADE')
            elif projection_type == ProjectionType.APPOINTMENT_PROJECTION:
                await conn.execute('TRUNCATE TABLE appointment_read_model CASCADE')
            elif projection_type == ProjectionType.CLINICAL_PROJECTION:
                await conn.execute('TRUNCATE TABLE clinical_notes_read_model CASCADE')
            elif projection_type == ProjectionType.BILLING_PROJECTION:
                await conn.execute('TRUNCATE TABLE billing_read_model CASCADE')
            elif projection_type == ProjectionType.ANALYTICS_PROJECTION:
                await conn.execute('TRUNCATE TABLE analytics_read_model CASCADE')

    def _get_relevant_event_types(self, projection_type: ProjectionType) -> List[EventType]:
        """Get relevant event types for a projection"""
        mapping = {
            ProjectionType.PATIENT_PROJECTION: [
                EventType.PATIENT_REGISTERED,
                EventType.PATIENT_UPDATED,
                EventType.PATIENT_DELETED,
                EventType.PATIENT_ADMITTED,
                EventType.PATIENT_DISCHARGED
            ],
            ProjectionType.APPOINTMENT_PROJECTION: [
                EventType.APPOINTMENT_CREATED,
                EventType.APPOINTMENT_UPDATED,
                EventType.APPOINTMENT_CANCELLED,
                EventType.APPOINTMENT_COMPLETED
            ],
            ProjectionType.CLINICAL_PROJECTION: [
                EventType.CLINICAL_NOTE_CREATED,
                EventType.PRESCRIPTION_CREATED,
                EventType.PRESCRIPTION_UPDATED,
                EventType.PRESCRIPTION_CANCELLED
            ],
            ProjectionType.BILLING_PROJECTION: [
                EventType.BILL_CREATED,
                EventType.BILL_UPDATED,
                EventType.BILL_PAID,
                EventType.BILL_CANCELLED
            ],
            ProjectionType.ANALYTICS_PROJECTION: [
                EventType.PATIENT_REGISTERED,
                EventType.APPOINTMENT_CREATED,
                EventType.APPOINTMENT_COMPLETED,
                EventType.BILL_CREATED,
                EventType.BILL_PAID
            ]
        }
        return mapping.get(projection_type, [])

    async def _log_projection_error(self, event_id: str, error_message: str, error_details: Dict[str, Any]):
        """Log a projection error"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO projection_errors (event_id, error_message, error_details)
                VALUES ($1, $2, $3)
            ''', event_id, error_message, json.dumps(error_details))

    # Patient projection handlers
    async def _handle_patient_registered(self, event: Event):
        """Handle patient registered event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO patient_read_model (
                    patient_id, first_name, last_name, date_of_birth, email,
                    phone, address, emergency_contact, medical_history, allergies,
                    medications, status, created_at, updated_at, last_event_version
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            ''',
                event.data["patient_id"],
                event.data["first_name"],
                event.data["last_name"],
                event.data["date_of_birth"],
                event.data["email"],
                event.data.get("phone"),
                event.data.get("address"),
                json.dumps(event.data.get("emergency_contact", {})),
                json.dumps(event.data.get("medical_history", [])),
                json.dumps(event.data.get("allergies", [])),
                json.dumps(event.data.get("medications", [])),
                "active",
                event.timestamp,
                event.timestamp,
                event.version
            )

    async def _handle_patient_updated(self, event: Event):
        """Handle patient updated event"""
        updates = event.data.get("updates", {})
        update_fields = []
        params = []
        param_count = 1

        field_mapping = {
            "first_name": "first_name",
            "last_name": "last_name",
            "date_of_birth": "date_of_birth",
            "email": "email",
            "phone": "phone",
            "address": "address",
            "emergency_contact": "emergency_contact",
            "medical_history": "medical_history",
            "allergies": "allergies",
            "medications": "medications"
        }

        for field, value in updates.items():
            if field in field_mapping:
                update_fields.append(f"{field_mapping[field]} = ${param_count}")
                params.append(value if field not in ["emergency_contact", "medical_history", "allergies", "medications"] else json.dumps(value))
                param_count += 1

        if update_fields:
            update_fields.append(f"updated_at = ${param_count}")
            params.append(event.timestamp)
            param_count += 1

            update_fields.append(f"last_event_version = ${param_count}")
            params.append(event.version)

            query = f'''
                UPDATE patient_read_model
                SET {', '.join(update_fields)}
                WHERE patient_id = ${param_count}
            '''
            params.append(event.data["patient_id"])

            async with self.postgres_pool.acquire() as conn:
                await conn.execute(query, *params)

    async def _handle_patient_deleted(self, event: Event):
        """Handle patient deleted event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                UPDATE patient_read_model
                SET status = $1, updated_at = $2, last_event_version = $3
                WHERE patient_id = $4
            ''', "deleted", event.timestamp, event.version, event.data["patient_id"])

    async def _handle_patient_admitted(self, event: Event):
        """Handle patient admitted event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                UPDATE patient_read_model
                SET status = $1, admission_date = $2, updated_at = $3, last_event_version = $4
                WHERE patient_id = $5
            ''', "admitted", event.data["admission_date"], event.timestamp, event.version, event.data["patient_id"])

    async def _handle_patient_discharged(self, event: Event):
        """Handle patient discharged event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                UPDATE patient_read_model
                SET status = $1, discharge_date = $2, updated_at = $3, last_event_version = $4
                WHERE patient_id = $5
            ''', "discharged", event.data["discharge_date"], event.timestamp, event.version, event.data["patient_id"])

    # Appointment projection handlers
    async def _handle_appointment_created(self, event: Event):
        """Handle appointment created event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO appointment_read_model (
                    appointment_id, patient_id, provider_id, appointment_time,
                    duration, appointment_type, status, location, notes,
                    reminder_sent, created_at, updated_at, last_event_version
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ''',
                event.data["appointment_id"],
                event.data["patient_id"],
                event.data["provider_id"],
                event.data["appointment_time"],
                event.data["duration"],
                event.data.get("appointment_type", "general"),
                event.data.get("status", "scheduled"),
                event.data.get("location"),
                event.data.get("notes"),
                event.data.get("reminder_sent", False),
                event.timestamp,
                event.timestamp,
                event.version
            )

    async def _handle_appointment_updated(self, event: Event):
        """Handle appointment updated event"""
        updates = event.data.get("updates", {})
        update_fields = []
        params = []
        param_count = 1

        field_mapping = {
            "appointment_time": "appointment_time",
            "duration": "duration",
            "appointment_type": "appointment_type",
            "status": "status",
            "location": "location",
            "notes": "notes",
            "reminder_sent": "reminder_sent"
        }

        for field, value in updates.items():
            if field in field_mapping:
                update_fields.append(f"{field_mapping[field]} = ${param_count}")
                params.append(value)
                param_count += 1

        if update_fields:
            update_fields.append(f"updated_at = ${param_count}")
            params.append(event.timestamp)
            param_count += 1

            update_fields.append(f"last_event_version = ${param_count}")
            params.append(event.version)

            query = f'''
                UPDATE appointment_read_model
                SET {', '.join(update_fields)}
                WHERE appointment_id = ${param_count}
            '''
            params.append(event.data["appointment_id"])

            async with self.postgres_pool.acquire() as conn:
                await conn.execute(query, *params)

    async def _handle_appointment_cancelled(self, event: Event):
        """Handle appointment cancelled event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                UPDATE appointment_read_model
                SET status = $1, updated_at = $2, last_event_version = $3
                WHERE appointment_id = $4
            ''', "cancelled", event.timestamp, event.version, event.data["appointment_id"])

    async def _handle_appointment_completed(self, event: Event):
        """Handle appointment completed event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                UPDATE appointment_read_model
                SET status = $1, updated_at = $2, last_event_version = $3
                WHERE appointment_id = $4
            ''', "completed", event.timestamp, event.version, event.data["appointment_id"])

    # Clinical projection handlers
    async def _handle_clinical_note_created(self, event: Event):
        """Handle clinical note created event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO clinical_notes_read_model (
                    note_id, patient_id, provider_id, note_type, content,
                    created_at, updated_at, last_event_version
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ''',
                event.data["note_id"],
                event.data["patient_id"],
                event.data["provider_id"],
                event.data["note_type"],
                event.data["content"],
                event.timestamp,
                event.timestamp,
                event.version
            )

    async def _handle_prescription_created(self, event: Event):
        """Handle prescription created event"""
        # This would create a prescription record in the read model
        pass

    async def _handle_prescription_updated(self, event: Event):
        """Handle prescription updated event"""
        # This would update a prescription record in the read model
        pass

    async def _handle_prescription_cancelled(self, event: Event):
        """Handle prescription cancelled event"""
        # This would cancel a prescription record in the read model
        pass

    # Billing projection handlers
    async def _handle_bill_created(self, event: Event):
        """Handle bill created event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO billing_read_model (
                    bill_id, patient_id, total_amount, paid_amount, status,
                    created_at, updated_at, last_event_version
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ''',
                event.data["bill_id"],
                event.data["patient_id"],
                event.data["total_amount"],
                event.data.get("paid_amount", 0.00),
                event.data.get("status", "pending"),
                event.timestamp,
                event.timestamp,
                event.version
            )

    async def _handle_bill_updated(self, event: Event):
        """Handle bill updated event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                UPDATE billing_read_model
                SET total_amount = $1, paid_amount = $2, status = $3,
                    updated_at = $4, last_event_version = $5
                WHERE bill_id = $6
            ''',
                event.data.get("total_amount"),
                event.data.get("paid_amount", 0.00),
                event.data.get("status", "pending"),
                event.timestamp,
                event.version,
                event.data["bill_id"]
            )

    async def _handle_bill_paid(self, event: Event):
        """Handle bill paid event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                UPDATE billing_read_model
                SET paid_amount = $1, status = $2, updated_at = $3, last_event_version = $4
                WHERE bill_id = $5
            ''',
                event.data.get("paid_amount"),
                "paid",
                event.timestamp,
                event.version,
                event.data["bill_id"]
            )

    async def _handle_bill_cancelled(self, event: Event):
        """Handle bill cancelled event"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute('''
                UPDATE billing_read_model
                SET status = $1, updated_at = $2, last_event_version = $3
                WHERE bill_id = $4
            ''', "cancelled", event.timestamp, event.version, event.data["bill_id"])

    # Analytics projection handlers
    async def _handle_analytics_event(self, event: Event):
        """Handle analytics events"""
        # This would update analytics read models
        pass

# Global projector instance
projector: Optional[Projector] = None

async def get_projector() -> Projector:
    """Get the global projector instance"""
    global projector
    if projector is None:
        projector = Projector(
            postgres_url="postgresql://user:password@localhost/hms_projections",
            redis_url="redis://localhost:6379"
        )
        await projector.initialize()
    return projector

async def initialize_projections():
    """Initialize default projections"""
    projector_instance = await get_projector()

    # Create default projections
    await projector_instance.create_projection(
        ProjectionType.PATIENT_PROJECTION,
        "Patient Projection",
        "Patient data read model for efficient querying"
    )

    await projector_instance.create_projection(
        ProjectionType.APPOINTMENT_PROJECTION,
        "Appointment Projection",
        "Appointment data read model for efficient querying"
    )

    await projector_instance.create_projection(
        ProjectionType.CLINICAL_PROJECTION,
        "Clinical Projection",
        "Clinical data read model for efficient querying"
    )

    await projector_instance.create_projection(
        ProjectionType.BILLING_PROJECTION,
        "Billing Projection",
        "Billing data read model for efficient querying"
    )

    await projector_instance.create_projection(
        ProjectionType.ANALYTICS_PROJECTION,
        "Analytics Projection",
        "Analytics data read model for reporting and dashboards"
    )

    # Start all projections
    projections = await projector_instance.get_projections_by_type(ProjectionType.PATIENT_PROJECTION)
    for projection in projections:
        await projector_instance.start_projection(projection.id)

    projections = await projector_instance.get_projections_by_type(ProjectionType.APPOINTMENT_PROJECTION)
    for projection in projections:
        await projector_instance.start_projection(projection.id)