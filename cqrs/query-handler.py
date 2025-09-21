# Query Handler Implementation
# Enterprise-grade query processing for HMS microservices

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Type, Union
from enum import Enum
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, status
import asyncpg
from redis.asyncio import Redis
import logging

from .event_store import Event, EventType, EventStore, get_event_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Query types for HMS read operations"""
    # Patient queries
    GET_PATIENT = "get_patient"
    GET_PATIENTS = "get_patients"
    GET_PATIENT_HISTORY = "get_patient_history"
    GET_PATIENT_APPOINTMENTS = "get_patient_appointments"
    GET_PATIENT_MEDICAL_RECORDS = "get_patient_medical_records"

    # Appointment queries
    GET_APPOINTMENT = "get_appointment"
    GET_APPOINTMENTS = "get_appointments"
    GET_APPOINTMENTS_BY_PROVIDER = "get_appointments_by_provider"
    GET_APPOINTMENTS_BY_DATE_RANGE = "get_appointments_by_date_range"
    GET_APPOINTMENTS_BY_STATUS = "get_appointments_by_status"

    # Clinical queries
    GET_CLINICAL_NOTES = "get_clinical_notes"
    GET_PRESCRIPTIONS = "get_prescriptions"
    GET_LAB_RESULTS = "get_lab_results"
    GET_RADIOLOGY_REPORTS = "get_radiology_reports"

    # Billing queries
    GET_BILL = "get_bill"
    GET_BILLS = "get_bills"
    GET_BILLS_BY_PATIENT = "get_bills_by_patient"
    GET_BILLS_BY_STATUS = "get_bills_by_status"
    GET_BILLING_SUMMARY = "get_billing_summary"

    # Analytics queries
    GET_SYSTEM_METRICS = "get_system_metrics"
    GET_USER_ACTIVITY = "get_user_activity"
    GET_SERVICE_UTILIZATION = "get_service_utilization"
    GET_REVENUE_REPORT = "get_revenue_report"

class Query(BaseModel):
    """Base query model"""
    id: str
    type: QueryType
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cache_key: Optional[str] = None
    cache_ttl: int = Field(default=300)  # 5 minutes

class QueryResult(BaseModel):
    """Query execution result"""
    query_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cached: bool = False
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_count: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None

class QueryHandler(ABC):
    """Abstract base class for query handlers"""

    @abstractmethod
    async def can_handle(self, query: Query) -> bool:
        """Check if this handler can process the query"""
        pass

    @abstractmethod
    async def handle(self, query: Query, event_store: EventStore) -> QueryResult:
        """Handle the query and return result"""
        pass

    @abstractmethod
    async def validate(self, query: Query) -> bool:
        """Validate the query"""
        pass

class ReadModel:
    """Base class for read models"""

    def __init__(self, postgres_url: str, redis_url: str):
        self.postgres_url = postgres_url
        self.redis_url = redis_url
        self.postgres_pool = None
        self.redis_client = None

    async def initialize(self):
        """Initialize the read model"""
        self.postgres_pool = await asyncpg.create_pool(self.postgres_url)
        self.redis_client = Redis.from_url(self.redis_url, decode_responses=True)

    async def create_tables(self):
        """Create read model tables"""
        async with self.postgres_pool.acquire() as conn:
            # Patient read model
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS patient_read_model (
                    id UUID PRIMARY KEY,
                    patient_id UUID UNIQUE NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    date_of_birth DATE NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    address TEXT,
                    emergency_contact JSONB,
                    medical_history JSONB DEFAULT '[]',
                    allergies JSONB DEFAULT '[]',
                    medications JSONB DEFAULT '[]',
                    status TEXT DEFAULT 'active',
                    admission_date TIMESTAMP,
                    discharge_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    last_event_version INTEGER DEFAULT 0
                );
            ''')

            # Appointment read model
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS appointment_read_model (
                    id UUID PRIMARY KEY,
                    appointment_id UUID UNIQUE NOT NULL,
                    patient_id UUID NOT NULL,
                    provider_id UUID NOT NULL,
                    appointment_time TIMESTAMP NOT NULL,
                    duration INTEGER NOT NULL,
                    appointment_type TEXT DEFAULT 'general',
                    status TEXT DEFAULT 'scheduled',
                    location TEXT,
                    notes TEXT,
                    reminder_sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    last_event_version INTEGER DEFAULT 0
                );
            ''')

            # Clinical notes read model
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS clinical_notes_read_model (
                    id UUID PRIMARY KEY,
                    note_id UUID UNIQUE NOT NULL,
                    patient_id UUID NOT NULL,
                    provider_id UUID NOT NULL,
                    note_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    last_event_version INTEGER DEFAULT 0
                );
            ''')

            # Billing read model
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS billing_read_model (
                    id UUID PRIMARY KEY,
                    bill_id UUID UNIQUE NOT NULL,
                    patient_id UUID NOT NULL,
                    total_amount DECIMAL(10,2) NOT NULL,
                    paid_amount DECIMAL(10,2) DEFAULT 0.00,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    last_event_version INTEGER DEFAULT 0
                );
            ''')

            # Analytics read model
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS analytics_read_model (
                    id UUID PRIMARY KEY,
                    metric_type TEXT NOT NULL,
                    metric_value DECIMAL(10,2) NOT NULL,
                    metric_date DATE NOT NULL,
                    additional_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            ''')

            # Create indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_patient_status ON patient_read_model(status);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_appointment_status ON appointment_read_model(status);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_appointment_time ON appointment_read_model(appointment_time);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_billing_status ON billing_read_model(status);')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_analytics_type_date ON analytics_read_model(metric_type, metric_date);')

class PatientQueryHandler(QueryHandler):
    """Handler for patient-related queries"""

    def __init__(self, read_model: ReadModel):
        self.read_model = read_model

    async def can_handle(self, query: Query) -> bool:
        """Check if this handler can process the query"""
        return query.type.value.startswith("get_patient")

    async def validate(self, query: Query) -> bool:
        """Validate the query"""
        if query.type == QueryType.GET_PATIENT:
            return "patient_id" in query.parameters
        elif query.type == QueryType.GET_PATIENTS:
            return True  # All parameters are optional
        elif query.type == QueryType.GET_PATIENT_HISTORY:
            return "patient_id" in query.parameters
        elif query.type == QueryType.GET_PATIENT_APPOINTMENTS:
            return "patient_id" in query.parameters
        elif query.type == QueryType.GET_PATIENT_MEDICAL_RECORDS:
            return "patient_id" in query.parameters
        return False

    async def handle(self, query: Query, event_store: EventStore) -> QueryResult:
        """Handle patient queries"""
        start_time = datetime.utcnow()

        try:
            if not await self.validate(query):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid query parameters"
                )

            # Check cache first
            if query.cache_key:
                cached_result = await self._get_cached_result(query.cache_key)
                if cached_result:
                    return QueryResult(
                        query_id=query.id,
                        data=cached_result,
                        cached=True,
                        processing_time=(datetime.utcnow() - start_time).total_seconds()
                    )

            result = None

            if query.type == QueryType.GET_PATIENT:
                result = await self._handle_get_patient(query)
            elif query.type == QueryType.GET_PATIENTS:
                result = await self._handle_get_patients(query)
            elif query.type == QueryType.GET_PATIENT_HISTORY:
                result = await self._handle_get_patient_history(query)
            elif query.type == QueryType.GET_PATIENT_APPOINTMENTS:
                result = await self._handle_get_patient_appointments(query)
            elif query.type == QueryType.GET_PATIENT_MEDICAL_RECORDS:
                result = await self._handle_get_patient_medical_records(query)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Cache the result
            if query.cache_key and result:
                await self._cache_result(query.cache_key, result, query.cache_ttl)

            return QueryResult(
                query_id=query.id,
                data=result,
                processing_time=processing_time,
                total_count=len(result) if isinstance(result, list) else 1
            )

        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error handling query {query.id}: {e}")

            return QueryResult(
                query_id=query.id,
                error=str(e),
                processing_time=processing_time
            )

    async def _handle_get_patient(self, query: Query) -> Optional[Dict[str, Any]]:
        """Handle get patient query"""
        patient_id = query.parameters["patient_id"]

        async with self.read_model.postgres_pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM patient_read_model
                WHERE patient_id = $1
            ''', patient_id)

            if not row:
                return None

            return dict(row)

    async def _handle_get_patients(self, query: Query) -> List[Dict[str, Any]]:
        """Handle get patients query"""
        page = query.parameters.get("page", 1)
        page_size = query.parameters.get("page_size", 20)
        offset = (page - 1) * page_size
        status = query.parameters.get("status")
        search_term = query.parameters.get("search")

        query_parts = ["SELECT * FROM patient_read_model"]
        params = []
        conditions = []

        if status:
            conditions.append("status = $1")
            params.append(status)

        if search_term:
            conditions.append("(first_name ILIKE $" + str(len(params) + 1) + " OR last_name ILIKE $" + str(len(params) + 2) + " OR email ILIKE $" + str(len(params) + 3) + ")")
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))

        query_parts.append("ORDER BY last_name, first_name")
        query_parts.append(f"LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}")
        params.extend([page_size, offset])

        async with self.read_model.postgres_pool.acquire() as conn:
            rows = await conn.fetch(' '.join(query_parts), *params)
            return [dict(row) for row in rows]

    async def _handle_get_patient_history(self, query: Query) -> List[Dict[str, Any]]:
        """Handle get patient history query"""
        patient_id = query.parameters["patient_id"]

        # Get events from event store
        events = await event_store.get_events(patient_id)

        return [
            {
                "event_id": event.id,
                "event_type": event.type.value,
                "timestamp": event.timestamp,
                "data": event.data,
                "user_id": event.user_id
            }
            for event in events
        ]

    async def _handle_get_patient_appointments(self, query: Query) -> List[Dict[str, Any]]:
        """Handle get patient appointments query"""
        patient_id = query.parameters["patient_id"]
        status = query.parameters.get("status")

        async with self.read_model.postgres_pool.acquire() as conn:
            query_parts = ["SELECT * FROM appointment_read_model WHERE patient_id = $1"]
            params = [patient_id]

            if status:
                query_parts.append("AND status = $2")
                params.append(status)

            query_parts.append("ORDER BY appointment_time DESC")

            rows = await conn.fetch(' '.join(query_parts), *params)
            return [dict(row) for row in rows]

    async def _handle_get_patient_medical_records(self, query: Query) -> List[Dict[str, Any]]:
        """Handle get patient medical records query"""
        patient_id = query.parameters["patient_id"]

        async with self.read_model.postgres_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM clinical_notes_read_model
                WHERE patient_id = $1
                ORDER BY created_at DESC
            ''', patient_id)

            return [dict(row) for row in rows]

    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result from Redis"""
        try:
            cached_data = await self.read_model.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error getting cached result: {e}")
        return None

    async def _cache_result(self, cache_key: str, data: Dict[str, Any], ttl: int):
        """Cache result in Redis"""
        try:
            await self.read_model.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Error caching result: {e}")

