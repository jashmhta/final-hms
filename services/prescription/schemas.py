from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PrescriptionBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionUpdate(PrescriptionBase):
    pass


class PrescriptionResponse(PrescriptionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
