from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class AuditCreate(AuditBase):
    pass


class AuditUpdate(AuditBase):
    pass


class AuditResponse(AuditBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
