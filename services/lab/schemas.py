from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LabBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class LabCreate(LabBase):
    pass


class LabUpdate(LabBase):
    pass


class LabResponse(LabBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
