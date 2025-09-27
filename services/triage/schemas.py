from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TriageBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class TriageCreate(TriageBase):
    pass


class TriageUpdate(TriageBase):
    pass


class TriageResponse(TriageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