class AppointmentQueryHandler(QueryHandler):
    """Handler for appointment-related queries"""

    def __init__(self, read_model: ReadModel):
        self.read_model = read_model

    async def can_handle(self, query: Query) -> bool:
        """Check if this handler can process the query"""
        return query.type.value.startswith("get_appointment")

    async def validate(self, query: Query) -> bool:
        """Validate the query"""
        if query.type == QueryType.GET_APPOINTMENT:
            return "appointment_id" in query.parameters
        elif query.type == QueryType.GET_APPOINTMENTS:
            return True  # All parameters are optional
        elif query.type == QueryType.GET_APPOINTMENTS_BY_PROVIDER:
            return "provider_id" in query.parameters
        elif query.type == QueryType.GET_APPOINTMENTS_BY_DATE_RANGE:
            return "start_date" in query.parameters and "end_date" in query.parameters
        elif query.type == QueryType.GET_APPOINTMENTS_BY_STATUS:
            return "status" in query.parameters
        return False

    async def handle(self, query: Query, event_store: EventStore) -> QueryResult:
        """Handle appointment queries"""
        start_time = datetime.utcnow()

        try:
            if not await self.validate(query):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid query parameters"
                )

            # Check cache first
            if query.cache_key:
                cached_result = await self._get_cached_result(query.cache_key)
                if cached_result:
                    return QueryResult(
                        query_id=query.id,
                        data=cached_result,
                        cached=True,
                        processing_time=(datetime.utcnow() - start_time).total_seconds()
                    )

            result = None

            if query.type == QueryType.GET_APPOINTMENT:
                result = await self._handle_get_appointment(query)
            elif query.type == QueryType.GET_APPOINTMENTS:
                result = await self._handle_get_appointments(query)
            elif query.type == QueryType.GET_APPOINTMENTS_BY_PROVIDER:
                result = await self._handle_get_appointments_by_provider(query)
            elif query.type == QueryType.GET_APPOINTMENTS_BY_DATE_RANGE:
                result = await self._handle_get_appointments_by_date_range(query)
            elif query.type == QueryType.GET_APPOINTMENTS_BY_STATUS:
                result = await self._handle_get_appointments_by_status(query)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Cache the result
            if query.cache_key and result:
                await self._cache_result(query.cache_key, result, query.cache_ttl)

            return QueryResult(
                query_id=query.id,
                data=result,
                processing_time=processing_time,
                total_count=len(result) if isinstance(result, list) else 1
            )

        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error handling query {query.id}: {e}")

            return QueryResult(
                query_id=query.id,
                error=str(e),
                processing_time=processing_time
            )

    async def _handle_get_appointment(self, query: Query) -> Optional[Dict[str, Any]]:
        """Handle get appointment query"""
        appointment_id = query.parameters["appointment_id"]

        async with self.read_model.postgres_pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM appointment_read_model
                WHERE appointment_id = $1
            ''', appointment_id)

            if not row:
                return None

            return dict(row)

    async def _handle_get_appointments(self, query: Query) -> List[Dict[str, Any]]:
        """Handle get appointments query"""
        page = query.parameters.get("page", 1)
        page_size = query.parameters.get("page_size", 20)
        offset = (page - 1) * page_size
        status = query.parameters.get("status")

        query_parts = ["SELECT * FROM appointment_read_model"]
        params = []
        conditions = []

        if status:
            conditions.append("status = $1")
            params.append(status)

        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))

        query_parts.append("ORDER BY appointment_time DESC")
        query_parts.append(f"LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}")
        params.extend([page_size, offset])

        async with self.read_model.postgres_pool.acquire() as conn:
            rows = await conn.fetch(' '.join(query_parts), *params)
            return [dict(row) for row in rows]

    async def _handle_get_appointments_by_provider(self, query: Query) -> List[Dict[str, Any]]:
        """Handle get appointments by provider query"""
        provider_id = query.parameters["provider_id"]
        start_date = query.parameters.get("start_date")
        end_date = query.parameters.get("end_date")

        async with self.read_model.postgres_pool.acquire() as conn:
            query_parts = ["SELECT * FROM appointment_read_model WHERE provider_id = $1"]
            params = [provider_id]

            if start_date and end_date:
                query_parts.append("AND appointment_time BETWEEN $2 AND $3")
                params.extend([start_date, end_date])

            query_parts.append("ORDER BY appointment_time ASC")

            rows = await conn.fetch(' '.join(query_parts), *params)
            return [dict(row) for row in rows]

    async def _handle_get_appointments_by_date_range(self, query: Query) -> List[Dict[str, Any]]:
        """Handle get appointments by date range query"""
        start_date = query.parameters["start_date"]
        end_date = query.parameters["end_date"]

        async with self.read_model.postgres_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM appointment_read_model
                WHERE appointment_time BETWEEN $1 AND $2
                ORDER BY appointment_time ASC
            ''', start_date, end_date)

            return [dict(row) for row in rows]

    async def _handle_get_appointments_by_status(self, query: Query) -> List[Dict[str, Any]]:
        """Handle get appointments by status query"""
        status = query.parameters["status"]

        async with self.read_model.postgres_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM appointment_read_model
                WHERE status = $1
                ORDER BY appointment_time ASC
            ''', status)

            return [dict(row) for row in rows]

    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result from Redis"""
        try:
            cached_data = await self.read_model.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error getting cached result: {e}")
        return None

    async def _cache_result(self, cache_key: str, data: Dict[str, Any], ttl: int):
        """Cache result in Redis"""
        try:
            await self.read_model.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Error caching result: {e}")

class AnalyticsQueryHandler(QueryHandler):
    """Handler for analytics queries"""

    def __init__(self, read_model: ReadModel):
        self.read_model = read_model

    async def can_handle(self, query: Query) -> bool:
        """Check if this handler can process the query"""
        return query.type.value.startswith("get_") and any(
            metric in query.type.value for metric in ["system", "user", "service", "revenue"]
        )

    async def validate(self, query: Query) -> bool:
        """Validate the query"""
        if query.type == QueryType.GET_SYSTEM_METRICS:
            return True
        elif query.type == QueryType.GET_USER_ACTIVITY:
            return True
        elif query.type == QueryType.GET_SERVICE_UTILIZATION:
            return True
        elif query.type == QueryType.GET_REVENUE_REPORT:
            return "start_date" in query.parameters and "end_date" in query.parameters
        return False

    async def handle(self, query: Query, event_store: EventStore) -> QueryResult:
        """Handle analytics queries"""
        start_time = datetime.utcnow()

        try:
            if not await self.validate(query):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid query parameters"
                )

            result = None

            if query.type == QueryType.GET_SYSTEM_METRICS:
                result = await self._handle_get_system_metrics(query)
            elif query.type == QueryType.GET_USER_ACTIVITY:
                result = await self._handle_get_user_activity(query)
            elif query.type == QueryType.GET_SERVICE_UTILIZATION:
                result = await self._handle_get_service_utilization(query)
            elif query.type == QueryType.GET_REVENUE_REPORT:
                result = await self._handle_get_revenue_report(query)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return QueryResult(
                query_id=query.id,
                data=result,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error handling query {query.id}: {e}")

            return QueryResult(
                query_id=query.id,
                error=str(e),
                processing_time=processing_time
            )

    async def _handle_get_system_metrics(self, query: Query) -> Dict[str, Any]:
        """Handle get system metrics query"""
        async with self.read_model.postgres_pool.acquire() as conn:
            # Get patient count
            patient_count = await conn.fetchval('SELECT COUNT(*) FROM patient_read_model WHERE status = $1', 'active')

            # Get appointment count
            appointment_count = await conn.fetchval('SELECT COUNT(*) FROM appointment_read_model')

            # Get billing summary
            total_billed = await conn.fetchval('SELECT COALESCE(SUM(total_amount), 0) FROM billing_read_model')
            total_paid = await conn.fetchval('SELECT COALESCE(SUM(paid_amount), 0) FROM billing_read_model')

            return {
                "total_patients": patient_count,
                "total_appointments": appointment_count,
                "total_billed": float(total_billed),
                "total_paid": float(total_paid),
                "outstanding_balance": float(total_billed - total_paid),
                "generated_at": datetime.utcnow().isoformat()
            }

    async def _handle_get_user_activity(self, query: Query) -> List[Dict[str, Any]]:
        """Handle get user activity query"""
        # This would typically query the audit log or user activity events
        # For now, return a mock implementation
        return []

    async def _handle_get_service_utilization(self, query: Query) -> Dict[str, Any]:
        """Handle get service utilization query"""
        async with self.read_model.postgres_pool.acquire() as conn:
            # Get appointment utilization by type
            appointment_types = await conn.fetch('''
                SELECT appointment_type, COUNT(*) as count
                FROM appointment_read_model
                GROUP BY appointment_type
            ''')

            # Get appointment status distribution
            appointment_status = await conn.fetch('''
                SELECT status, COUNT(*) as count
                FROM appointment_read_model
                GROUP BY status
            ''')

            return {
                "appointment_types": [
                    {"type": row["appointment_type"], "count": row["count"]}
                    for row in appointment_types
                ],
                "appointment_status": [
                    {"status": row["status"], "count": row["count"]}
                    for row in appointment_status
                ],
                "generated_at": datetime.utcnow().isoformat()
            }

    async def _handle_get_revenue_report(self, query: Query) -> Dict[str, Any]:
        """Handle get revenue report query"""
        start_date = query.parameters["start_date"]
        end_date = query.parameters["end_date"]

        async with self.read_model.postgres_pool.acquire() as conn:
            # Get revenue for the period
            revenue_data = await conn.fetch('''
                SELECT
                    DATE(created_at) as date,
                    SUM(total_amount) as total_billed,
                    SUM(paid_amount) as total_paid,
                    COUNT(*) as bill_count
                FROM billing_read_model
                WHERE created_at BETWEEN $1 AND $2
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', start_date, end_date)

            return {
                "revenue_data": [
                    {
                        "date": row["date"],
                        "total_billed": float(row["total_billed"]),
                        "total_paid": float(row["total_paid"]),
                        "bill_count": row["bill_count"]
                    }
                    for row in revenue_data
                ],
                "summary": {
                    "total_billed": sum(float(row["total_billed"]) for row in revenue_data),
                    "total_paid": sum(float(row["total_paid"]) for row in revenue_data),
                    "total_bills": sum(row["bill_count"] for row in revenue_data)
                },
                "period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "generated_at": datetime.utcnow().isoformat()
            }

