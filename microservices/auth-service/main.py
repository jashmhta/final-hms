"""
Authentication Service - Microservice for User Management and Authentication

This service handles user authentication, authorization, JWT token management,
role-based access control, and multi-factor authentication.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import QueuePool
from passlib.context import CryptContext
from jose import JWTError, jwt
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
import asyncpg
from redis.asyncio import Redis
import pyotp
import qrcode
import io
import base64

# Configuration
from .config import (
    DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, JWT_REFRESH_SECRET_KEY,
    SERVICE_NAME, SERVICE_VERSION, JAEGER_AGENT_HOST, JAEGER_AGENT_PORT,
    ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS,
    MFA_ISSUER_NAME, MFA_TOKEN_VALIDITY, EMAIL_SERVICE_URL
)

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name=JAEGER_AGENT_HOST,
    agent_port=JAEGER_AGENT_PORT,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
tracer = trace.get_tracer(__name__)

# Database setup
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis = Redis.from_url(REDIS_URL, decode_responses=True)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Setup
security = HTTPBearer()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database Models
class UserRole(str):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    STAFF = "staff"
    PATIENT = "patient"

class UserStatus(str):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.STAFF)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    created_by_user = relationship("User", remote_side=[id])

class RolePermission(Base):
    __tablename__ = 'role_permissions'

    id = Column(Integer, primary_key=True, index=True)
    role = Column(Enum(UserRole), nullable=False)
    permission = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_revoked = Column(Boolean, default=False)

    user = relationship("User")

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status = Column(String, nullable=False)  # success, failure
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

# Pydantic Models
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=12)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = UserRole.STAFF

class UserLogin(BaseModel):
    username: str
    password: str
    mfa_token: Optional[str] = Field(None, min_length=6, max_length=6)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class MFASetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]

class MFATokenRequest(BaseModel):
    token: str = Field(..., min_length=6, max_length=6)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12)

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(user_id: int) -> str:
    """Create JWT refresh token"""
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.utcnow() + expires_delta

    token_data = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())
    }

    refresh_token = jwt.encode(token_data, JWT_REFRESH_SECRET_KEY, algorithm="HS256")
    return refresh_token

async def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify JWT token"""
    try:
        secret_key = JWT_SECRET_KEY if token_type == "access" else JWT_REFRESH_SECRET_KEY
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])

        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail="Invalid token type")

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(lambda: SessionLocal())
) -> User:
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = await verify_token(token, "access")
        user_id = int(payload.get("sub"))

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=401, detail="User account is inactive")

        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def audit_log_action(
    user_id: Optional[int],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: str = "success",
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: Session = Depends(lambda: SessionLocal())
):
    """Log audit actions"""
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        details=details
    )
    db.add(audit_entry)
    db.commit()

async def check_user_permissions(user: User, permission: str, resource: str) -> bool:
    """Check if user has required permissions"""
    if user.role == UserRole.SUPER_ADMIN:
        return True

    # Check role-based permissions
    cache_key = f"permissions:{user.role}"
    permissions = await redis.get(cache_key)

    if not permissions:
        # Cache miss, fetch from database
        db = SessionLocal()
        role_permissions = db.query(RolePermission).filter(
            RolePermission.role == user.role
        ).all()
        permissions = [
            f"{perm.permission}:{perm.resource}"
            for perm in role_permissions
        ]
        await redis.setex(cache_key, 3600, ",".join(permissions))
        db.close()
    else:
        permissions = permissions.split(",")

    required_permission = f"{permission}:{resource}"
    return required_permission in permissions

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    yield
    # Shutdown
    logger.info(f"Shutting down {SERVICE_NAME}")

app = FastAPI(
    title="Authentication Service",
    description="Enterprise-grade Authentication and Authorization Service",
    version=SERVICE_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check database connection
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")

        # Check Redis connection
        await redis.ping()

        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )

@app.post("/api/auth/register", response_model=TokenResponse)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(lambda: SessionLocal())
):
    """Register a new user"""
    with tracer.start_as_current_span("register_user") as span:
        span.set_attribute("email", user_data.email)
        span.set_attribute("username", user_data.username)

        # Check if user already exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="Username already taken")

        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            uuid=str(uuid.uuid4()),
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=user_data.role
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Log registration
        background_tasks.add_task(
            audit_log_action,
            user.id,
            "user_registered",
            "user",
            str(user.id),
            "success",
            f"New user registered: {user.email}"
        )

        # Generate tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(user.id)

        # Store refresh token
        refresh_token_entry = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(refresh_token_entry)
        db.commit()

        logger.info(f"User registered successfully: {user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "uuid": user.uuid,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "mfa_enabled": user.mfa_enabled
            }
        )

