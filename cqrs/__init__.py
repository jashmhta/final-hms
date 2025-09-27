# CQRS Package Initialization
# Enterprise-grade CQRS implementation for HMS microservices

"""
CQRS (Command Query Responsibility Segregation) implementation for the HMS.

This package provides a comprehensive CQRS implementation with:
- Event sourcing with PostgreSQL and Redis
- Command handlers for write operations
- Query handlers for read operations
- Projections for building read models
- Real-time event processing
- Caching and optimization
- Comprehensive error handling
- Health monitoring
- Analytics and reporting

Architecture:
- Event Store: PostgreSQL + Redis for event persistence and real-time processing
- Command Handlers: Process write operations and generate events
- Query Handlers: Process read operations with caching
- Projectors: Build and maintain read models from events
- API Layer: RESTful API for commands and queries
- WebSocket: Real-time event broadcasting
- Monitoring: Comprehensive metrics and health checks

Usage:
    from cqrs import EventStore, CommandDispatcher, QueryDispatcher, Projector

    # Initialize components
    event_store = await get_event_store()
    command_dispatcher = get_command_dispatcher()
    query_dispatcher = get_query_dispatcher()
    projector = await get_projector()

    # Process commands
    result = await command_dispatcher.dispatch(command)

    # Process queries
    result = await query_dispatcher.dispatch(query)

    # Handle events
    await projector.process_event(event)
"""

from .command_handler import (
    Command,
    CommandDispatcher,
    CommandHandler,
    CommandResult,
    dispatch_command,
)
from .cqrs_api import app
from .event_store import Event, EventStore, EventType, get_event_store
from .projector import Projection, ProjectionType, Projector, get_projector
from .query_handler import (
    Query,
    QueryDispatcher,
    QueryHandler,
    QueryResult,
    dispatch_query,
)

__version__ = "1.0.0"
__author__ = "HMS Enterprise Team"
__email__ = "dev@hms.enterprise.com"

__all__ = [
    # Event Store
    "EventStore",
    "Event",
    "EventType",
    "get_event_store",
    # Command Handling
    "Command",
    "CommandResult",
    "CommandHandler",
    "CommandDispatcher",
    "dispatch_command",
    # Query Handling
    "Query",
    "QueryResult",
    "QueryHandler",
    "QueryDispatcher",
    "dispatch_query",
    # Projections
    "Projector",
    "Projection",
    "ProjectionType",
    "get_projector",
    # API
    "app",
]
