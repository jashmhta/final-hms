"""
API Optimization Framework for Enterprise Healthcare Systems
Advanced REST, GraphQL, and real-time communication optimization
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Union

import aiohttp
import aioredis
import graphene
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_socketio import SocketManager
from graphene import Argument, Field, Int, List, ObjectType, Schema, String
from graphene_federation import build_schema, extend, external, key
from graphql import GraphQLResolveInfo
from prometheus_fastapi_instrumentator import Instrumentator
from redis import asyncio as aioredis
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.utils import timezone


class APIType(Enum):
    """API types supported"""

    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    WEBSOCKET = "websocket"
    SSE = "sse"


class APIMetrics:
    """API performance metrics tracking"""

    def __init__(self):
        self.request_count = 0
        self.response_times = []
        self.error_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.active_connections = 0
        self.rate_limited_requests = 0

    def record_request(self, response_time: float, is_error: bool = False):
        """Record API request metrics"""
        self.request_count += 1
        self.response_times.append(response_time)
        if is_error:
            self.error_count += 1

    def record_cache_result(self, hit: bool):
        """Record cache hit/miss"""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def get_average_response_time(self) -> float:
        """Get average response time"""
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0

    def get_error_rate(self) -> float:
        """Get error rate percentage"""
        return (self.error_count / self.request_count * 100) if self.request_count > 0 else 0

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary"""
        return {
            "request_count": self.request_count,
            "average_response_time": self.get_average_response_time(),
            "error_rate": self.get_error_rate(),
            "cache_hit_rate": self.get_cache_hit_rate(),
            "active_connections": self.active_connections,
            "rate_limited_requests": self.rate_limited_requests,
        }


class APIRateLimiter:
    """Advanced rate limiting for APIs"""

    def __init__(self, redis_client: aioredis.Redis):
        self.redis_client = redis_client
        self.rate_limits = {
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
            "auth": {"requests": 5, "window": 60},  # 5 auth requests per minute
            "sensitive": {"requests": 10, "window": 60},  # 10 sensitive requests per minute
            "admin": {"requests": 1000, "window": 60},  # 1000 admin requests per minute
        }

    async def check_rate_limit(self, key: str, rate_type: str = "default") -> bool:
        """Check if request is within rate limit"""
        if rate_type not in self.rate_limits:
            rate_type = "default"

        limit = self.rate_limits[rate_type]
        redis_key = f"rate_limit:{key}:{rate_type}"
        current_time = int(time.time())

        # Use Redis pipeline for atomic operations
        async with self.redis_client.pipeline() as pipe:
            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, current_time - limit["window"])

            # Get current count
            pipe.zcard(redis_key)

            # Add current request
            pipe.zadd(redis_key, {str(current_time): current_time})

            # Set expiration
            pipe.expire(redis_key, limit["window"])

            results = await pipe.execute()
            current_count = results[1]

            return current_count <= limit["requests"]

    async def get_remaining_requests(self, key: str, rate_type: str = "default") -> int:
        """Get remaining requests for rate limit"""
        if rate_type not in self.rate_limits:
            rate_type = "default"

        limit = self.rate_limits[rate_type]
        redis_key = f"rate_limit:{key}:{rate_type}"
        current_count = await self.redis_client.zcard(redis_key)
        return max(0, limit["requests"] - current_count)


