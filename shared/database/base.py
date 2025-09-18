"""
Shared Database Base Models and Utilities
Eliminates redundant model patterns across all services.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr


class BaseTimestampMixin:
    """Mixin for common timestamp fields - eliminates redundant timestamp definitions."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def age(self) -> Optional[float]:
        """Calculate age of record in hours."""
        if not self.created_at:
            return None
        return (datetime.utcnow() - self.created_at).total_seconds() / 3600


class BaseActiveMixin:
    """Mixin for active/inactive status fields - eliminates redundant status patterns."""

    is_active = Column(Boolean, default=True, nullable=False, index=True)


class BaseAuditMixin:
    """Mixin for audit trail fields - eliminates redundant audit patterns."""

    created_by = Column(String(100), nullable=True, index=True)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BaseIdentificationMixin:
    """Mixin for common identification fields - eliminates redundant ID patterns."""

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=True, index=True)

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()


# Base class with all common mixins
Base = declarative_base()


class HMSBaseModel(Base, BaseTimestampMixin, BaseActiveMixin, BaseIdentificationMixin):
    """Base model for all HMS entities - consolidates all common patterns."""

    __abstract__ = True

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)  # For additional flexible data

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, name='{self.name}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary - eliminates redundant serialization code."""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata
        }


class AuditModel(Base, BaseAuditMixin):
    """Base model for audit entities - consolidates audit patterns."""

    __abstract__ = True

    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)


# Common table configurations
class TableConfig:
    """Centralized table configuration patterns."""

    # Common column configurations
    TIMESTAMP_COLUMNS = {
        'created_at': Column(DateTime, default=datetime.utcnow, nullable=False),
        'updated_at': Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    }

    STATUS_COLUMNS = {
        'is_active': Column(Boolean, default=True, nullable=False),
        'is_deleted': Column(Boolean, default=False, nullable=False)
    }

    IDENTITY_COLUMNS = {
        'id': Column(Integer, primary_key=True, index=True),
        'uuid': Column(String(36), unique=True, nullable=True, index=True)
    }

    # Common indexes
    COMMON_INDEXES = [
        'created_at',
        'updated_at',
        'is_active',
        'name'
    ]

    @classmethod
    def get_table_name(cls, class_name: str) -> str:
        """Generate standardized table names."""
        # Convert CamelCase to snake_case and add prefix
        import re
        snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', class_name).lower()
        return f"hms_{snake_case}"


# Database utility functions
def get_db_session_config():
    """Standard database session configuration - eliminates redundant session setup."""
    return {
        'autocommit': False,
        'autoflush': False,
        'expire_on_commit': False
    }


def common_column_types():
    """Common column type definitions."""
    return {
        'id': Integer,
        'name': String(255),
        'description': Text,
        'status': String(50),
        'metadata': JSON,
        'created_at': DateTime,
        'updated_at': DateTime
    }


def get_standard_indexes():
    """Standard index patterns."""
    return [
        {'column': 'created_at', 'name': 'idx_created_at'},
        {'column': 'updated_at', 'name': 'idx_updated_at'},
        {'column': 'is_active', 'name': 'idx_is_active'},
        {'column': 'name', 'name': 'idx_name'},
    ]


# Common constraints
class CommonConstraints:
    """Centralized constraint definitions."""

    @staticmethod
    def name_length(min_length: int = 2, max_length: int = 255):
        """Common name length constraint."""
        return f"LENGTH(name) BETWEEN {min_length} AND {max_length}"

    @staticmethod
    def positive_id():
        """Positive ID constraint."""
        return "id > 0"

    @staticmethod
    def valid_uuid():
        """Valid UUID format constraint."""
        return "uuid ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'"