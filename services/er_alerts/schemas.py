from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class ErAlertsBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class ErAlertsCreate(ErAlertsBase):
    pass
class ErAlertsUpdate(ErAlertsBase):
    pass
class ErAlertsResponse(ErAlertsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True