class APICacheManager:
    """Advanced API caching strategies"""

    def __init__(self, redis_client: aioredis.Redis):
        self.redis_client = redis_client
        self.cache_strategies = {
            "patient_data": {"ttl": 300, "prefix": "patient"},
            "appointment_data": {"ttl": 60, "prefix": "appointment"},
            "clinical_data": {"ttl": 180, "prefix": "clinical"},
            "billing_data": {"ttl": 300, "prefix": "billing"},
            "admin_data": {"ttl": 600, "prefix": "admin"},
        }

    async def get_cache_key(self, request: Request, user_id: Optional[int] = None) -> str:
        """Generate cache key for request"""
        cache_key_parts = [
            request.method,
            str(request.url),
            str(request.query_params),
        ]

        if user_id:
            cache_key_parts.append(f"user_{user_id}")

        return ":".join(cache_key_parts)

    async def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached API response"""
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logging.error(f"Cache get error: {e}")
            return None

    async def cache_response(self, cache_key: str, response_data: Dict, ttl: int = 300):
        """Cache API response"""
        try:
            await self.redis_client.setex(cache_key, ttl, json.dumps(response_data, default=str))
        except Exception as e:
            logging.error(f"Cache set error: {e}")

    async def invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            logging.error(f"Cache invalidation error: {e}")


class APIResponseOptimizer:
    """Optimize API responses for performance"""

    @staticmethod
    def optimize_response_data(data: Any, request: Request) -> Dict:
        """Optimize response data based on request"""
        optimized = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "request_id": getattr(request.state, "request_id", None),
            "data": data,
        }

        # Add pagination info if present
        if hasattr(data, "__dict__") and hasattr(data, "items"):
            if hasattr(data, "page") and hasattr(data, "total_pages"):
                optimized["pagination"] = {
                    "page": data.page,
                    "page_size": data.page_size,
                    "total_pages": data.total_pages,
                    "total_items": data.total,
                }

        return optimized

    @staticmethod
    def compress_response(response_data: Dict) -> Dict:
        """Compress response data for better performance"""

        # Remove None values to reduce payload size
        def remove_none(obj):
            if isinstance(obj, dict):
                return {k: remove_none(v) for k, v in obj.items() if v is not None}
            elif isinstance(obj, list):
                return [remove_none(item) for item in obj if item is not None]
            else:
                return obj

        return remove_none(response_data)


class RESTAPIOptimizer:
    """REST API optimization and best practices"""

    def __init__(self, app: FastAPI, redis_client: aioredis.Redis):
        self.app = app
        self.redis_client = redis_client
        self.rate_limiter = APIRateLimiter(redis_client)
        self.cache_manager = APICacheManager(redis_client)
        self.metrics = APIMetrics()
        self._setup_middleware()
        self._setup_error_handling()
        self._setup_documentation()

    def _setup_middleware(self):
        """Setup REST API middleware"""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOWED_ORIGINS if hasattr(settings, "CORS_ALLOWED_ORIGINS") else ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Gzip compression
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)

        # Security headers
        self.app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

        # Request ID middleware
        @self.app.middleware("http")
        async def add_request_id(request: Request, call_next):
            import uuid

            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

    def _setup_error_handling(self):
        """Setup centralized error handling"""

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            self.metrics.record_request(0, is_error=True)
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "error": exc.detail,
                    "request_id": getattr(request.state, "request_id", None),
                    "timestamp": datetime.now().isoformat(),
                },
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            self.metrics.record_request(0, is_error=True)
            logging.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "request_id": getattr(request.state, "request_id", None),
                    "timestamp": datetime.now().isoformat(),
                },
            )

    def _setup_documentation(self):
        """Setup API documentation"""
        self.app.title = "HMS Enterprise API"
        self.app.description = "Enterprise-grade Hospital Management System API"
        self.app.version = "1.0.0"
        self.app.docs_url = "/docs"
        self.app.redoc_url = "/redoc"

    def create_endpoint(self, path: str, methods: List[str], cache_ttl: int = 0, rate_limit_type: str = "default"):
        """Decorator for optimized REST endpoints"""

        def decorator(func):
            @self.app.route(path, methods=methods)
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                start_time = time.time()
                self.metrics.active_connections += 1

                try:
                    # Rate limiting
                    client_ip = request.client.host
                    if not await self.rate_limiter.check_rate_limit(client_ip, rate_limit_type):
                        self.metrics.rate_limited_requests += 1
                        raise HTTPException(status_code=429, detail="Rate limit exceeded")

                    # Cache check
                    cache_key = await self.cache_manager.get_cache_key(request)
                    if cache_ttl > 0:
                        cached_response = await self.cache_manager.get_cached_response(cache_key)
                        if cached_response:
                            self.metrics.record_cache_result(hit=True)
                            return JSONResponse(cached_response)

                    # Execute function
                    result = await func(request, *args, **kwargs)

                    # Optimize response
                    response_data = APIResponseOptimizer.optimize_response_data(result, request)
                    response_data = APIResponseOptimizer.compress_response(response_data)

                    # Cache response
                    if cache_ttl > 0:
                        await self.cache_manager.cache_response(cache_key, response_data, cache_ttl)

                    response_time = time.time() - start_time
                    self.metrics.record_request(response_time, is_error=False)
                    self.metrics.record_cache_result(hit=False)

                    return JSONResponse(response_data)

                except HTTPException:
                    response_time = time.time() - start_time
                    self.metrics.record_request(response_time, is_error=True)
                    raise
                except Exception as e:
                    response_time = time.time() - start_time
                    self.metrics.record_request(response_time, is_error=True)
                    logging.error(f"API endpoint error: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Internal server error")
                finally:
                    self.metrics.active_connections -= 1

            return wrapper

        return decorator


class GraphQLAPIOptimizer:
    """GraphQL API optimization and federation"""

    def __init__(self):
        self.schema = None
        self.resolvers = {}
        self.metrics = APIMetrics()

    def create_schema(self) -> Schema:
        """Create optimized GraphQL schema"""

        class Query(ObjectType):
            # Patient queries
            patients = List(PatientType)
            patient = Field(PatientType, id=Int(required=True))
            search_patients = List(PatientType, query=String())

            # Appointment queries
            appointments = List(AppointmentType)
            appointment = Field(AppointmentType, id=Int(required=True))

            # Clinical queries
            medical_records = List(MedicalRecordType)
            lab_results = List(LabResultType)

            # Billing queries
            bills = List(BillType)
            payments = List(PaymentType)

        class Mutation(ObjectType):
            # Patient mutations
            create_patient = PatientType(required=True)
            update_patient = PatientType(required=True)
            delete_patient = PatientType(required=True)

            # Appointment mutations
            create_appointment = AppointmentType(required=True)
            update_appointment = AppointmentType(required=True)
            cancel_appointment = AppointmentType(required=True)

            # Clinical mutations
            create_medical_record = MedicalRecordType(required=True)
            update_medical_record = MedicalRecordType(required=True)

            # Billing mutations
            create_bill = BillType(required=True)
            process_payment = PaymentType(required=True)

        # Build federated schema
        self.schema = build_schema(query=Query, mutation=Mutation)
        return self.schema

    def optimize_resolver(self, resolver_name: str, cache_ttl: int = 0):
        """Decorator for optimized GraphQL resolvers"""

        def decorator(func):
            @wraps(func)
            async def wrapper(root, info: GraphQLResolveInfo, **kwargs):
                start_time = time.time()
                self.metrics.active_connections += 1

                try:
                    # Execute resolver
                    result = await func(root, info, **kwargs)

                    response_time = time.time() - start_time
                    self.metrics.record_request(response_time, is_error=False)

                    return result

                except Exception as e:
                    response_time = time.time() - start_time
                    self.metrics.record_request(response_time, is_error=True)
                    logging.error(f"GraphQL resolver error: {e}", exc_info=True)
                    raise e
                finally:
                    self.metrics.active_connections -= 1

            return wrapper

        return decorator

    def setup_federation(self):
        """Setup GraphQL federation for microservices"""
        # This would set up Apollo Federation for microservices
        # Each service would extend the base schema with its own types
        pass


# GraphQL Type Definitions (simplified)
class PatientType(ObjectType):
    id = Int(required=True)
    medical_record_number = String(required=True)
    first_name = String(required=True)
    last_name = String(required=True)
    date_of_birth = String()
    gender = String()
    email = String()
    phone = String()


class AppointmentType(ObjectType):
    id = Int(required=True)
    patient_id = Int(required=True)
    doctor_id = Int(required=True)
    appointment_date = String(required=True)
    appointment_time = String(required=True)
    status = String()
    appointment_type = String()


class MedicalRecordType(ObjectType):
    id = Int(required=True)
    patient_id = Int(required=True)
    record_type = String(required=True)
    title = String(required=True)
    description = String()
    created_at = String()


class LabResultType(ObjectType):
    id = Int(required=True)
    patient_id = Int(required=True)
    test_name = String(required=True)
    result_value = String()
    reference_range = String()
    test_date = String()


class BillType(ObjectType):
    id = Int(required=True)
    patient_id = Int(required=True)
    amount = String(required=True)
    status = String()
    created_at = String()


class PaymentType(ObjectType):
    id = Int(required=True)
    bill_id = Int(required=True)
    amount = String(required=True)
    payment_method = String()
    payment_date = String()


class RealTimeCommunicationManager:
    """Real-time communication with WebSockets and SSE"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.socket_manager = SocketManager()
        self.active_connections = {}
        self.event_subscribers = {}

    def setup_websockets(self):
        """Setup WebSocket endpoints"""

        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket, client_id: str):
            await self.socket_manager.connect(websocket, client_id)
            self.active_connections[client_id] = websocket

            try:
                while True:
                    data = await websocket.receive_text()
                    await self.handle_websocket_message(client_id, data)
            except Exception as e:
                logging.error(f"WebSocket error for {client_id}: {e}")
            finally:
                self.socket_manager.disconnect(websocket, client_id)
                del self.active_connections[client_id]

    def setup_sse(self):
        """Setup Server-Sent Events endpoint"""

        @self.app.get("/sse/{client_id}")
        async def sse_endpoint(client_id: str):
            async def event_generator():
                while client_id in self.active_connections:
                    # Send heartbeat
                    yield {"event": "heartbeat", "data": json.dumps({"timestamp": datetime.now().isoformat()})}
                    await asyncio.sleep(30)

            return EventSourceResponse(event_generator())

    async def handle_websocket_message(self, client_id: str, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "subscribe":
                # Subscribe to events
                events = data.get("events", [])
                for event in events:
                    if event not in self.event_subscribers:
                        self.event_subscribers[event] = []
                    self.event_subscribers[event].append(client_id)

            elif message_type == "unsubscribe":
                # Unsubscribe from events
                events = data.get("events", [])
                for event in events:
                    if event in self.event_subscribers:
                        self.event_subscribers[event].remove(client_id)

        except Exception as e:
            logging.error(f"WebSocket message handling error: {e}")

    async def broadcast_event(self, event_type: str, data: Dict):
        """Broadcast event to subscribed clients"""
        if event_type in self.event_subscribers:
            message = {"type": event_type, "data": data, "timestamp": datetime.now().isoformat()}

            for client_id in self.event_subscribers[event_type]:
                if client_id in self.active_connections:
                    try:
                        await self.active_connections[client_id].send_text(json.dumps(message))
                    except Exception as e:
                        logging.error(f"Failed to send message to {client_id}: {e}")


class APIGateway:
    """API Gateway for unified access to all API types"""

    def __init__(self):
        self.rest_optimizer = None
        self.graphql_optimizer = GraphQLAPIOptimizer()
        self.realtime_manager = None
        self.redis_client = None

    async def initialize(self, app: FastAPI):
        """Initialize API Gateway"""
        # Initialize Redis
        if hasattr(settings, "REDIS_URL"):
            self.redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

            # Initialize REST optimizer
            self.rest_optimizer = RESTAPIOptimizer(app, self.redis_client)

            # Initialize real-time manager
            self.realtime_manager = RealTimeCommunicationManager(app)
            self.realtime_manager.setup_websockets()
            self.realtime_manager.setup_sse()

        # Initialize GraphQL
        self.graphql_optimizer.create_schema()

    def get_metrics(self) -> Dict:
        """Get combined API metrics"""
        metrics = {
            "rest": self.rest_optimizer.metrics.to_dict() if self.rest_optimizer else {},
            "graphql": self.graphql_optimizer.metrics.to_dict(),
            "total_requests": 0,
            "total_errors": 0,
            "average_response_time": 0,
            "cache_hit_rate": 0,
        }

        # Calculate combined metrics
        if self.rest_optimizer:
            metrics["total_requests"] += self.rest_optimizer.metrics.request_count
            metrics["total_errors"] += self.rest_optimizer.metrics.error_count

        metrics["total_requests"] += self.graphql_optimizer.metrics.request_count
        metrics["total_errors"] += self.graphql_optimizer.metrics.error_count

        if metrics["total_requests"] > 0:
            metrics["average_response_time"] = (
                (
                    self.rest_optimizer.metrics.get_average_response_time() * self.rest_optimizer.metrics.request_count
                    if self.rest_optimizer
                    else 0
                )
                + (
                    self.graphql_optimizer.metrics.get_average_response_time()
                    * self.graphql_optimizer.metrics.request_count
                )
            ) / metrics["total_requests"]

        return metrics


# Global API Gateway instance
api_gateway = APIGateway()


# API monitoring and observability
class APIMonitor:
    """API monitoring and observability"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.setup_prometheus()
        self.setup_health_checks()

    def setup_prometheus(self):
        """Setup Prometheus metrics"""
        instrumentator = Instrumentator().instrument(app=self.app).expose(app)
        self.instrumentator = instrumentator

    def setup_health_checks(self):
        """Setup health check endpoints"""

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "services": {"database": "healthy", "redis": "healthy", "api": "healthy"},
            }

        @self.app.get("/health/detailed")
        async def detailed_health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "metrics": api_gateway.get_metrics(),
                "system_info": {
                    "python_version": "3.9",
                    "framework": "FastAPI",
                    "database": "PostgreSQL",
                    "cache": "Redis",
                },
            }


# Global API monitor instance
api_monitor = None


def initialize_api_optimization(app: FastAPI):
    """Initialize API optimization framework"""
    global api_monitor

    # Initialize API Gateway
    asyncio.create_task(api_gateway.initialize(app))

    # Initialize monitoring
    api_monitor = APIMonitor(app)

    logging.info("API optimization framework initialized")


# Decorators for easy use
def optimized_rest_endpoint(
    path: str, methods: List[str] = ["GET"], cache_ttl: int = 0, rate_limit_type: str = "default"
):
    """Decorator for optimized REST endpoints"""

    def decorator(func):
        if api_gateway.rest_optimizer:
            return api_gateway.rest_optimizer.create_endpoint(path, methods, cache_ttl, rate_limit_type)(func)
        return func

    return decorator


def optimized_graphql_resolver(cache_ttl: int = 0):
    """Decorator for optimized GraphQL resolvers"""

    def decorator(func):
        return api_gateway.graphql_optimizer.optimize_resolver(func.__name__, cache_ttl)(func)

    return decorator
