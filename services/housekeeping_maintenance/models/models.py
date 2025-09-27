"""
models module
"""

from sqlalchemy.types import String, TypeDecorator


class EncryptedString(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value


import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    created_at = None
    updated_at = None


from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
import os
import sys

sys.path.append("/root/hms_app/hmsupdt/backend")
import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class CleaningTask(Base, TimestampMixin):
    __tablename__ = "cleaning_tasks"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(EncryptedString, nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    scheduled_date = Column(DateTime, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    assigned_user = relationship("User", backref="cleaning_tasks")
    __table_args__ = (Index("ix_cleaning_tasks_status", "status"),)


class MaintenanceRequest(Base, TimestampMixin):
    __tablename__ = "maintenance_requests"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, nullable=False)
    description = Column(EncryptedString, nullable=False)
    priority = Column(String, nullable=False)
    status = Column(String, default="OPEN", nullable=False)
    __table_args__ = (Index("ix_maintenance_requests_status", "status"),)


class AssetUpkeep(Base, TimestampMixin):
    __tablename__ = "asset_upkeep"
    id = Column(Integer, primary_key=True, index=True)
    asset_name = Column(String, nullable=False)
    last_maintenance_date = Column(DateTime, nullable=True)
    next_due_date = Column(DateTime, nullable=True)
    status = Column(String, default="OK", nullable=False)
    __table_args__ = (Index("ix_asset_upkeep_status", "status"),)


from sqlalchemy import Column, Integer, String


class UserStub(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
