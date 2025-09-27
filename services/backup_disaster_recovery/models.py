import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class BackupJob(Base):
    __tablename__ = "backup_jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String, unique=True)
    description = Column(Text)
    schedule_type = Column(String)
    schedule_config = Column(JSON)
    target_type = Column(String)
    target_config = Column(JSON)
    storage_type = Column(String)
    storage_config = Column(JSON)
    encryption_enabled = Column(Boolean, default=True)
    retention_days = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BackupExecution(Base):
    __tablename__ = "backup_executions"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("backup_jobs.id"))
    execution_id = Column(String, unique=True)
    status = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    backup_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    checksum = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    job = relationship("BackupJob")


class RecoveryJob(Base):
    __tablename__ = "recovery_jobs"
    id = Column(Integer, primary_key=True, index=True)
    backup_execution_id = Column(Integer, ForeignKey("backup_executions.id"))
    recovery_type = Column(String)
    target_config = Column(JSON)
    status = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    recovery_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    backup_execution = relationship("BackupExecution")


class DisasterRecoveryPlan(Base):
    __tablename__ = "disaster_recovery_plans"
    id = Column(Integer, primary_key=True, index=True)
    plan_name = Column(String, unique=True)
    description = Column(Text)
    rpo_minutes = Column(Integer)
    rto_minutes = Column(Integer)
    priority_level = Column(String)
    components = Column(JSON)
    procedures = Column(Text)
    contact_persons = Column(JSON)
    last_tested = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StorageConfiguration(Base):
    __tablename__ = "storage_configurations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    provider = Column(String)
    config = Column(JSON)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
