# Event Store Implementation
# Enterprise-grade event sourcing for HMS microservices

import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from abc import ABC, abstractmethod
import asyncpg
from redis.asyncio import Redis
import aioredis
from pydantic import BaseModel, Field
from fastapi import WebSocket, WebSocketDisconnect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventType(Enum):
    """Event types for HMS domain events"""
    # Patient events
    PATIENT_REGISTERED = "patient_registered"
    PATIENT_UPDATED = "patient_updated"
    PATIENT_DELETED = "patient_deleted"
    PATIENT_ADMITTED = "patient_admitted"
    PATIENT_DISCHARGED = "patient_discharged"

    # Appointment events
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_UPDATED = "appointment_updated"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_COMPLETED = "appointment_completed"

    # Clinical events
    CLINICAL_NOTE_CREATED = "clinical_note_created"
    PRESCRIPTION_CREATED = "prescription_created"
    PRESCRIPTION_UPDATED = "prescription_updated"
    PRESCRIPTION_CANCELLED = "prescription_cancelled"

    # Billing events
    BILL_CREATED = "bill_created"
    BILL_UPDATED = "bill_updated"
    BILL_PAID = "bill_paid"
    BILL_CANCELLED = "bill_cancelled"

    # Auth events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"

    # System events
    SERVICE_DEPLOYED = "service_deployed"
    SERVICE_UPDATED = "service_updated"
    CONFIGURATION_CHANGED = "configuration_changed"

