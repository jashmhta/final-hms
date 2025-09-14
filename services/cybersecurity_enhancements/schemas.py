from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SecurityEventType(str, Enum):
    LOGIN_ATTEMPT = "login_attempt"
    ACCESS_DENIED = "access_denied"
    CONFIG_CHANGE = "config_change"
    DATA_ACCESS = "data_access"
    SYSTEM_ALERT = "system_alert"
    COMPLIANCE_VIOLATION = "compliance_violation"


class SecurityEventSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventBase(BaseModel):
    event_id: str
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    timestamp: datetime
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: str
    details: Dict[str, Any]
    status: str


class SecurityEventCreate(SecurityEventBase):
    pass


class SecurityEvent(SecurityEventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditLogBase(BaseModel):
    log_id: str
    timestamp: datetime
    user_id: int
    user_role: str
    action: str
    resource_type: str
    resource_id: int
    resource_name: str
    changes: Optional[Dict[str, Any]] = None
    ip_address: str
    user_agent: str
    status: str
    details: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLog(AuditLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityPolicyBase(BaseModel):
    policy_id: str
    name: str
    description: str
    policy_type: str
    rules: Dict[str, Any]
    is_active: bool = True
    version: int = 1
    created_by: str


class SecurityPolicyCreate(SecurityPolicyBase):
    pass


class SecurityPolicy(SecurityPolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccessControlRuleBase(BaseModel):
    rule_id: str
    resource_type: str
    resource_id: Optional[int] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    permission: str
    conditions: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_by: str


class AccessControlRuleCreate(AccessControlRuleBase):
    pass


class AccessControlRule(AccessControlRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncidentBase(BaseModel):
    incident_id: str
    title: str
    description: str
    severity: SecurityEventSeverity
    status: str
    assigned_to: Optional[str] = None
    reported_by: str
    reported_at: datetime
    resolved_at: Optional[datetime] = None
    root_cause: Optional[str] = None
    remediation: Optional[str] = None
    affected_systems: Dict[str, Any]


class IncidentCreate(IncidentBase):
    pass


class Incident(IncidentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplianceCheckBase(BaseModel):
    check_id: str
    standard: str
    requirement: str
    description: str
    status: str
    evidence: Optional[Dict[str, Any]] = None
    last_check: datetime
    next_check: datetime


class ComplianceCheckCreate(ComplianceCheckBase):
    pass


class ComplianceCheck(ComplianceCheckBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EncryptionKeyBase(BaseModel):
    key_id: str
    key_type: str
    algorithm: str
    key_data: str
    key_version: int
    is_active: bool = True
    expires_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None


class EncryptionKeyCreate(EncryptionKeyBase):
    pass


class EncryptionKey(EncryptionKeyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
