from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FacilitiesBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class FacilitiesCreate(FacilitiesBase):
    pass


class FacilitiesUpdate(FacilitiesBase):
    pass


class FacilitiesResponse(FacilitiesBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
