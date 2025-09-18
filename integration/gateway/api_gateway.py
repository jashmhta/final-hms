import asyncio
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import aiofiles
import aiohttp
import asyncpg
import jwt
from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, validator, EmailStr
from redis.asyncio import redis
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from cryptography.fernet import Fernet
from prometheus_fastapi_instrumentator import Instrumentator
from ..orchestrator import IntegrationOrchestrator
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Base = declarative_base()
class APIGatewayMode(Enum):
    PROXY = "PROXY"
    ROUTE = "ROUTE"
    AGGREGATE = "AGGREGATE"
    TRANSFORM = "TRANSFORM"
    CACHE = "CACHE"
    SECURITY = "SECURITY"
class AuthenticationType(Enum):
    JWT = "JWT"
    API_KEY = "API_KEY"
    OAUTH2 = "OAUTH2"
    BASIC_AUTH = "BASIC_AUTH"
    CLIENT_CERT = "CLIENT_CERT"
    SAML = "SAML"
    OPENID_CONNECT = "OPENID_CONNECT"
class AuthorizationType(Enum):
    RBAC = "RBAC"  
    ABAC = "ABAC"  
    ACL = "ACL"   
    POLICY_BASED = "POLICY_BASED"
class SecurityLevel(Enum):
    PUBLIC = "PUBLIC"           
    BASIC = "BASIC"             
    STANDARD = "STANDARD"       
    ENHANCED = "ENHANCED"       
    RESTRICTED = "RESTRICTED"    
    ADMIN = "ADMIN"             
class RateLimitStrategy(Enum):
    FIXED_WINDOW = "FIXED_WINDOW"
    SLIDING_WINDOW = "SLIDING_WINDOW"
    TOKEN_BUCKET = "TOKEN_BUCKET"
    LEAKY_BUCKET = "LEAKY_BUCKET"
@dataclass
class RouteConfig:
    path: str
    method: str
    target_service: str
    target_path: str
    authentication_required: bool = True
    security_level: SecurityLevel = SecurityLevel.STANDARD
    rate_limit: int = 1000  
    cache_enabled: bool = True
    cache_ttl: int = 300  
    transformation_enabled: bool = False
    validation_enabled: bool = True
    allowed_roles: List[str] = field(default_factory=list)
    allowed_ip_ranges: List[str] = field(default_factory=list)
    request_headers: Dict[str, str] = field(default_factory=dict)
    response_headers: Dict[str, str] = field(default_factory=dict)
@dataclass
class UserContext:
    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    tenant_id: str
    department_id: Optional[str] = None
    facility_id: Optional[str] = None
    authentication_type: AuthenticationType = AuthenticationType.JWT
    session_id: str = ""
    client_ip: str = ""
    user_agent: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))
