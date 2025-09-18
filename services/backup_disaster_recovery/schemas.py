from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
class BackupJobBase(BaseModel):
    job_name: str
    description: str
    schedule_type: str
    schedule_config: Dict[str, Any]
    target_type: str
    target_config: Dict[str, Any]
    storage_type: str
    storage_config: Dict[str, Any]
class BackupJobCreate(BackupJobBase):
    encryption_enabled: bool = True
    retention_days: int = 30
    is_active: bool = True
class BackupJob(BackupJobBase):
    id: int
    encryption_enabled: bool
    retention_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class BackupExecutionBase(BaseModel):
    job_id: int
    status: str
    start_time: datetime
class BackupExecutionCreate(BackupExecutionBase):
    pass
class BackupExecution(BackupExecutionBase):
    id: int
    execution_id: str
    end_time: Optional[datetime] = None
    size_bytes: Optional[int] = None
    duration_seconds: Optional[int] = None
    backup_path: Optional[str] = None
    error_message: Optional[str] = None
    checksum: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True
class RecoveryJobBase(BaseModel):
    backup_execution_id: int
    recovery_type: str
    target_config: Dict[str, Any]
class RecoveryJobCreate(RecoveryJobBase):
    pass
class RecoveryJob(RecoveryJobBase):
    id: int
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    recovery_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True
class DisasterRecoveryPlanBase(BaseModel):
    plan_name: str
    description: str
    rpo_minutes: int
    rto_minutes: int
    priority_level: str
    components: Dict[str, Any]
    procedures: str
    contact_persons: Dict[str, Any]
class DisasterRecoveryPlanCreate(DisasterRecoveryPlanBase):
    is_active: bool = True
class DisasterRecoveryPlan(DisasterRecoveryPlanBase):
    id: int
    last_tested: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class StorageConfigurationBase(BaseModel):
    name: str
    provider: str
    config: Dict[str, Any]
class StorageConfigurationCreate(StorageConfigurationBase):
    is_default: bool = False
    is_active: bool = True
class StorageConfiguration(StorageConfigurationBase):
    id: int
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class BackupRequest(BaseModel):
    job_id: int
    manual_trigger: bool = False
class RecoveryRequest(BaseModel):
    backup_execution_id: int
    recovery_type: str
    target_config: Dict[str, Any]
class TestRecoveryRequest(BaseModel):
    plan_id: int
    test_scenario: str