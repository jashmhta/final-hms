from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
Base = declarative_base()
class HMSBaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    metadata = Column(JSON, nullable=True)  
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata
        }
class AuditMixin:
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
class SoftDeleteMixin:
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by = Column(String(100), nullable=True)
    def soft_delete(self, user_id: str = None):
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id
        self.is_active = False
    def restore(self):
        self.deleted_at = None
        self.deleted_by = None
        self.is_active = True