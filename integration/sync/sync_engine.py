"""
sync_engine module
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import aiofiles
import aiohttp
import asyncpg
import redis.asyncio as redis
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from ..orchestrator import IntegrationOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Base = declarative_base()


class SyncEventType(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    BULK_CREATE = "BULK_CREATE"
    BULK_UPDATE = "BULK_UPDATE"
    BULK_DELETE = "BULK_DELETE"
    SYNC_COMPLETE = "SYNC_COMPLETE"
    SYNC_FAILED = "SYNC_FAILED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    DATA_VALIDATION_FAILED = "DATA_VALIDATION_FAILED"


class SyncEntityType(Enum):
    PATIENT = "PATIENT"
    PRACTITIONER = "PRACTITIONER"
    ENCOUNTER = "ENCOUNTER"
    OBSERVATION = "OBSERVATION"
    MEDICATION = "MEDICATION"
    ALLERGY = "ALLERGY"
    CONDITION = "CONDITION"
    PROCEDURE = "PROCEDURE"
    IMMUNIZATION = "IMMUNIZATION"
    DIAGNOSTIC_REPORT = "DIAGNOSTIC_REPORT"
    APPOINTMENT = "APPOINTMENT"
    BILLING_CLAIM = "BILLING_CLAIM"
    INSURANCE = "INSURANCE"
    PHARMACY_ORDER = "PHARMACY_ORDER"
    LAB_RESULT = "LAB_RESULT"
    RADIOLOGY_ORDER = "RADIOLOGY_ORDER"
    FACILITY = "FACILITY"
    DEPARTMENT = "DEPARTMENT"
    USER = "USER"
    ROLE = "ROLE"
    PERMISSION = "PERMISSION"


class SyncStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"
    CONFLICT = "CONFLICT"


class ConflictResolutionStrategy(Enum):
    SOURCE_WINS = "SOURCE_WINS"
    TARGET_WINS = "TARGET_WINS"
    MERGE = "MERGE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    TIMESTAMP_BASED = "TIMESTAMP_BASED"
    FIELD_LEVEL_MERGE = "FIELD_LEVEL_MERGE"


@dataclass
class SyncEvent:
    event_id: str
    event_type: SyncEventType
    entity_type: SyncEntityType
    entity_id: str
    source_system: str
    target_systems: List[str]
    data: Dict
    metadata: Dict
    timestamp: datetime
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    conflict_resolution: ConflictResolutionStrategy = (
        ConflictResolutionStrategy.SOURCE_WINS
    )


@dataclass
class SyncResult:
    event_id: str
    status: SyncStatus
    success_count: int = 0
    failure_count: int = 0
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    conflicts_detected: List[Dict] = field(default_factory=list)


class SyncSubscription(Base):
    __tablename__ = "sync_subscriptions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(100), nullable=False, index=True)
    entity_types = Column(JSON)
    filters = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class SyncEventLog(Base):
    __tablename__ = "sync_event_log"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(20), nullable=False)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    source_system = Column(String(100), nullable=False)
    target_systems = Column(JSON)
    data = Column(JSON, nullable=False)
    metadata = Column(JSON)
    status = Column(String(20), nullable=False)
    processing_time = Column(Float)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)


class SyncConflict(Base):
    __tablename__ = "sync_conflicts"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    source_data = Column(JSON, nullable=False)
    target_data = Column(JSON, nullable=False)
    conflict_type = Column(String(50), nullable=False)
    resolution_strategy = Column(String(50))
    resolved_data = Column(JSON)
    resolution_status = Column(String(20), default="PENDING")
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class SyncMetrics(Base):
    __tablename__ = "sync_metrics"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_system = Column(String(100), nullable=False)
    target_system = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    event_type = Column(String(20), nullable=False)
    total_events = Column(Integer, default=0)
    successful_events = Column(Integer, default=0)
    failed_events = Column(Integer, default=0)
    avg_processing_time = Column(Float, default=0.0)
    last_event_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataSynchronizer:
    def __init__(self, orchestrator: IntegrationOrchestrator):
        self.orchestrator = orchestrator
        self.redis_client: Optional[redis.Redis] = None
        self.db_url = os.getenv(
            "SYNC_DB_URL", "postgresql+asyncpg://hms:hms@localhost:5432/sync"
        )
        self.engine = create_async_engine(self.db_url)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.event_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        self.conflict_queue = asyncio.Queue()
        self.entity_handlers: Dict[SyncEntityType, Callable] = {}
        self.conflict_resolvers: Dict[ConflictResolutionStrategy, Callable] = {}
        self.active_connections: List[WebSocket] = []
        self.metrics_cache = {}
        self._initialize_handlers()
        self._initialize_conflict_resolvers()

    async def initialize(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        asyncio.create_task(self._event_processor())
        asyncio.create_task(self._result_processor())
        asyncio.create_task(self._conflict_processor())
        asyncio.create_task(self._metrics_collector())
        asyncio.create_task(self._cleanup_task())
        logger.info("Data Synchronization Engine initialized successfully")

    def _initialize_handlers(self):
        self.entity_handlers[SyncEntityType.PATIENT] = self._handle_patient_sync
        self.entity_handlers[SyncEntityType.ENCOUNTER] = self._handle_encounter_sync
        self.entity_handlers[SyncEntityType.OBSERVATION] = self._handle_observation_sync
        self.entity_handlers[SyncEntityType.MEDICATION] = self._handle_medication_sync
        self.entity_handlers[SyncEntityType.ALLERGY] = self._handle_allergy_sync
        self.entity_handlers[SyncEntityType.CONDITION] = self._handle_condition_sync
        self.entity_handlers[SyncEntityType.PROCEDURE] = self._handle_procedure_sync
        self.entity_handlers[SyncEntityType.APPOINTMENT] = self._handle_appointment_sync
        self.entity_handlers[SyncEntityType.BILLING_CLAIM] = self._handle_billing_sync
        self.entity_handlers[SyncEntityType.LAB_RESULT] = self._handle_lab_result_sync
        self.entity_handlers[SyncEntityType.RADIOLOGY_ORDER] = (
            self._handle_radiology_sync
        )

    def _initialize_conflict_resolvers(self):
        self.conflict_resolvers[ConflictResolutionStrategy.SOURCE_WINS] = (
            self._resolve_source_wins
        )
        self.conflict_resolvers[ConflictResolutionStrategy.TARGET_WINS] = (
            self._resolve_target_wins
        )
        self.conflict_resolvers[ConflictResolutionStrategy.MERGE] = self._resolve_merge
        self.conflict_resolvers[ConflictResolutionStrategy.TIMESTAMP_BASED] = (
            self._resolve_timestamp_based
        )
        self.conflict_resolvers[ConflictResolutionStrategy.FIELD_LEVEL_MERGE] = (
            self._resolve_field_level_merge
        )

    async def publish_event(self, event: SyncEvent) -> str:
        try:
            await self._validate_event(event)
            await self.event_queue.put(event)
            if self.redis_client:
                await self.redis_client.setex(
                    f"sync_event:{event.event_id}",
                    3600,
                    json.dumps(
                        {
                            "event_type": event.event_type.value,
                            "entity_type": event.entity_type.value,
                            "entity_id": event.entity_id,
                            "source_system": event.source_system,
                            "timestamp": event.timestamp.isoformat(),
                        }
                    ),
                )
            await self._log_event(event, SyncStatus.PENDING)
            logger.info(
                f"Published sync event: {event.event_id} - {event.event_type.value} {event.entity_type.value}"
            )
            return event.event_id
        except Exception as e:
            logger.error(f"Error publishing sync event: {e}")
            raise

    async def _validate_event(self, event: SyncEvent):
        if not event.event_id:
            raise ValueError("Event ID is required")
        if not event.entity_id:
            raise ValueError("Entity ID is required")
        if not event.source_system:
            raise ValueError("Source system is required")
        if not event.target_systems:
            raise ValueError("At least one target system is required")
        if event.retry_count > event.max_retries:
            raise ValueError("Retry count exceeds maximum retries")
        await self._validate_entity_data(event.entity_type, event.data)

    async def _validate_entity_data(self, entity_type: SyncEntityType, data: Dict):
        required_fields = {
            SyncEntityType.PATIENT: ["first_name", "last_name", "date_of_birth"],
            SyncEntityType.ENCOUNTER: ["patient_id", "encounter_type", "start_date"],
            SyncEntityType.OBSERVATION: ["patient_id", "observation_type", "value"],
            SyncEntityType.MEDICATION: ["patient_id", "medication_name", "dosage"],
            SyncEntityType.APPOINTMENT: ["patient_id", "provider_id", "start_time"],
        }
        if entity_type in required_fields:
            for field in required_fields[entity_type]:
                if field not in data:
                    raise ValueError(
                        f"Required field '{field}' missing for {entity_type.value}"
                    )

    async def _event_processor(self):
        while True:
            try:
                event = await self.event_queue.get()
                logger.info(f"Processing event: {event.event_id}")
                result = await self._process_event(event)
                await self.result_queue.put((event, result))
                await self._broadcast_event_update(event, result)
            except Exception as e:
                logger.error(f"Error in event processor: {e}")

    async def _process_event(self, event: SyncEvent) -> SyncResult:
        start_time = time.time()
        result = SyncResult(event_id=event.event_id, status=SyncStatus.PROCESSING)
        try:
            handler = self.entity_handlers.get(event.entity_type)
            if not handler:
                raise ValueError(f"No handler registered for {event.entity_type.value}")
            for target_system in event.target_systems:
                try:
                    await handler(event, target_system)
                    result.success_count += 1
                except Exception as e:
                    result.failure_count += 1
                    result.errors.append(
                        f"Failed to sync with {target_system}: {str(e)}"
                    )
            if result.failure_count == 0:
                result.status = SyncStatus.COMPLETED
            elif result.success_count > 0:
                result.status = SyncStatus.COMPLETED
            else:
                result.status = SyncStatus.FAILED
            result.processing_time = time.time() - start_time
        except Exception as e:
            result.status = SyncStatus.FAILED
            result.processing_time = time.time() - start_time
            result.errors.append(f"Processing failed: {str(e)}")
        return result

    async def _handle_patient_sync(self, event: SyncEvent, target_system: str):
        if event.event_type == SyncEventType.CREATE:
            await self._sync_patient_create(event, target_system)
        elif event.event_type == SyncEventType.UPDATE:
            await self._sync_patient_update(event, target_system)
        elif event.event_type == SyncEventType.DELETE:
            await self._sync_patient_delete(event, target_system)

    async def _handle_encounter_sync(self, event: SyncEvent, target_system: str):
        pass

    async def _handle_observation_sync(self, event: SyncEvent, target_system: str):
        pass

    async def _handle_medication_sync(self, event: SyncEvent, target_system: str):
        pass

    async def _handle_appointment_sync(self, event: SyncEvent, target_system: str):
        pass

    async def _sync_patient_create(self, event: SyncEvent, target_system: str):
        exists = await self._check_entity_exists(
            target_system, event.entity_type, event.entity_id
        )
        if exists:
            conflict = await self._detect_conflict(
                event, target_system, "Patient already exists"
            )
            if conflict:
                await self._handle_conflict(event, target_system, conflict)
        else:
            await self._create_entity_in_target(
                target_system, event.entity_type, event.data
            )

    async def _sync_patient_update(self, event: SyncEvent, target_system: str):
        target_version = await self._get_entity_version(
            target_system, event.entity_type, event.entity_id
        )
        source_version = event.metadata.get("version")
        if target_version and target_version != source_version:
            conflict = await self._detect_conflict(
                event, target_system, "Version mismatch"
            )
            if conflict:
                await self._handle_conflict(event, target_system, conflict)
        else:
            await self._update_entity_in_target(
                target_system, event.entity_type, event.entity_id, event.data
            )

    async def _sync_patient_delete(self, event: SyncEvent, target_system: str):
        await self._delete_entity_in_target(
            target_system, event.entity_type, event.entity_id
        )

    async def _check_entity_exists(
        self, target_system: str, entity_type: SyncEntityType, entity_id: str
    ) -> bool:
        try:
            integration_config = self.orchestrator.integrations.get(target_system)
            if not integration_config:
                raise ValueError(f"Integration '{target_system}' not found")
            response = await self.orchestrator.execute_integration_request(
                target_system, "GET", f"/api/{entity_type.value.lower()}/{entity_id}"
            )
            return response.get("status") == "success"
        except Exception as e:
            logger.warning(f"Error checking entity existence: {e}")
            return False

    async def _get_entity_version(
        self, target_system: str, entity_type: SyncEntityType, entity_id: str
    ) -> Optional[str]:
        try:
            response = await self.orchestrator.execute_integration_request(
                target_system,
                "GET",
                f"/api/{entity_type.value.lower()}/{entity_id}/version",
            )
            return response.get("version")
        except Exception as e:
            logger.warning(f"Error getting entity version: {e}")
            return None

    async def _create_entity_in_target(
        self, target_system: str, entity_type: SyncEntityType, data: Dict
    ):
        await self.orchestrator.execute_integration_request(
            target_system, "POST", f"/api/{entity_type.value.lower()}", data=data
        )

    async def _update_entity_in_target(
        self,
        target_system: str,
        entity_type: SyncEntityType,
        entity_id: str,
        data: Dict,
    ):
        await self.orchestrator.execute_integration_request(
            target_system,
            "PUT",
            f"/api/{entity_type.value.lower()}/{entity_id}",
            data=data,
        )

    async def _delete_entity_in_target(
        self, target_system: str, entity_type: SyncEntityType, entity_id: str
    ):
        await self.orchestrator.execute_integration_request(
            target_system, "DELETE", f"/api/{entity_type.value.lower()}/{entity_id}"
        )

    async def _detect_conflict(
        self, event: SyncEvent, target_system: str, conflict_type: str
    ) -> Optional[Dict]:
        conflict = {
            "event_id": event.event_id,
            "entity_type": event.entity_type.value,
            "entity_id": event.entity_id,
            "target_system": target_system,
            "conflict_type": conflict_type,
            "source_data": event.data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.conflict_queue.put(conflict)
        return conflict

    async def _handle_conflict(
        self, event: SyncEvent, target_system: str, conflict: Dict
    ):
        resolver = self.conflict_resolvers.get(event.conflict_resolution)
        if resolver:
            await resolver(event, target_system, conflict)
        else:
            logger.warning(
                f"No conflict resolver for {event.conflict_resolution.value}"
            )

    async def _resolve_source_wins(
        self, event: SyncEvent, target_system: str, conflict: Dict
    ):
        if event.event_type == SyncEventType.UPDATE:
            await self._update_entity_in_target(
                target_system, event.entity_type, event.entity_id, event.data
            )
        elif event.event_type == SyncEventType.CREATE:
            await self._create_entity_in_target(
                target_system, event.entity_type, event.data
            )

    async def _resolve_target_wins(
        self, event: SyncEvent, target_system: str, conflict: Dict
    ):
        pass

    async def _resolve_merge(
        self, event: SyncEvent, target_system: str, conflict: Dict
    ):
        target_data = await self._get_entity_data(
            target_system, event.entity_type, event.entity_id
        )
        merged_data = {**target_data, **event.data}
        await self._update_entity_in_target(
            target_system, event.entity_type, event.entity_id, merged_data
        )

    async def _resolve_timestamp_based(
        self, event: SyncEvent, target_system: str, conflict: Dict
    ):
        source_timestamp = event.metadata.get("updated_at")
        target_timestamp = await self._get_entity_timestamp(
            target_system, event.entity_type, event.entity_id
        )
        if source_timestamp and target_timestamp:
            if source_timestamp > target_timestamp:
                await self._resolve_source_wins(event, target_system, conflict)
            else:
                await self._resolve_target_wins(event, target_system, conflict)

    async def _resolve_field_level_merge(
        self, event: SyncEvent, target_system: str, conflict: Dict
    ):
        pass

    async def _get_entity_data(
        self, target_system: str, entity_type: SyncEntityType, entity_id: str
    ) -> Dict:
        response = await self.orchestrator.execute_integration_request(
            target_system, "GET", f"/api/{entity_type.value.lower()}/{entity_id}"
        )
        return response.get("data", {})

    async def _get_entity_timestamp(
        self, target_system: str, entity_type: SyncEntityType, entity_id: str
    ) -> Optional[datetime]:
        response = await self.orchestrator.execute_integration_request(
            target_system,
            "GET",
            f"/api/{entity_type.value.lower()}/{entity_id}/timestamp",
        )
        timestamp_str = response.get("timestamp")
        if timestamp_str:
            return datetime.fromisoformat(timestamp_str)
        return None

    async def _result_processor(self):
        while True:
            try:
                event, result = await self.result_queue.get()
                await self._log_event_result(event, result)
                await self._update_metrics(event, result)
                if self.redis_client:
                    await self.redis_client.setex(
                        f"sync_result:{event.event_id}",
                        3600,
                        json.dumps(
                            {
                                "status": result.status.value,
                                "success_count": result.success_count,
                                "failure_count": result.failure_count,
                                "processing_time": result.processing_time,
                            }
                        ),
                    )
            except Exception as e:
                logger.error(f"Error in result processor: {e}")

    async def _conflict_processor(self):
        while True:
            try:
                conflict = await self.conflict_queue.get()
                async with self.SessionLocal() as session:
                    conflict_log = SyncConflict(
                        event_id=conflict["event_id"],
                        entity_type=conflict["entity_type"],
                        entity_id=conflict["entity_id"],
                        source_data=conflict["source_data"],
                        target_data=conflict.get("target_data", {}),
                        conflict_type=conflict["conflict_type"],
                        resolution_status="PENDING",
                    )
                    session.add(conflict_log)
                    await session.commit()
            except Exception as e:
                logger.error(f"Error in conflict processor: {e}")

    async def _log_event(self, event: SyncEvent, status: SyncStatus):
        async with self.SessionLocal() as session:
            event_log = SyncEventLog(
                event_id=event.event_id,
                event_type=event.event_type.value,
                entity_type=event.entity_type.value,
                entity_id=event.entity_id,
                source_system=event.source_system,
                target_systems=event.target_systems,
                data=event.data,
                metadata=event.metadata,
                status=status.value,
            )
            session.add(event_log)
            await session.commit()

    async def _log_event_result(self, event: SyncEvent, result: SyncResult):
        async with self.SessionLocal() as session:
            event_log = await session.get(SyncEventLog, event.event_id)
            if event_log:
                event_log.status = result.status.value
                event_log.processing_time = result.processing_time
                if result.errors:
                    event_log.error_message = "; ".join(result.errors)
                event_log.processed_at = datetime.utcnow()
                await session.commit()

    async def _update_metrics(self, event: SyncEvent, result: SyncResult):
        for target_system in event.target_systems:
            metrics_key = (
                f"{event.source_system}:{target_system}:{event.entity_type.value}"
            )
            if metrics_key not in self.metrics_cache:
                self.metrics_cache[metrics_key] = await self._load_metrics(
                    event.source_system, target_system, event.entity_type
                )
            metrics = self.metrics_cache[metrics_key]
            metrics.total_events += 1
            if result.status == SyncStatus.COMPLETED:
                metrics.successful_events += 1
            else:
                metrics.failed_events += 1
            total_time = (
                metrics.avg_processing_time * (metrics.total_events - 1)
                + result.processing_time
            )
            metrics.avg_processing_time = total_time / metrics.total_events
            metrics.last_event_time = datetime.utcnow()
            metrics.updated_at = datetime.utcnow()
            await session.commit()

    async def _load_metrics(
        self, source_system: str, target_system: str, entity_type: SyncEntityType
    ) -> SyncMetrics:
        async with self.SessionLocal() as session:
            metrics = await session.execute(
                session.query(SyncMetrics)
                .filter(
                    SyncMetrics.source_system == source_system,
                    SyncMetrics.target_system == target_system,
                    SyncMetrics.entity_type == entity_type.value,
                )
                .order_by(SyncMetrics.created_at.desc())
                .first()
            )
            if metrics:
                return metrics.scalar_one_or_none()
            else:
                new_metrics = SyncMetrics(
                    source_system=source_system,
                    target_system=target_system,
                    entity_type=entity_type.value,
                    event_type="ALL",
                )
                session.add(new_metrics)
                await session.commit()
                return new_metrics

    async def _metrics_collector(self):
        while True:
            try:
                await self._collect_system_metrics()
                await self._collect_integration_metrics()
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")

    async def _collect_system_metrics(self):
        pass

    async def _collect_integration_metrics(self):
        pass

    async def _cleanup_task(self):
        while True:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                async with self.SessionLocal() as session:
                    await session.execute(
                        session.query(SyncEventLog)
                        .filter(SyncEventLog.created_at < cutoff_date)
                        .delete()
                    )
                    await session.commit()
                metrics_cutoff = datetime.utcnow() - timedelta(days=7)
                async with self.SessionLocal() as session:
                    await session.execute(
                        session.query(SyncMetrics)
                        .filter(SyncMetrics.updated_at < metrics_cutoff)
                        .delete()
                    )
                    await session.commit()
                await asyncio.sleep(86400)
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def _broadcast_event_update(self, event: SyncEvent, result: SyncResult):
        message = {
            "type": "sync_update",
            "event_id": event.event_id,
            "entity_type": event.entity_type.value,
            "entity_id": event.entity_id,
            "status": result.status.value,
            "timestamp": datetime.utcnow().isoformat(),
        }
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                self.active_connections.remove(connection)

    async def connect_websocket(
        self, websocket: WebSocket, client_id: str, entity_types: List[str] = None
    ):
        await websocket.accept()
        self.active_connections.append(websocket)
        async with self.SessionLocal() as session:
            subscription = SyncSubscription(
                client_id=client_id,
                entity_types=entity_types or [],
                filters={},
                last_active=datetime.utcnow(),
            )
            session.add(subscription)
            await session.commit()
        try:
            while True:
                await asyncio.sleep(30)
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)

    async def get_sync_status(self, event_id: str) -> Optional[Dict]:
        if self.redis_client:
            cached_result = await self.redis_client.get(f"sync_result:{event_id}")
            if cached_result:
                return json.loads(cached_result)
        async with self.SessionLocal() as session:
            event_log = await session.get(SyncEventLog, event_id)
            if event_log:
                return {
                    "event_id": event_log.event_id,
                    "status": event_log.status,
                    "processing_time": event_log.processing_time,
                    "error_message": event_log.error_message,
                    "processed_at": (
                        event_log.processed_at.isoformat()
                        if event_log.processed_at
                        else None
                    ),
                }
        return None

    async def get_sync_metrics(
        self,
        source_system: str = None,
        target_system: str = None,
        entity_type: str = None,
        time_range: int = 24,
    ) -> List[Dict]:
        async with self.SessionLocal() as session:
            query = session.query(SyncMetrics)
            if source_system:
                query = query.filter(SyncMetrics.source_system == source_system)
            if target_system:
                query = query.filter(SyncMetrics.target_system == target_system)
            if entity_type:
                query = query.filter(SyncMetrics.entity_type == entity_type)
            time_filter = datetime.utcnow() - timedelta(hours=time_range)
            query = query.filter(SyncMetrics.updated_at >= time_filter)
            results = await session.execute(query)
            metrics_list = results.scalars().all()
            return [
                {
                    "source_system": m.source_system,
                    "target_system": m.target_system,
                    "entity_type": m.entity_type,
                    "total_events": m.total_events,
                    "successful_events": m.successful_events,
                    "failed_events": m.failed_events,
                    "success_rate": (
                        (m.successful_events / m.total_events * 100)
                        if m.total_events > 0
                        else 0
                    ),
                    "avg_processing_time": m.avg_processing_time,
                    "last_event_time": (
                        m.last_event_time.isoformat() if m.last_event_time else None
                    ),
                    "updated_at": m.updated_at.isoformat(),
                }
                for m in metrics_list
            ]


sync_app = FastAPI(
    title="HMS Sync Engine",
    description="Real-time data synchronization engine",
    version="1.0.0",
)
sync_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
synchronizer: Optional[DataSynchronizer] = None


async def get_synchronizer() -> DataSynchronizer:
    global synchronizer
    if synchronizer is None:
        from ..orchestrator import orchestrator

        synchronizer = DataSynchronizer(orchestrator)
        await synchronizer.initialize()
    return synchronizer


@sync_app.get("/sync/status/{event_id}")
async def get_sync_status(
    event_id: str, synchronizer: DataSynchronizer = Depends(get_synchronizer)
):
    status = await synchronizer.get_sync_status(event_id)
    if not status:
        raise HTTPException(status_code=404, detail="Event not found")
    return status


@sync_app.get("/sync/metrics")
async def get_sync_metrics(
    source_system: Optional[str] = None,
    target_system: Optional[str] = None,
    entity_type: Optional[str] = None,
    time_range: int = Query(24, ge=1, le=168),
    synchronizer: DataSynchronizer = Depends(get_synchronizer),
):
    return await synchronizer.get_sync_metrics(
        source_system, target_system, entity_type, time_range
    )


@sync_app.websocket("/sync/updates/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    entity_types: Optional[str] = None,
    synchronizer: DataSynchronizer = Depends(get_synchronizer),
):
    types = entity_types.split(",") if entity_types else None
    await synchronizer.connect_websocket(websocket, client_id, types)


@sync_app.post("/sync/publish")
async def publish_sync_event(
    event_type: str,
    entity_type: str,
    entity_id: str,
    source_system: str,
    target_systems: List[str],
    data: Dict,
    metadata: Dict = None,
    priority: int = 1,
    conflict_resolution: str = "SOURCE_WINS",
    synchronizer: DataSynchronizer = Depends(get_synchronizer),
):
    event = SyncEvent(
        event_id=str(uuid.uuid4()),
        event_type=SyncEventType(event_type),
        entity_type=SyncEntityType(entity_type),
        entity_id=entity_id,
        source_system=source_system,
        target_systems=target_systems,
        data=data,
        metadata=metadata or {},
        timestamp=datetime.utcnow(),
        priority=priority,
        conflict_resolution=ConflictResolutionStrategy(conflict_resolution),
    )
    event_id = await synchronizer.publish_event(event)
    return {"event_id": event_id, "status": "published"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(sync_app, host="0.0.0.0", port=8082)
