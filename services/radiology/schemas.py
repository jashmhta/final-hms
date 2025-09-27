from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RadiologyBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class RadiologyCreate(RadiologyBase):
    pass


class RadiologyUpdate(RadiologyBase):
    pass


class RadiologyResponse(RadiologyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
