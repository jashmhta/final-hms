from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ComplianceChecklistsBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class ComplianceChecklistsCreate(ComplianceChecklistsBase):
    pass


class ComplianceChecklistsUpdate(ComplianceChecklistsBase):
    pass


class ComplianceChecklistsResponse(ComplianceChecklistsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
