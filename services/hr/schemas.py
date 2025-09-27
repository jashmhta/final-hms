from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HrBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class HrCreate(HrBase):
    pass


class HrUpdate(HrBase):
    pass


class HrResponse(HrBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
