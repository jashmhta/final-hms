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
    schedule_type = Column(String)  # daily, weekly, monthly, manual
    schedule_config = Column(JSON)  # cron expression or schedule details
    target_type = Column(String)  # database, filesystem, configuration
    target_config = Column(JSON)  # connection details, paths, etc.
    storage_type = Column(String)  # local, s3, azure, google
    storage_config = Column(JSON)  # storage connection details
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
    status = Column(String)  # running, completed, failed, cancelled
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
    recovery_type = Column(String)  # full, partial, point_in_time
    target_config = Column(JSON)  # recovery target details
    status = Column(String)  # running, completed, failed
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
    rpo_minutes = Column(Integer)  # Recovery Point Objective
    rto_minutes = Column(Integer)  # Recovery Time Objective
    priority_level = Column(String)  # critical, high, medium, low
    components = Column(JSON)  # systems and services covered
    procedures = Column(Text)  # recovery procedures
    contact_persons = Column(JSON)  # emergency contacts
    last_tested = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StorageConfiguration(Base):
    __tablename__ = "storage_configurations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    provider = Column(String)  # aws, azure, google, local
    config = Column(JSON)  # connection details
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
