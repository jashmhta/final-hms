import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SecurityEventType(enum.Enum):
    LOGIN_ATTEMPT = "login_attempt"
    ACCESS_DENIED = "access_denied"
    CONFIG_CHANGE = "config_change"
    DATA_ACCESS = "data_access"
    SYSTEM_ALERT = "system_alert"
    COMPLIANCE_VIOLATION = "compliance_violation"


class SecurityEventSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True)
    event_type = Column(Enum(SecurityEventType))
    severity = Column(Enum(SecurityEventSeverity))
    timestamp = Column(DateTime)
    user_id = Column(Integer, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    resource = Column(String, nullable=True)
    action = Column(String)
    details = Column(JSON)
    status = Column(String)  # new, investigating, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String, unique=True)
    timestamp = Column(DateTime)
    user_id = Column(Integer)
    user_role = Column(String)
    action = Column(String)
    resource_type = Column(String)
    resource_id = Column(Integer)
    resource_name = Column(String)
    changes = Column(JSON, nullable=True)
    ip_address = Column(String)
    user_agent = Column(String)
    status = Column(String)  # success, failure
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SecurityPolicy(Base):
    __tablename__ = "security_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String, unique=True)
    name = Column(String)
    description = Column(Text)
    policy_type = Column(String)  # access_control, data_protection, network, etc.
    rules = Column(JSON)
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccessControlRule(Base):
    __tablename__ = "access_control_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String, unique=True)
    resource_type = Column(String)
    resource_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    role = Column(String, nullable=True)
    permission = Column(String)  # read, write, delete, admin
    conditions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True)
    title = Column(String)
    description = Column(Text)
    severity = Column(Enum(SecurityEventSeverity))
    status = Column(String)  # new, investigating, contained, resolved
    assigned_to = Column(String, nullable=True)
    reported_by = Column(String)
    reported_at = Column(DateTime)
    resolved_at = Column(DateTime, nullable=True)
    root_cause = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    affected_systems = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(String, unique=True)
    standard = Column(String)  # HIPAA, GDPR, ISO27001, etc.
    requirement = Column(String)
    description = Column(Text)
    status = Column(String)  # compliant, non_compliant, partial
    evidence = Column(JSON, nullable=True)
    last_check = Column(DateTime)
    next_check = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EncryptionKey(Base):
    __tablename__ = "encryption_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String, unique=True)
    key_type = Column(String)  # data_encryption, ssl, etc.
    algorithm = Column(String)
    key_data = Column(Text)  # encrypted key data
    key_version = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    rotated_at = Column(DateTime, nullable=True)