class QueryDispatcher:
    """Query dispatcher for routing queries to appropriate handlers"""

    def __init__(self, read_model: ReadModel):
        self.handlers: List[QueryHandler] = []
        self.read_model = read_model

    def register_handler(self, handler: QueryHandler):
        """Register a query handler"""
        self.handlers.append(handler)

    async def dispatch(self, query: Query) -> QueryResult:
        """Dispatch a query to the appropriate handler"""
        for handler in self.handlers:
            if await handler.can_handle(query):
                event_store = await get_event_store()
                return await handler.handle(query, event_store)

        return QueryResult(
            query_id=query.id,
            error=f"No handler found for query type: {query.type}",
            processing_time=0.0
        )

# Initialize read model and query handlers
read_model = ReadModel(
    postgres_url="postgresql://user:password@localhost/hms_read_models",
    redis_url="redis://localhost:6379"
)

query_dispatcher = QueryDispatcher(read_model)
query_dispatcher.register_handler(PatientQueryHandler(read_model))
query_dispatcher.register_handler(AppointmentQueryHandler(read_model))
query_dispatcher.register_handler(AnalyticsQueryHandler(read_model))

async def initialize_read_model():
    """Initialize the read model"""
    await read_model.initialize()
    await read_model.create_tables()

async def dispatch_query(query: Query) -> QueryResult:
    """Dispatch a query using the global dispatcher"""
    return await query_dispatcher.dispatch(query)