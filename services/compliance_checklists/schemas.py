from pydantic import BaseModel
from typing import Optional
from datetime import datetime
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