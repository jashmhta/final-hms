"""
Shared API Base Classes and Utilities
Eliminates redundant API patterns across all services.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Type variables for generic responses
T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response format - eliminates redundant response structures."""

    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[T] = Field(None, description="Response data")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PaginatedResponse(APIResponse[List[T]], Generic[T]):
    """Paginated API response format."""

    pagination: Dict[str, Any] = Field(..., description="Pagination information")

    @classmethod
    def create(
        cls,
        data: List[T],
        skip: int,
        limit: int,
        total: int,
        message: str = "Success",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create paginated response."""
        return cls(
            success=True,
            data=data,
            message=message,
            pagination={
                "skip": skip,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
                "current_page": (skip // limit) + 1,
                "has_next": skip + limit < total,
                "has_prev": skip > 0,
            },
            metadata=metadata,
        )


class ErrorResponse(BaseModel):
    """Standard error response format."""

    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
    trace_id: Optional[str] = Field(None, description="Request trace ID")


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Health check response format."""

    status: HealthStatus = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )
    checks: Optional[Dict[str, Any]] = Field(
        None, description="Individual health checks"
    )
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BaseServiceApp:
    """Base service application class - eliminates redundant app configuration."""

    def __init__(
        self,
        service_name: str,
        service_description: str,
        version: str = "1.0.0",
        cors_origins: List[str] = None,
    ):
        self.service_name = service_name
        self.service_description = service_description
        self.version = version
        self.cors_origins = cors_origins or ["*"]
        self.start_time = datetime.utcnow()

        self.app = FastAPI(
            title=f"{service_name} Service API",
            description=service_description,
            version=version,
            docs_url="/docs" if self.is_development() else None,
            redoc_url="/redoc" if self.is_development() else None,
        )

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """Setup standard middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Setup standard routes."""
        self.app.add_api_route("/", self.root, methods=["GET"])
        self.app.add_api_route("/health", self.health_check, methods=["GET"])

    async def root(self) -> APIResponse[Dict[str, str]]:
        """Root endpoint - standardized across all services."""
        return APIResponse(
            success=True,
            data={
                "service": self.service_name,
                "version": self.version,
                "description": self.service_description,
            },
            message=f"{self.service_name} Service API is running",
            metadata={
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
            },
        )

    async def health_check(self) -> HealthResponse:
        """Health check endpoint - standardized across all services."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return HealthResponse(
            status=HealthStatus.HEALTHY,
            service=self.service_name.lower(),
            version=self.version,
            uptime=uptime,
            checks={
                "database": await self.check_database(),
                "memory": await self.check_memory(),
                "disk": await self.check_disk(),
            },
        )

    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity (to be implemented by services)."""
        return {"status": "healthy", "message": "Database check not implemented"}

    async def check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        import psutil

        memory = psutil.virtual_memory()
        return {
            "status": "healthy" if memory.percent < 80 else "degraded",
            "usage_percent": memory.percent,
            "available_mb": memory.available / (1024 * 1024),
        }

    async def check_disk(self) -> Dict[str, Any]:
        """Check disk usage."""
        import psutil

        disk = psutil.disk_usage("/")
        return {
            "status": "healthy" if disk.percent < 80 else "degraded",
            "usage_percent": disk.percent,
            "free_gb": disk.free / (1024 * 1024 * 1024),
        }

    def add_error_handlers(self):
        """Add standard error handlers."""

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            return JSONResponse(
                status_code=exc.status_code,
                content=ErrorResponse(
                    error="HTTP_ERROR",
                    message=exc.detail,
                    details={"status_code": exc.status_code},
                ).dict(exclude_none=True),
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error="INTERNAL_ERROR",
                    message="An unexpected error occurred",
                    details={"exception": str(exc)},
                ).dict(exclude_none=True),
            )

    def is_development(self) -> bool:
        """Check if running in development mode."""
        import os

        return os.getenv("ENVIRONMENT", "development").lower() == "development"

    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app


# Standard API utility functions
def create_success_response(
    data: Any, message: str = "Success", metadata: Optional[Dict[str, Any]] = None
) -> APIResponse:
    """Create standard success response."""
    return APIResponse(success=True, data=data, message=message, metadata=metadata)


def create_error_response(
    error: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400,
) -> tuple[ErrorResponse, int]:
    """Create standard error response."""
    error_response = ErrorResponse(error=error, message=message, details=details)
    return error_response, status_code


def handle_database_errors(func):
    """Decorator to handle database errors."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return wrapper


def validate_pagination_params(skip: int = 0, limit: int = 100) -> tuple[int, int]:
    """Validate and normalize pagination parameters."""
    skip = max(0, skip)
    limit = min(1000, max(1, limit))  # Max 1000 records per request
    return skip, limit


def get_request_metadata(request) -> Dict[str, Any]:
    """Extract common metadata from request."""
    return {
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.url.path,
    }


# Common middleware
class TimingMiddleware:
    """Middleware to measure request timing."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = datetime.utcnow()
        request_id = scope.get("headers", {}).get(b"x-request-id", b"").decode()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                process_time = (datetime.utcnow() - start_time).total_seconds()
                headers = dict(message.get("headers", []))
                headers[b"x-process-time"] = str(process_time).encode()
                if request_id:
                    headers[b"x-request-id"] = request_id.encode()
                message["headers"] = list(headers.items())
            await send(message)

        await self.app(scope, receive, send_wrapper)
