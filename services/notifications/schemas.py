from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class NotificationsBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class NotificationsCreate(NotificationsBase):
    pass
class NotificationsUpdate(NotificationsBase):
    pass
class NotificationsResponse(NotificationsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True