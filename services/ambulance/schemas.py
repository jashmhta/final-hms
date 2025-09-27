from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AmbulanceBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class AmbulanceCreate(AmbulanceBase):
    pass


class AmbulanceUpdate(AmbulanceBase):
    pass


class AmbulanceResponse(AmbulanceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
