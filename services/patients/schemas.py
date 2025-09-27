from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PatientsBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class PatientsCreate(PatientsBase):
    pass


class PatientsUpdate(PatientsBase):
    pass


class PatientsResponse(PatientsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