class Event(BaseModel):
    """Base event model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    aggregate_id: str
    aggregate_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

class EventStoreInterface(ABC):
    """Abstract base class for event store implementations"""

    @abstractmethod
    async def save_event(self, event: Event) -> None:
        """Save an event to the store"""
        pass

    @abstractmethod
    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[Event]:
        """Get all events for an aggregate"""
        pass

    @abstractmethod
    async def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get all events of a specific type"""
        pass

    @abstractmethod
    async def get_events_by_time_range(self, start_time: datetime, end_time: datetime) -> List[Event]:
        """Get events within a time range"""
        pass

    @abstractmethod
    async def create_snapshot(self, aggregate_id: str, version: int, state: Dict[str, Any]) -> None:
        """Create a snapshot of an aggregate"""
        pass

    @abstractmethod
    async def get_snapshot(self, aggregate_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get a snapshot of an aggregate"""
        pass

class PostgresEventStore(EventStoreInterface):
    """PostgreSQL implementation of event store"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None

    async def initialize(self):
        """Initialize the event store"""
        self.pool = await asyncpg.create_pool(self.database_url)

        # Create tables
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id UUID PRIMARY KEY,
                    type VARCHAR(100) NOT NULL,
                    aggregate_id UUID NOT NULL,
                    aggregate_type VARCHAR(100) NOT NULL,
                    data JSONB NOT NULL,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    version INTEGER NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    user_id UUID,
                    correlation_id UUID,
                    causation_id UUID,
                    INDEX (aggregate_id),
                    INDEX (type),
                    INDEX (timestamp),
                    INDEX (user_id),
                    UNIQUE (aggregate_id, version)
                );
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS snapshots (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    aggregate_id UUID NOT NULL,
                    version INTEGER NOT NULL,
                    state JSONB NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    INDEX (aggregate_id),
                    INDEX (version),
                    UNIQUE (aggregate_id, version)
                );
            ''')

    async def save_event(self, event: Event) -> None:
        """Save an event to the store"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO events (
                    id, type, aggregate_id, aggregate_type, data, metadata,
                    version, timestamp, user_id, correlation_id, causation_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ''',
                event.id, event.type.value, event.aggregate_id, event.aggregate_type,
                json.dumps(event.data), json.dumps(event.metadata), event.version,
                event.timestamp, event.user_id, event.correlation_id, event.causation_id
            )

    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[Event]:
        """Get all events for an aggregate"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM events
                WHERE aggregate_id = $1 AND version >= $2
                ORDER BY version ASC
            ''', aggregate_id, from_version)

            return [
                Event(
                    id=str(row['id']),
                    type=EventType(row['type']),
                    aggregate_id=str(row['aggregate_id']),
                    aggregate_type=row['aggregate_type'],
                    data=json.loads(row['data']),
                    metadata=json.loads(row['metadata']),
                    version=row['version'],
                    timestamp=row['timestamp'],
                    user_id=str(row['user_id']) if row['user_id'] else None,
                    correlation_id=str(row['correlation_id']) if row['correlation_id'] else None,
                    causation_id=str(row['causation_id']) if row['causation_id'] else None
                ) for row in rows
            ]

    async def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get all events of a specific type"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM events
                WHERE type = $1
                ORDER BY timestamp DESC
            ''', event_type.value)

            return [
                Event(
                    id=str(row['id']),
                    type=EventType(row['type']),
                    aggregate_id=str(row['aggregate_id']),
                    aggregate_type=row['aggregate_type'],
                    data=json.loads(row['data']),
                    metadata=json.loads(row['metadata']),
                    version=row['version'],
                    timestamp=row['timestamp'],
                    user_id=str(row['user_id']) if row['user_id'] else None,
                    correlation_id=str(row['correlation_id']) if row['correlation_id'] else None,
                    causation_id=str(row['causation_id']) if row['causation_id'] else None
                ) for row in rows
            ]

    async def get_events_by_time_range(self, start_time: datetime, end_time: datetime) -> List[Event]:
        """Get events within a time range"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM events
                WHERE timestamp BETWEEN $1 AND $2
                ORDER BY timestamp DESC
            ''', start_time, end_time)

            return [
                Event(
                    id=str(row['id']),
                    type=EventType(row['type']),
                    aggregate_id=str(row['aggregate_id']),
                    aggregate_type=row['aggregate_type'],
                    data=json.loads(row['data']),
                    metadata=json.loads(row['metadata']),
                    version=row['version'],
                    timestamp=row['timestamp'],
                    user_id=str(row['user_id']) if row['user_id'] else None,
                    correlation_id=str(row['correlation_id']) if row['correlation_id'] else None,
                    causation_id=str(row['causation_id']) if row['causation_id'] else None
                ) for row in rows
            ]

    async def create_snapshot(self, aggregate_id: str, version: int, state: Dict[str, Any]) -> None:
        """Create a snapshot of an aggregate"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO snapshots (aggregate_id, version, state)
                VALUES ($1, $2, $3)
                ON CONFLICT (aggregate_id, version)
                DO UPDATE SET state = $3, timestamp = NOW()
            ''', aggregate_id, version, json.dumps(state))

    async def get_snapshot(self, aggregate_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get a snapshot of an aggregate"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT state FROM snapshots
                WHERE aggregate_id = $1 AND version <= $2
                ORDER BY version DESC
                LIMIT 1
            ''', aggregate_id, version)

            return json.loads(row['state']) if row else None

class RedisEventStore(EventStoreInterface):
    """Redis implementation of event store for real-time processing"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None

    async def initialize(self):
        """Initialize the event store"""
        self.redis = aioredis.from_url(self.redis_url, decode_responses=True)

    async def save_event(self, event: Event) -> None:
        """Save an event to Redis"""
        event_data = event.dict()
        event_data['type'] = event.type.value

        # Store in aggregate stream
        await self.redis.xadd(
            f"aggregate:{event.aggregate_id}",
            event_data,
            maxlen=10000
        )

        # Store in type stream
        await self.redis.xadd(
            f"type:{event.type.value}",
            event_data,
            maxlen=10000
        )

        # Store in global stream
        await self.redis.xadd(
            "events:global",
            event_data,
            maxlen=10000
        )

        # Set TTL for older events
        await self.redis.expire(f"aggregate:{event.aggregate_id}", 86400)  # 24 hours
        await self.redis.expire(f"type:{event.type.value}", 86400)

    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[Event]:
        """Get all events for an aggregate"""
        events = []
        try:
            stream = await self.redis.xread({f"aggregate:{aggregate_id}": "$"})
            for stream_key, messages in stream:
                for message_id, fields in messages:
                    if int(fields.get('version', 0)) >= from_version:
                        events.append(Event(
                            id=fields['id'],
                            type=EventType(fields['type']),
                            aggregate_id=fields['aggregate_id'],
                            aggregate_type=fields['aggregate_type'],
                            data=json.loads(fields['data']),
                            metadata=json.loads(fields.get('metadata', '{}')),
                            version=int(fields['version']),
                            timestamp=datetime.fromisoformat(fields['timestamp']),
                            user_id=fields.get('user_id'),
                            correlation_id=fields.get('correlation_id'),
                            causation_id=fields.get('causation_id')
                        ))
        except Exception as e:
            logger.error(f"Error getting events for aggregate {aggregate_id}: {e}")

        return sorted(events, key=lambda x: x.version)

    async def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get all events of a specific type"""
        events = []
        try:
            stream = await self.redis.xread({f"type:{event_type.value}": "$"})
            for stream_key, messages in stream:
                for message_id, fields in messages:
                    events.append(Event(
                        id=fields['id'],
                        type=EventType(fields['type']),
                        aggregate_id=fields['aggregate_id'],
                        aggregate_type=fields['aggregate_type'],
                        data=json.loads(fields['data']),
                        metadata=json.loads(fields.get('metadata', '{}')),
                        version=int(fields['version']),
                        timestamp=datetime.fromisoformat(fields['timestamp']),
                        user_id=fields.get('user_id'),
                        correlation_id=fields.get('correlation_id'),
                        causation_id=fields.get('causation_id')
                    ))
        except Exception as e:
            logger.error(f"Error getting events of type {event_type}: {e}")

        return sorted(events, key=lambda x: x.timestamp, reverse=True)

    async def get_events_by_time_range(self, start_time: datetime, end_time: datetime) -> List[Event]:
        """Get events within a time range"""
        events = []
        try:
            stream = await self.redis.xrange(
                "events:global",
                min=int(start_time.timestamp() * 1000),
                max=int(end_time.timestamp() * 1000)
            )
            for message_id, fields in stream:
                timestamp = datetime.fromisoformat(fields['timestamp'])
                if start_time <= timestamp <= end_time:
                    events.append(Event(
                        id=fields['id'],
                        type=EventType(fields['type']),
                        aggregate_id=fields['aggregate_id'],
                        aggregate_type=fields['aggregate_type'],
                        data=json.loads(fields['data']),
                        metadata=json.loads(fields.get('metadata', '{}')),
                        version=int(fields['version']),
                        timestamp=timestamp,
                        user_id=fields.get('user_id'),
                        correlation_id=fields.get('correlation_id'),
                        causation_id=fields.get('causation_id')
                    ))
        except Exception as e:
            logger.error(f"Error getting events by time range: {e}")

        return sorted(events, key=lambda x: x.timestamp, reverse=True)

    async def create_snapshot(self, aggregate_id: str, version: int, state: Dict[str, Any]) -> None:
        """Create a snapshot of an aggregate"""
        await self.redis.hset(
            f"snapshot:{aggregate_id}",
            str(version),
            json.dumps(state)
        )

    async def get_snapshot(self, aggregate_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get a snapshot of an aggregate"""
        try:
            snapshots = await self.redis.hgetall(f"snapshot:{aggregate_id}")
            for snapshot_version, state_data in snapshots.items():
                if int(snapshot_version) <= version:
                    return json.loads(state_data)
        except Exception as e:
            logger.error(f"Error getting snapshot for aggregate {aggregate_id}: {e}")

        return None

class EventPublisher:
    """Event publisher for broadcasting events"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
        self.websockets: List[WebSocket] = []

    async def initialize(self):
        """Initialize the publisher"""
        self.redis = aioredis.from_url(self.redis_url, decode_responses=True)

    async def publish_event(self, event: Event):
        """Publish an event to Redis and WebSocket clients"""
        event_data = event.dict()
        event_data['type'] = event.type.value

        # Publish to Redis pub/sub
        await self.redis.publish(f"events:{event.type.value}", json.dumps(event_data))
        await self.redis.publish("events:all", json.dumps(event_data))

        # Send to WebSocket clients
        await self.broadcast_to_websockets(event_data)

    async def broadcast_to_websockets(self, data: Dict[str, Any]):
        """Broadcast event data to WebSocket clients"""
        disconnected = []
        for websocket in self.websockets:
            try:
                await websocket.send_text(json.dumps(data))
            except WebSocketDisconnect:
                disconnected.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            self.websockets.remove(websocket)

    async def add_websocket(self, websocket: WebSocket):
        """Add a WebSocket client"""
        self.websockets.append(websocket)

    async def remove_websocket(self, websocket: WebSocket):
        """Remove a WebSocket client"""
        if websocket in self.websockets:
            self.websockets.remove(websocket)

class EventStore:
    """Main event store combining multiple implementations"""

    def __init__(self, postgres_url: str, redis_url: str):
        self.postgres_store = PostgresEventStore(postgres_url)
        self.redis_store = RedisEventStore(redis_url)
        self.publisher = EventPublisher(redis_url)

    async def initialize(self):
        """Initialize all components"""
        await self.postgres_store.initialize()
        await self.redis_store.initialize()
        await self.publisher.initialize()

    async def save_event(self, event: Event) -> None:
        """Save an event to all stores"""
        await self.postgres_store.save_event(event)
        await self.redis_store.save_event(event)
        await self.publisher.publish_event(event)

    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[Event]:
        """Get events from Redis first, fallback to PostgreSQL"""
        events = await self.redis_store.get_events(aggregate_id, from_version)
        if not events:
            events = await self.postgres_store.get_events(aggregate_id, from_version)
        return events

    async def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get events by type from Redis first, fallback to PostgreSQL"""
        events = await self.redis_store.get_events_by_type(event_type)
        if not events:
            events = await self.postgres_store.get_events_by_type(event_type)
        return events

    async def get_events_by_time_range(self, start_time: datetime, end_time: datetime) -> List[Event]:
        """Get events by time range from Redis first, fallback to PostgreSQL"""
        events = await self.redis_store.get_events_by_time_range(start_time, end_time)
        if not events:
            events = await self.postgres_store.get_events_by_time_range(start_time, end_time)
        return events

    async def create_snapshot(self, aggregate_id: str, version: int, state: Dict[str, Any]) -> None:
        """Create a snapshot in all stores"""
        await self.postgres_store.create_snapshot(aggregate_id, version, state)
        await self.redis_store.create_snapshot(aggregate_id, version, state)

    async def get_snapshot(self, aggregate_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get snapshot from Redis first, fallback to PostgreSQL"""
        snapshot = await self.redis_store.get_snapshot(aggregate_id, version)
        if not snapshot:
            snapshot = await self.postgres_store.get_snapshot(aggregate_id, version)
        return snapshot

# Global event store instance
event_store: Optional[EventStore] = None

async def get_event_store() -> EventStore:
    """Get the global event store instance"""
    global event_store
    if event_store is None:
        event_store = EventStore(
            postgres_url="postgresql://user:password@localhost/hms_events",
            redis_url="redis://localhost:6379"
        )
        await event_store.initialize()
    return event_store