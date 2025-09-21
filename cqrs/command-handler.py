# Command Handler Implementation
# Enterprise-grade command processing for HMS microservices

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Type, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, status
import logging

from .event_store import Event, EventType, EventStore, get_event_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandStatus(Enum):
    """Command execution status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CommandPriority(Enum):
    """Command priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class Command(BaseModel):
    """Base command model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: CommandPriority = CommandPriority.NORMAL
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: CommandStatus = CommandStatus.PENDING
    version: int = 1

class CommandResult(BaseModel):
    """Command execution result"""
    command_id: str
    status: CommandStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    events: List[Event] = Field(default_factory=list)
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CommandHandler(ABC):
    """Abstract base class for command handlers"""

    @abstractmethod
    async def can_handle(self, command: Command) -> bool:
        """Check if this handler can process the command"""
        pass

    @abstractmethod
    async def handle(self, command: Command, event_store: EventStore) -> CommandResult:
        """Handle the command and return result"""
        pass

    @abstractmethod
    async def validate(self, command: Command) -> bool:
        """Validate the command"""
        pass

class PatientCommandHandler(CommandHandler):
    """Handler for patient-related commands"""

    async def can_handle(self, command: Command) -> bool:
        """Check if this handler can process the command"""
        return command.type.startswith("patient_")

    async def validate(self, command: Command) -> bool:
        """Validate the command"""
        required_fields = []

        if command.type == "patient_register":
            required_fields = ["first_name", "last_name", "date_of_birth", "email"]
        elif command.type == "patient_update":
            required_fields = ["patient_id"]
        elif command.type == "patient_delete":
            required_fields = ["patient_id"]
        elif command.type == "patient_admit":
            required_fields = ["patient_id", "admission_date", "department"]
        elif command.type == "patient_discharge":
            required_fields = ["patient_id", "discharge_date"]

        return all(field in command.data for field in required_fields)

    async def handle(self, command: Command, event_store: EventStore) -> CommandResult:
        """Handle patient commands"""
        start_time = datetime.utcnow()

        try:
            if not await self.validate(command):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid command data"
                )

            events = []
            result = {}

            if command.type == "patient_register":
                events, result = await self._handle_patient_registration(command, event_store)
            elif command.type == "patient_update":
                events, result = await self._handle_patient_update(command, event_store)
            elif command.type == "patient_delete":
                events, result = await self._handle_patient_deletion(command, event_store)
            elif command.type == "patient_admit":
                events, result = await self._handle_patient_admission(command, event_store)
            elif command.type == "patient_discharge":
                events, result = await self._handle_patient_discharge(command, event_store)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return CommandResult(
                command_id=command.id,
                status=CommandStatus.COMPLETED,
                result=result,
                events=events,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error handling command {command.id}: {e}")

            return CommandResult(
                command_id=command.id,
                status=CommandStatus.FAILED,
                error=str(e),
                processing_time=processing_time
            )

    async def _handle_patient_registration(self, command: Command, event_store: EventStore) -> tuple[List[Event], Dict[str, Any]]:
        """Handle patient registration"""
        patient_id = str(uuid.uuid4())

        # Get current version
        existing_events = await event_store.get_events(patient_id)
        version = len(existing_events) + 1

        # Create patient registered event
        event = Event(
            type=EventType.PATIENT_REGISTERED,
            aggregate_id=patient_id,
            aggregate_type="patient",
            data={
                "patient_id": patient_id,
                "first_name": command.data["first_name"],
                "last_name": command.data["last_name"],
                "date_of_birth": command.data["date_of_birth"],
                "email": command.data["email"],
                "phone": command.data.get("phone"),
                "address": command.data.get("address"),
                "emergency_contact": command.data.get("emergency_contact"),
                "medical_history": command.data.get("medical_history", []),
                "allergies": command.data.get("allergies", []),
                "medications": command.data.get("medications", [])
            },
            metadata={
                "source": "patient_service",
                "action": "register",
                "ip_address": command.metadata.get("ip_address"),
                "user_agent": command.metadata.get("user_agent")
            },
            version=version,
            user_id=command.user_id,
            correlation_id=command.correlation_id
        )

        await event_store.save_event(event)

        return [event], {"patient_id": patient_id, "status": "registered"}

    async def _handle_patient_update(self, command: Command, event_store: EventStore) -> tuple[List[Event], Dict[str, Any]]:
        """Handle patient update"""
        patient_id = command.data["patient_id"]

        # Get current version
        existing_events = await event_store.get_events(patient_id)
        version = len(existing_events) + 1

        # Create patient updated event
        event = Event(
            type=EventType.PATIENT_UPDATED,
            aggregate_id=patient_id,
            aggregate_type="patient",
            data={
                "patient_id": patient_id,
                "updates": command.data.get("updates", {}),
                "updated_fields": list(command.data.get("updates", {}).keys())
            },
            metadata={
                "source": "patient_service",
                "action": "update",
                "ip_address": command.metadata.get("ip_address"),
                "user_agent": command.metadata.get("user_agent")
            },
            version=version,
            user_id=command.user_id,
            correlation_id=command.correlation_id
        )

        await event_store.save_event(event)

        return [event], {"patient_id": patient_id, "status": "updated"}

    async def _handle_patient_deletion(self, command: Command, event_store: EventStore) -> tuple[List[Event], Dict[str, Any]]:
        """Handle patient deletion"""
        patient_id = command.data["patient_id"]

        # Get current version
        existing_events = await event_store.get_events(patient_id)
        version = len(existing_events) + 1

        # Create patient deleted event
        event = Event(
            type=EventType.PATIENT_DELETED,
            aggregate_id=patient_id,
            aggregate_type="patient",
            data={
                "patient_id": patient_id,
                "reason": command.data.get("reason", "user_request"),
                "deleted_by": command.user_id
            },
            metadata={
                "source": "patient_service",
                "action": "delete",
                "ip_address": command.metadata.get("ip_address"),
                "user_agent": command.metadata.get("user_agent")
            },
            version=version,
            user_id=command.user_id,
            correlation_id=command.correlation_id
        )

        await event_store.save_event(event)

        return [event], {"patient_id": patient_id, "status": "deleted"}

    async def _handle_patient_admission(self, command: Command, event_store: EventStore) -> tuple[List[Event], Dict[str, Any]]:
        """Handle patient admission"""
        patient_id = command.data["patient_id"]

        # Get current version
        existing_events = await event_store.get_events(patient_id)
        version = len(existing_events) + 1

        # Create patient admitted event
        event = Event(
            type=EventType.PATIENT_ADMITTED,
            aggregate_id=patient_id,
            aggregate_type="patient",
            data={
                "patient_id": patient_id,
                "admission_date": command.data["admission_date"],
                "department": command.data["department"],
                "room_number": command.data.get("room_number"),
                "bed_number": command.data.get("bed_number"),
                "admitting_physician": command.data.get("admitting_physician"),
                "admission_reason": command.data.get("admission_reason"),
                "expected_stay": command.data.get("expected_stay")
            },
            metadata={
                "source": "patient_service",
                "action": "admit",
                "ip_address": command.metadata.get("ip_address"),
                "user_agent": command.metadata.get("user_agent")
            },
            version=version,
            user_id=command.user_id,
            correlation_id=command.correlation_id
        )

        await event_store.save_event(event)

        return [event], {"patient_id": patient_id, "status": "admitted"}

    async def _handle_patient_discharge(self, command: Command, event_store: EventStore) -> tuple[List[Event], Dict[str, Any]]:
        """Handle patient discharge"""
        patient_id = command.data["patient_id"]

        # Get current version
        existing_events = await event_store.get_events(patient_id)
        version = len(existing_events) + 1

        # Create patient discharged event
        event = Event(
            type=EventType.PATIENT_DISCHARGED,
            aggregate_id=patient_id,
            aggregate_type="patient",
            data={
                "patient_id": patient_id,
                "discharge_date": command.data["discharge_date"],
                "discharge_reason": command.data.get("discharge_reason"),
                "discharge_notes": command.data.get("discharge_notes"),
                "follow_up_required": command.data.get("follow_up_required", False),
                "follow_up_date": command.data.get("follow_up_date")
            },
            metadata={
                "source": "patient_service",
                "action": "discharge",
                "ip_address": command.metadata.get("ip_address"),
                "user_agent": command.metadata.get("user_agent")
            },
            version=version,
            user_id=command.user_id,
            correlation_id=command.correlation_id
        )

        await event_store.save_event(event)

        return [event], {"patient_id": patient_id, "status": "discharged"}

class AppointmentCommandHandler(CommandHandler):
    """Handler for appointment-related commands"""

    async def can_handle(self, command: Command) -> bool:
        """Check if this handler can process the command"""
        return command.type.startswith("appointment_")

    async def validate(self, command: Command) -> bool:
        """Validate the command"""
        required_fields = []

        if command.type == "appointment_create":
            required_fields = ["patient_id", "provider_id", "appointment_time", "duration"]
        elif command.type == "appointment_update":
            required_fields = ["appointment_id"]
        elif command.type == "appointment_cancel":
            required_fields = ["appointment_id"]
        elif command.type == "appointment_complete":
            required_fields = ["appointment_id"]

        return all(field in command.data for field in required_fields)

    async def handle(self, command: Command, event_store: EventStore) -> CommandResult:
        """Handle appointment commands"""
        start_time = datetime.utcnow()

        try:
            if not await self.validate(command):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid command data"
                )

            events = []
            result = {}

            if command.type == "appointment_create":
                events, result = await self._handle_appointment_creation(command, event_store)
            elif command.type == "appointment_update":
                events, result = await self._handle_appointment_update(command, event_store)
            elif command.type == "appointment_cancel":
                events, result = await self._handle_appointment_cancellation(command, event_store)
            elif command.type == "appointment_complete":
                events, result = await self._handle_appointment_completion(command, event_store)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return CommandResult(
                command_id=command.id,
                status=CommandStatus.COMPLETED,
                result=result,
                events=events,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error handling command {command.id}: {e}")

            return CommandResult(
                command_id=command.id,
                status=CommandStatus.FAILED,
                error=str(e),
                processing_time=processing_time
            )

    async def _handle_appointment_creation(self, command: Command, event_store: EventStore) -> tuple[List[Event], Dict[str, Any]]:
        """Handle appointment creation"""
        appointment_id = str(uuid.uuid4())

        # Get current version
        existing_events = await event_store.get_events(appointment_id)
        version = len(existing_events) + 1

        # Create appointment created event
        event = Event(
            type=EventType.APPOINTMENT_CREATED,
            aggregate_id=appointment_id,
            aggregate_type="appointment",
            data={
                "appointment_id": appointment_id,
                "patient_id": command.data["patient_id"],
                "provider_id": command.data["provider_id"],
                "appointment_time": command.data["appointment_time"],
                "duration": command.data["duration"],
                "appointment_type": command.data.get("appointment_type", "general"),
                "status": "scheduled",
                "location": command.data.get("location"),
                "notes": command.data.get("notes"),
                "reminder_sent": False
            },
            metadata={
                "source": "appointment_service",
                "action": "create",
                "ip_address": command.metadata.get("ip_address"),
                "user_agent": command.metadata.get("user_agent")
            },
            version=version,
            user_id=command.user_id,
            correlation_id=command.correlation_id
        )

        await event_store.save_event(event)

        return [event], {"appointment_id": appointment_id, "status": "created"}

    async def _handle_appointment_update(self, command: Command, event_store: EventStore) -> tuple[List[Event], Dict[str, Any]]:
        """Handle appointment update"""
        appointment_id = command.data["appointment_id"]

        # Get current version
        existing_events = await event_store.get_events(appointment_id)
        version = len(existing_events) + 1

        # Create appointment updated event
        event = Event(
            type=EventType.APPOINTMENT_UPDATED,
            aggregate_id=appointment_id,
            aggregate_type="appointment",
            data={
                "appointment_id": appointment_id,
                "updates": command.data.get("updates", {}),
                "updated_fields": list(command.data.get("updates", {}).keys())
            },
            metadata={
                "source": "appointment_service",
                "action": "update",
                "ip_address": command.metadata.get("ip_address"),
                "user_agent": command.metadata.get("user_agent")
            },
            version=version,
            user_id=command.user_id,
            correlation_id=command.correlation_id
        )

        await event_store.save_event(event)

        return [event], {"appointment_id": appointment_id, "status": "updated"}

    async def _handle_appointment_cancellation(self, command: Command, event_store: EventStore) -> tuple[List[Event], Dict[str, Any]]:
        """Handle appointment cancellation"""
        appointment_id = command.data["appointment_id"]

        # Get current version
        existing_events = await event_store.get_events(appointment_id)
        version = len(existing_events) + 1

        # Create appointment cancelled event
        event = Event(
            type=EventType.APPOINTMENT_CANCELLED,
            aggregate_id=appointment_id,
            aggregate_type="appointment",
            data={
                "appointment_id": appointment_id,
                "cancellation_reason": command.data.get("cancellation_reason"),
                "cancelled_by": command.user_id,
                "cancellation_time": datetime.utcnow().isoformat()
            },
            metadata={
                "source": "appointment_service",
                "action": "cancel",
                "ip_address": command.metadata.get("ip_address"),
                "user_agent": command.metadata.get("user_agent")
            },
            version=version,
            user_id=command.user_id,
            correlation_id=command.correlation_id
        )

        await event_store.save_event(event)

        return [event], {"appointment_id": appointment_id, "status": "cancelled"}

    async def _handle_appointment_completion(self, command: Command, event_store: EventStore) -> tuple[List[Event], Dict[str, Any]]:
        """Handle appointment completion"""
        appointment_id = command.data["appointment_id"]

        # Get current version
        existing_events = await event_store.get_events(appointment_id)
        version = len(existing_events) + 1

        # Create appointment completed event
        event = Event(
            type=EventType.APPOINTMENT_COMPLETED,
            aggregate_id=appointment_id,
            aggregate_type="appointment",
            data={
                "appointment_id": appointment_id,
                "completion_time": datetime.utcnow().isoformat(),
                "completion_notes": command.data.get("completion_notes"),
                "follow_up_required": command.data.get("follow_up_required", False),
                "next_appointment": command.data.get("next_appointment")
            },
            metadata={
                "source": "appointment_service",
                "action": "complete",
                "ip_address": command.metadata.get("ip_address"),
                "user_agent": command.metadata.get("user_agent")
            },
            version=version,
            user_id=command.user_id,
            correlation_id=command.correlation_id
        )

        await event_store.save_event(event)

        return [event], {"appointment_id": appointment_id, "status": "completed"}

class CommandDispatcher:
    """Command dispatcher for routing commands to appropriate handlers"""

    def __init__(self):
        self.handlers: List[CommandHandler] = []
        self.command_queue = asyncio.Queue()
        self.processing = False

    def register_handler(self, handler: CommandHandler):
        """Register a command handler"""
        self.handlers.append(handler)

    async def dispatch(self, command: Command) -> CommandResult:
        """Dispatch a command to the appropriate handler"""
        for handler in self.handlers:
            if await handler.can_handle(command):
                event_store = await get_event_store()
                return await handler.handle(command, event_store)

        return CommandResult(
            command_id=command.id,
            status=CommandStatus.FAILED,
            error=f"No handler found for command type: {command.type}",
            processing_time=0.0
        )

    async def dispatch_async(self, command: Command) -> str:
        """Dispatch a command asynchronously"""
        await self.command_queue.put(command)
        return command.id

    async def start_processing(self):
        """Start processing commands asynchronously"""
        self.processing = True
        asyncio.create_task(self._process_commands())

    async def stop_processing(self):
        """Stop processing commands"""
        self.processing = False

    async def _process_commands(self):
        """Process commands from the queue"""
        while self.processing or not self.command_queue.empty():
            try:
                command = await asyncio.wait_for(self.command_queue.get(), timeout=1.0)
                await self.dispatch(command)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing command: {e}")

# Global command dispatcher instance
command_dispatcher = CommandDispatcher()

# Register default handlers
command_dispatcher.register_handler(PatientCommandHandler())
command_dispatcher.register_handler(AppointmentCommandHandler())

async def dispatch_command(command: Command) -> CommandResult:
    """Dispatch a command using the global dispatcher"""
    return await command_dispatcher.dispatch(command)

async def dispatch_command_async(command: Command) -> str:
    """Dispatch a command asynchronously"""
    return await command_dispatcher.dispatch_async(command)