@app.post("/api/auth/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(lambda: SessionLocal())
):
    """Login user with username and password"""
    with tracer.start_as_current_span("login_user") as span:
        span.set_attribute("username", login_data.username)

        # Find user by username or email
        user = db.query(User).filter(
            (User.username == login_data.username) | (User.email == login_data.username)
        ).first()

        if not user or not verify_password(login_data.password, user.hashed_password):
            # Log failed login attempt
            background_tasks.add_task(
                audit_log_action,
                user.id if user else None,
                "login_failed",
                "user",
                str(user.id) if user else None,
                "failure",
                f"Failed login attempt for {login_data.username}",
                request.client.host,
                request.headers.get("user-agent")
            )

            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
                db.commit()

            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Check if account is locked
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            raise HTTPException(status_code=403, detail="Account is temporarily locked")

        # Check MFA if enabled
        if user.mfa_enabled:
            if not login_data.mfa_token:
                raise HTTPException(status_code=400, detail="MFA token required")

            if not pyotp.TOTP(user.mfa_secret).verify(login_data.mfa_token):
                background_tasks.add_task(
                    audit_log_action,
                    user.id,
                    "mfa_failed",
                    "user",
                    str(user.id),
                    "failure",
                    f"Failed MFA attempt for {user.username}",
                    request.client.host,
                    request.headers.get("user-agent")
                )
                raise HTTPException(status_code=401, detail="Invalid MFA token")

        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.utcnow()
        db.commit()

        # Generate tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(user.id)

        # Store refresh token
        refresh_token_entry = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(refresh_token_entry)
        db.commit()

        # Log successful login
        background_tasks.add_task(
            audit_log_action,
            user.id,
            "login_success",
            "user",
            str(user.id),
            "success",
            f"Successful login for {user.username}",
            request.client.host,
            request.headers.get("user-agent")
        )

        logger.info(f"User logged in successfully: {user.username}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "uuid": user.uuid,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "mfa_enabled": user.mfa_enabled
            }
        )

@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(lambda: SessionLocal())
):
    """Refresh access token using refresh token"""
    with tracer.start_as_current_span("refresh_token") as span:
        try:
            payload = await verify_token(refresh_token, "refresh")
            user_id = int(payload.get("sub"))

            # Check if refresh token exists and is not revoked
            token_entry = db.query(RefreshToken).filter(
                RefreshToken.token == refresh_token,
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            ).first()

            if not token_entry:
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="User not found or inactive")

            # Generate new tokens
            new_access_token = create_access_token(data={"sub": str(user.id)})
            new_refresh_token = create_refresh_token(user.id)

            # Revoke old refresh token
            token_entry.is_revoked = True

            # Store new refresh token
            new_token_entry = RefreshToken(
                token=new_refresh_token,
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            )
            db.add(new_token_entry)
            db.commit()

            # Log token refresh
            background_tasks.add_task(
                audit_log_action,
                user.id,
                "token_refreshed",
                "user",
                str(user.id),
                "success"
            )

            span.set_attribute("user_id", user_id)
            logger.info(f"Token refreshed for user: {user.username}")

            return TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user={
                    "id": user.id,
                    "uuid": user.uuid,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "mfa_enabled": user.mfa_enabled
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(status_code=401, detail="Token refresh failed")

@app.post("/api/auth/logout")
async def logout_user(
    refresh_token: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal())
):
    """Logout user by revoking refresh token"""
    with tracer.start_as_current_span("logout_user") as span:
        span.set_attribute("user_id", current_user.id)

        # Revoke refresh token
        token_entry = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == current_user.id
        ).first()

        if token_entry:
            token_entry.is_revoked = True
            db.commit()

        # Log logout
        background_tasks.add_task(
            audit_log_action,
            current_user.id,
            "logout",
            "user",
            str(current_user.id),
            "success"
        )

        logger.info(f"User logged out: {current_user.username}")

        return {"message": "Logged out successfully"}

@app.post("/api/auth/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal())
):
    """Setup Multi-Factor Authentication"""
    with tracer.start_as_current_span("setup_mfa") as span:
        span.set_attribute("user_id", current_user.id)

        if current_user.mfa_enabled:
            raise HTTPException(status_code=400, detail="MFA already enabled")

        # Generate MFA secret
        mfa_secret = pyotp.random_base32()

        # Store temporarily (user needs to verify first)
        temp_key = f"mfa_temp:{current_user.id}"
        await redis.setex(temp_key, 300, mfa_secret)  # 5 minutes

        # Generate QR code
        totp = pyotp.TOTP(mfa_secret)
        provisioning_uri = totp.provisioning_uri(
            current_user.email,
            issuer_name=MFA_ISSUER_NAME
        )

        qr_img = qrcode.make(provisioning_uri)
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()

        # Generate backup codes
        backup_codes = [pyotp.random_base32()[:8] for _ in range(10)]

        # Store backup codes temporarily
        backup_key = f"mfa_backup:{current_user.id}"
        await redis.setex(backup_key, 300, ",".join(backup_codes))

        logger.info(f"MFA setup initiated for user: {current_user.username}")

        return MFASetupResponse(
            secret=mfa_secret,
            qr_code=qr_base64,
            backup_codes=backup_codes
        )

@app.post("/api/auth/mfa/verify")
async def verify_mfa(
    mfa_data: MFATokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal())
):
    """Verify MFA setup"""
    with tracer.start_as_current_span("verify_mfa") as span:
        span.set_attribute("user_id", current_user.id)

        if current_user.mfa_enabled:
            raise HTTPException(status_code=400, detail="MFA already enabled")

        # Get temporary MFA secret
        temp_key = f"mfa_temp:{current_user.id}"
        mfa_secret = await redis.get(temp_key)

        if not mfa_secret:
            raise HTTPException(status_code=400, detail="MFA setup expired")

        # Verify token
        totp = pyotp.TOTP(mfa_secret)
        if not totp.verify(mfa_data.token):
            raise HTTPException(status_code=400, detail="Invalid MFA token")

        # Enable MFA for user
        current_user.mfa_enabled = True
        current_user.mfa_secret = mfa_secret
        db.commit()

        # Get backup codes
        backup_key = f"mfa_backup:{current_user.id}"
        backup_codes = await redis.get(backup_key)

        # Clean up temporary data
        await redis.delete(temp_key, backup_key)

        logger.info(f"MFA verified and enabled for user: {current_user.username}")

        return {"message": "MFA enabled successfully", "backup_codes": backup_codes.split(",")}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )