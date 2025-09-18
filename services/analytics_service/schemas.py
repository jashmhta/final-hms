from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class AnalyticsServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class AnalyticsServiceCreate(AnalyticsServiceBase):
    pass
class AnalyticsServiceUpdate(AnalyticsServiceBase):
    pass
class AnalyticsServiceResponse(AnalyticsServiceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True