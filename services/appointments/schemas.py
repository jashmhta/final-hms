from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AppointmentsBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class AppointmentsCreate(AppointmentsBase):
    pass


class AppointmentsUpdate(AppointmentsBase):
    pass


class AppointmentsResponse(AppointmentsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
