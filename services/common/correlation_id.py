"""
Correlation ID utilities for end-to-end request tracking
"""

import uuid
import logging
from typing import Optional, Dict, Any
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

logger = structlog.get_logger(__name__)

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context"""
    return correlation_id_var.get()

def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in context"""
    correlation_id_var.set(correlation_id)

def generate_correlation_id() -> str:
    """Generate a new correlation ID"""
    return str(uuid.uuid4())

def ensure_correlation_id() -> str:
    """Ensure correlation ID exists, creating one if needed"""
    correlation_id = get_correlation_id()
    if correlation_id is None:
        correlation_id = generate_correlation_id()
        set_correlation_id(correlation_id)
    return correlation_id

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to handle correlation ID in HTTP requests"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract correlation ID from headers
        correlation_id = request.headers.get("x-correlation-id")

        if not correlation_id:
            # Generate new correlation ID
            correlation_id = generate_correlation_id()

        # Set in context
        set_correlation_id(correlation_id)

        # Add correlation ID to logger context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            user_agent=request.headers.get("user-agent", ""),
            path=request.url.path,
            method=request.method
        )

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["x-correlation-id"] = correlation_id

        return response

class CorrelationIDFilter(logging.Filter):
    """Logging filter to add correlation ID to log records"""

    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True

# Async context manager for correlation ID
class CorrelationIDContext:
    """Context manager for correlation ID handling"""

    def __init__(self, correlation_id: str = None):
        self.correlation_id = correlation_id or generate_correlation_id()
        self.token = None

    async def __aenter__(self):
        self.token = correlation_id_var.set(self.correlation_id)

        # Update structured logger
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=self.correlation_id
        )

        return self.correlation_id

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            correlation_id_var.reset(self.token)

# Decorator for adding correlation ID to async functions
def with_correlation_id(func):
    """Decorator to ensure correlation ID exists in async function"""
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with CorrelationIDContext() as correlation_id:
            logger.info("Starting async operation", operation=func.__name__)
            try:
                result = await func(*args, **kwargs)
                logger.info("Completed async operation", operation=func.__name__)
                return result
            except Exception as e:
                logger.error("Failed async operation", operation=func.__name__, error=str(e))
                raise
    return wrapper

# Utilities for message queues
def add_correlation_to_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Add correlation ID to message"""
    correlation_id = get_correlation_id()
    if correlation_id:
        message["correlation_id"] = correlation_id
    return message

def extract_correlation_from_message(message: Dict[str, Any]) -> Optional[str]:
    """Extract correlation ID from message"""
    return message.get("correlation_id")

# Integration with OpenTelemetry
def inject_correlation_to_span(span, correlation_id: str):
    """Inject correlation ID into OpenTelemetry span"""
    span.set_attribute("correlation.id", correlation_id)
    span.set_attribute("user.id", getattr(span, 'user_id', 'unknown'))
    span.set_attribute("session.id", getattr(span, 'session_id', 'unknown'))

# Database utilities
def add_correlation_to_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add correlation ID to query parameters for logging"""
    correlation_id = get_correlation_id()
    if correlation_id:
        params["_correlation_id"] = correlation_id
    return params

# FastAPI dependency
from fastapi import Depends, Request
from typing import Annotated

async def get_correlation_id_from_request(request: Request) -> str:
    """FastAPI dependency to get correlation ID from request"""
    correlation_id = request.headers.get("x-correlation-id")
    if not correlation_id:
        correlation_id = generate_correlation_id()
        request.headers.__dict__["_list"].append(("x-correlation-id", correlation_id))
    return correlation_id

CorrelationID = Annotated[str, Depends(get_correlation_id_from_request)]

# Django middleware
class DjangoCorrelationIDMiddleware:
    """Django middleware for correlation ID handling"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract or create correlation ID
        correlation_id = request.META.get('HTTP_X_CORRELATION_ID')
        if not correlation_id:
            correlation_id = generate_correlation_id()

        # Set on request
        request.correlation_id = correlation_id
        set_correlation_id(correlation_id)

        # Process request
        response = self.get_response(request)

        # Add to response headers
        response['X-Correlation-ID'] = correlation_id

        return response

# Celery task correlation
class CeleryCorrelationIDTask:
    """Base class for Celery tasks with correlation ID support"""

    def __call__(self, *args, **kwargs):
        correlation_id = kwargs.pop('correlation_id', None)
        if not correlation_id:
            correlation_id = generate_correlation_id()

        with CorrelationIDContext(correlation_id):
            return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement run method")

# gRPC interceptor
import grpc
from grpc.aio import ServerInterceptor, ClientInterceptor

class CorrelationIDServerInterceptor(ServerInterceptor):
    """gRPC server interceptor for correlation ID"""

    async def intercept_service(self, continuation, handler_call_details):
        # Extract correlation ID from metadata
        metadata = dict(handler_call_details.invocation_metadata)
        correlation_id = metadata.get('x-correlation-id') or generate_correlation_id()

        # Set in context
        set_correlation_id(correlation_id)

        # Call next interceptor
        return await continuation(handler_call_details)

class CorrelationIDClientInterceptor(ClientInterceptor):
    """gRPC client interceptor for correlation ID"""

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        # Add correlation ID to metadata
        metadata = list(client_call_details.metadata or [])
        correlation_id = get_correlation_id() or generate_correlation_id()
        metadata.append(('x-correlation-id', correlation_id))

        # Update call details
        client_call_details = client_call_details._replace(
            metadata=tuple(metadata)
        )

        # Call next interceptor
        return await continuation(client_call_details, request)

# WebSockets
async def websocket_with_correlation(websocket):
    """WebSocket wrapper with correlation ID"""
    correlation_id = websocket.headers.get("x-correlation-id")
    if not correlation_id:
        correlation_id = generate_correlation_id()

    async with CorrelationIDContext(correlation_id):
        logger.info("WebSocket connection established")
        try:
            await websocket.accept()
            await websocket.send_json({"correlation_id": correlation_id})
            # Handle websocket messages
            while True:
                data = await websocket.receive_text()
                logger.info("Received WebSocket message", data=data)
                await websocket.send_json({"echo": data})
        except Exception as e:
            logger.error("WebSocket error", error=str(e))
        finally:
            logger.info("WebSocket connection closed")