class APIGatewayConfig(Base):
    __tablename__ = "api_gateway_config"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_name = Column(String(100), nullable=False, unique=True)
    config_type = Column(String(50), nullable=False)
    config_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class APIRoute(Base):
    __tablename__ = "api_routes"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    path = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    target_service = Column(String(100), nullable=False)
    target_path = Column(String(200), nullable=False)
    authentication_required = Column(Boolean, default=True)
    security_level = Column(String(20), default="STANDARD")
    rate_limit = Column(Integer, default=1000)
    cache_enabled = Column(Boolean, default=True)
    cache_ttl = Column(Integer, default=300)
    transformation_enabled = Column(Boolean, default=False)
    validation_enabled = Column(Boolean, default=True)
    allowed_roles = Column(JSON)
    allowed_ip_ranges = Column(JSON)
    request_headers = Column(JSON)
    response_headers = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_name = Column(String(100), nullable=False)
    api_key_hash = Column(String(255), nullable=False, unique=True)
    user_id = Column(String(100), nullable=False)
    permissions = Column(JSON)
    allowed_services = Column(JSON)
    rate_limit = Column(Integer, default=1000)
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
class RateLimitLog(Base):
    __tablename__ = "rate_limit_log"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_ip = Column(String(45), nullable=False)
    endpoint = Column(String(200), nullable=False)
    user_id = Column(String(100))
    request_count = Column(Integer, default=1)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    exceeded_limit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class SecurityAuditLog(Base):
    __tablename__ = "security_audit_log"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100))
    client_ip = Column(String(45), nullable=False)
    action = Column(String(100), nullable=False)
    resource = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    auth_type = Column(String(50))
    auth_result = Column(String(20))
    request_headers = Column(JSON)
    request_body = Column(Text)
    response_headers = Column(JSON)
    error_message = Column(Text)
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
class APIGateway:
    def __init__(self, orchestrator: IntegrationOrchestrator):
        self.orchestrator = orchestrator
        self.redis_client: Optional[redis.Redis] = None
        self.db_url = os.getenv("GATEWAY_DB_URL", "postgresql+asyncpg://hms:hms@localhost:5432/gateway")
        self.engine = create_async_engine(self.db_url)
        self.SessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.jwt_secret = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = timedelta(hours=1)
        self.encryption_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
        self.fernet = Fernet(self.encryption_key.encode())
        self.rate_limit_strategy = RateLimitStrategy.SLIDING_WINDOW
        self.rate_limiters = {}
        self.cache_ttl = 300  
        self.routes: Dict[str, RouteConfig] = {}
        self.middleware_chain = []
        self._initialize_routes()
        self._initialize_middleware()
    async def initialize(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await self._load_routes()
        asyncio.create_task(self._cleanup_task())
        asyncio.create_task(self._metrics_collector())
        logger.info("API Gateway initialized successfully")
    def _initialize_routes(self):
        default_routes = [
            RouteConfig(
                path="/api/patients",
                method="GET",
                target_service="patients_service",
                target_path="/api/patients",
                security_level=SecurityLevel.STANDARD,
                allowed_roles=["DOCTOR", "NURSE", "ADMIN", "RECEPTIONIST"]
            ),
            RouteConfig(
                path="/api/patients",
                method="POST",
                target_service="patients_service",
                target_path="/api/patients",
                security_level=SecurityLevel.STANDARD,
                allowed_roles=["DOCTOR", "ADMIN", "RECEPTIONIST"]
            ),
            RouteConfig(
                path="/api/encounters",
                method="GET",
                target_service="ehr_service",
                target_path="/api/encounters",
                security_level=SecurityLevel.STANDARD,
                allowed_roles=["DOCTOR", "NURSE", "ADMIN"]
            ),
            RouteConfig(
                path="/api/observations",
                method="GET",
                target_service="ehr_service",
                target_path="/api/observations",
                security_level=SecurityLevel.STANDARD,
                allowed_roles=["DOCTOR", "NURSE", "LAB_TECH"]
            ),
            RouteConfig(
                path="/api/medications",
                method="GET",
                target_service="pharmacy_service",
                target_path="/api/medications",
                security_level=SecurityLevel.STANDARD,
                allowed_roles=["DOCTOR", "PHARMACIST", "NURSE"]
            ),
            RouteConfig(
                path="/api/lab/orders",
                method="POST",
                target_service="lab_service",
                target_path="/api/lab/orders",
                security_level=SecurityLevel.STANDARD,
                allowed_roles=["DOCTOR", "NURSE"]
            ),
            RouteConfig(
                path="/api/billing/claims",
                method="POST",
                target_service="billing_service",
                target_path="/api/billing/claims",
                security_level=SecurityLevel.ENHANCED,
                allowed_roles=["BILLING_ADMIN", "ADMIN"]
            ),
            RouteConfig(
                path="/api/admin/**",
                method="*",
                target_service="admin_service",
                target_path="/api/admin",
                security_level=SecurityLevel.ADMIN,
                allowed_roles=["SUPER_ADMIN", "ADMIN"]
            ),
            RouteConfig(
                path="/health",
                method="GET",
                target_service="gateway",
                target_path="/health",
                authentication_required=False,
                security_level=SecurityLevel.PUBLIC
            )
        ]
        for route in default_routes:
            route_key = f"{route.method}:{route.path}"
            self.routes[route_key] = route
    def _initialize_middleware(self):
        self.middleware_chain = [
            self._cors_middleware,
            self._security_middleware,
            self._rate_limit_middleware,
            self._authentication_middleware,
            self._authorization_middleware,
            self._cache_middleware,
            self._transformation_middleware,
            self._validation_middleware,
            self._proxy_middleware
        ]
    async def _load_routes(self):
        async with self.SessionLocal() as session:
            routes = await session.execute(
                session.query(APIRoute).filter(APIRoute.is_active == True)
            )
            db_routes = routes.scalars().all()
            for db_route in db_routes:
                route_config = RouteConfig(
                    path=db_route.path,
                    method=db_route.method,
                    target_service=db_route.target_service,
                    target_path=db_route.target_path,
                    authentication_required=db_route.authentication_required,
                    security_level=SecurityLevel(db_route.security_level),
                    rate_limit=db_route.rate_limit,
                    cache_enabled=db_route.cache_enabled,
                    cache_ttl=db_route.cache_ttl,
                    transformation_enabled=db_route.transformation_enabled,
                    validation_enabled=db_route.validation_enabled,
                    allowed_roles=db_route.allowed_roles or [],
                    allowed_ip_ranges=db_route.allowed_ip_ranges or [],
                    request_headers=db_route.request_headers or {},
                    response_headers=db_route.response_headers or {}
                )
                route_key = f"{db_route.method}:{db_route.path}"
                self.routes[route_key] = route_config
    async def process_request(self, request: Request) -> Response:
        start_time = time.time()
        try:
            response = None
            context = {
                "request": request,
                "user_context": None,
                "route_config": None,
                "cache_key": None,
                "rate_limit_key": None
            }
            for middleware in self.middleware_chain:
                response = await middleware(request, context)
                if response is not None:
                    break
            if response is None:
                response = JSONResponse(
                    status_code=404,
                    content={"error": "Endpoint not found"}
                )
            await self._log_security_event(
                request=request,
                context=context,
                status_code=response.status_code,
                processing_time=time.time() - start_time
            )
            return response
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            await self._log_security_event(
                request=request,
                context=context or {},
                status_code=500,
                error_message=str(e)
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    async def _cors_middleware(self, request: Request, context: Dict) -> Optional[Response]:
        return None
    async def _security_middleware(self, request: Request, context: Dict) -> Optional[Response]:
        if not request.headers.get("X-Content-Type-Options"):
            pass
        content_type = request.headers.get("content-type", "")
        if request.method in ["POST", "PUT", "PATCH"] and not content_type.startswith("application/"):
            return JSONResponse(
                status_code=415,
                content={"error": "Unsupported Media Type"}
            )
        return None
    async def _rate_limit_middleware(self, request: Request, context: Dict) -> Optional[Response]:
        client_ip = request.client.host
        endpoint = f"{request.method}:{request.url.path}"
        route_key = f"{request.method}:{request.url.path}"
        route_config = self.routes.get(route_key)
        if not route_config:
            return None
        context["route_config"] = route_config
        user_id = getattr(context.get("user_context"), "user_id", None) if context.get("user_context") else None
        rate_limit_key = f"rate_limit:{client_ip}:{endpoint}:{user_id or 'anonymous'}"
        context["rate_limit_key"] = rate_limit_key
        if self.redis_client:
            current_time = datetime.utcnow()
            window_start = current_time.replace(second=0, microsecond=0)
            window_end = window_start + timedelta(hours=1)
            current_count = await self.redis_client.get(rate_limit_key)
            if current_count is None:
                current_count = 0
            if int(current_count) >= route_config.rate_limit:
                await self._log_rate_limit_exceeded(
                    client_ip=client_ip,
                    endpoint=endpoint,
                    user_id=user_id,
                    window_start=window_start,
                    window_end=window_end
                )
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
            await self.redis_client.incr(rate_limit_key)
            await self.redis_client.expireat(rate_limit_key, int(window_end.timestamp()))
        return None
    async def _authentication_middleware(self, request: Request, context: Dict) -> Optional[Response]:
        route_config = context.get("route_config")
        if not route_config or not route_config.authentication_required:
            return None
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Authentication required"}
            )
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            user_context = UserContext(
                user_id=payload["user_id"],
                username=payload["username"],
                email=payload["email"],
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                tenant_id=payload["tenant_id"],
                client_ip=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                authentication_type=AuthenticationType.JWT
            )
            context["user_context"] = user_context
            if self.redis_client:
                await self.redis_client.setex(
                    f"user_session:{user_context.user_id}",
                    3600,
                    json.dumps({
                        "username": user_context.username,
                        "roles": user_context.roles,
                        "last_activity": datetime.utcnow().isoformat()
                    })
                )
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"error": "Token expired"}
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid token"}
            )
        return None
    async def _authorization_middleware(self, request: Request, context: Dict) -> Optional[Response]:
        route_config = context.get("route_config")
        user_context = context.get("user_context")
        if not route_config or not user_context:
            return None
        if route_config.security_level == SecurityLevel.ADMIN and "ADMIN" not in user_context.roles:
            return JSONResponse(
                status_code=403,
                content={"error": "Administrator access required"}
            )
        if route_config.allowed_roles:
            user_roles = set(user_context.roles)
            allowed_roles = set(route_config.allowed_roles)
            if not user_roles.intersection(allowed_roles):
                return JSONResponse(
                    status_code=403,
                    content={"error": "Insufficient permissions"}
                )
        if route_config.allowed_ip_ranges:
            client_ip = request.client.host
            allowed_ips = route_config.allowed_ip_ranges
            if not self._is_ip_allowed(client_ip, allowed_ips):
                return JSONResponse(
                    status_code=403,
                    content={"error": "IP address not allowed"}
                )
        return None
    def _is_ip_allowed(self, client_ip: str, allowed_ranges: List[str]) -> bool:
        if "*" in allowed_ranges:
            return True
        return client_ip in allowed_ranges
    async def _cache_middleware(self, request: Request, context: Dict) -> Optional[Response]:
        route_config = context.get("route_config")
        if not route_config or not route_config.cache_enabled or request.method != "GET":
            return None
        cache_key = f"cache:{request.url.path}:{request.query_params}"
        context["cache_key"] = cache_key
        if self.redis_client:
            cached_response = await self.redis_client.get(cache_key)
            if cached_response:
                response_data = json.loads(cached_response)
                return JSONResponse(
                    content=response_data,
                    headers={"X-Cache": "HIT"}
                )
        return None
    async def _transformation_middleware(self, request: Request, context: Dict) -> Optional[Response]:
        return None
    async def _validation_middleware(self, request: Request, context: Dict) -> Optional[Response]:
        route_config = context.get("route_config")
        if not route_config or not route_config.validation_enabled:
            return None
        for header_name, header_value in route_config.request_headers.items():
            if request.headers.get(header_name) != header_value:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Required header '{header_name}' missing or invalid"}
                )
        return None
    async def _proxy_middleware(self, request: Request, context: Dict) -> Optional[Response]:
        route_config = context.get("route_config")
        if not route_config:
            return None
        try:
            target_url = f"{self._get_service_url(route_config.target_service)}{route_config.target_path}"
            headers = dict(request.headers)
            headers.pop("host", None)  
            if context.get("user_context"):
                headers["X-User-ID"] = context["user_context"].user_id
                headers["X-User-Roles"] = ",".join(context["user_context"].roles)
            async with aiohttp.ClientSession() as session:
                if request.method == "GET":
                    async with session.get(target_url, headers=headers) as response:
                        response_data = await response.json()
                elif request.method == "POST":
                    request_body = await request.json()
                    async with session.post(target_url, json=request_body, headers=headers) as response:
                        response_data = await response.json()
                elif request.method == "PUT":
                    request_body = await request.json()
                    async with session.put(target_url, json=request_body, headers=headers) as response:
                        response_data = await response.json()
                elif request.method == "DELETE":
                    async with session.delete(target_url, headers=headers) as response:
                        response_data = await response.json()
                else:
                    return JSONResponse(
                        status_code=405,
                        content={"error": "Method not allowed"}
                    )
            if route_config.cache_enabled and request.method == "GET" and response.status == 200:
                cache_key = context.get("cache_key")
                if cache_key and self.redis_client:
                    await self.redis_client.setex(
                        cache_key,
                        route_config.cache_ttl,
                        json.dumps(response_data)
                    )
            response_headers = {}
            for header_name, header_value in route_config.response_headers.items():
                response_headers[header_name] = header_value
            return JSONResponse(
                content=response_data,
                status_code=response.status,
                headers=response_headers
            )
        except Exception as e:
            logger.error(f"Error proxying request: {e}")
            return JSONResponse(
                status_code=502,
                content={"error": "Bad Gateway"}
            )
    def _get_service_url(self, service_name: str) -> str:
        service_urls = {
            "patients_service": "http://localhost:8001",
            "ehr_service": "http://localhost:8002",
            "pharmacy_service": "http://localhost:8003",
            "lab_service": "http://localhost:8004",
            "billing_service": "http://localhost:8005",
            "admin_service": "http://localhost:8006"
        }
        return service_urls.get(service_name, f"http://localhost:8000")
    async def _log_security_event(self, request: Request, context: Dict, status_code: int,
                                 processing_time: float = 0.0, error_message: str = None):
        user_context = context.get("user_context")
        route_config = context.get("route_config")
        async with self.SessionLocal() as session:
            audit_log = SecurityAuditLog(
                user_id=user_context.user_id if user_context else None,
                client_ip=request.client.host,
                action=f"{request.method} {request.url.path}",
                resource=request.url.path,
                method=request.method,
                status_code=status_code,
                auth_type=user_context.authentication_type.value if user_context else None,
                auth_result="SUCCESS" if status_code < 400 else "FAILURE",
                processing_time=processing_time,
                error_message=error_message
            )
            session.add(audit_log)
            await session.commit()
    async def _log_rate_limit_exceeded(self, client_ip: str, endpoint: str, user_id: str,
                                       window_start: datetime, window_end: datetime):
        async with self.SessionLocal() as session:
            rate_limit_log = RateLimitLog(
                client_ip=client_ip,
                endpoint=endpoint,
                user_id=user_id,
                window_start=window_start,
                window_end=window_end,
                exceeded_limit=True
            )
            session.add(rate_limit_log)
            await session.commit()
    async def _cleanup_task(self):
        while True:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                async with self.SessionLocal() as session:
                    await session.execute(
                        session.query(SecurityAuditLog)
                        .filter(SecurityAuditLog.created_at < cutoff_date)
                        .delete()
                    )
                    await session.commit()
                rate_limit_cutoff = datetime.utcnow() - timedelta(days=7)
                async with self.SessionLocal() as session:
                    await session.execute(
                        session.query(RateLimitLog)
                        .filter(RateLimitLog.created_at < rate_limit_cutoff)
                        .delete()
                    )
                    await session.commit()
                await asyncio.sleep(86400)  
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    async def _metrics_collector(self):
        while True:
            try:
                await self._collect_gateway_metrics()
                await asyncio.sleep(300)  
            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")
    async def _collect_gateway_metrics(self):
        pass
    def generate_jwt_token(self, user_context: UserContext) -> str:
        payload = {
            "user_id": user_context.user_id,
            "username": user_context.username,
            "email": user_context.email,
            "roles": user_context.roles,
            "permissions": user_context.permissions,
            "tenant_id": user_context.tenant_id,
            "exp": datetime.utcnow() + self.jwt_expiration,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    def validate_jwt_token(self, token: str) -> Optional[UserContext]:
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            return UserContext(
                user_id=payload["user_id"],
                username=payload["username"],
                email=payload["email"],
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                tenant_id=payload["tenant_id"],
                authentication_type=AuthenticationType.JWT
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
gateway_app = FastAPI(
    title="HMS API Gateway",
    description="Secure API Gateway for Hospital Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
gateway_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
gateway_app.add_middleware(GZipMiddleware, minimum_size=1000)
gateway_app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
Instrumentator().instrument(gateway_app).expose(gateway_app)
gateway: Optional[APIGateway] = None
async def get_gateway() -> APIGateway:
    global gateway
    if gateway is None:
        from ..orchestrator import orchestrator
        gateway = APIGateway(orchestrator)
        await gateway.initialize()
    return gateway
@gateway_app.on_event("startup")
async def startup_event():
    global gateway
    if gateway is None:
        from ..orchestrator import orchestrator
        gateway = APIGateway(orchestrator)
        await gateway.initialize()
@gateway_app.on_event("shutdown")
async def shutdown_event():
    if gateway and gateway.redis_client:
        await gateway.redis_client.close()
@gateway_app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
@gateway_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_route(request: Request, gateway: APIGateway = Depends(get_gateway)):
    return await gateway.process_request(request)
@gateway_app.post("/gateway/auth/login")
async def login(username: str, password: str, gateway: APIGateway = Depends(get_gateway)):
    if username == "admin" and password == os.getenv("DEMO_ADMIN_PASSWORD", secrets.token_urlsafe(12)):
        user_context = UserContext(
            user_id="1",
            username=username,
            email="admin@hms.com",
            roles=["ADMIN"],
            permissions=["*"],
            tenant_id="default"
        )
        token = gateway.generate_jwt_token(user_context)
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": {
                "user_id": user_context.user_id,
                "username": user_context.username,
                "email": user_context.email,
                "roles": user_context.roles
            }
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
@gateway_app.get("/gateway/routes")
async def get_routes(gateway: APIGateway = Depends(get_gateway)):
    routes_info = []
    for route_key, route_config in gateway.routes.items():
        routes_info.append({
            "path": route_config.path,
            "method": route_config.method,
            "target_service": route_config.target_service,
            "target_path": route_config.target_path,
            "security_level": route_config.security_level.value,
            "rate_limit": route_config.rate_limit,
            "cache_enabled": route_config.cache_enabled,
            "allowed_roles": route_config.allowed_roles
        })
    return {"routes": routes_info}
@gateway_app.get("/gateway/metrics")
async def get_gateway_metrics(gateway: APIGateway = Depends(get_gateway)):
    return {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "avg_response_time": 0.0,
        "active_connections": 0
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(gateway_app, host="0.0.0.0", port=8000)