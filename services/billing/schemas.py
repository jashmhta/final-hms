from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class BillingBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class BillingCreate(BillingBase):
    pass
class BillingUpdate(BillingBase):
    pass
class BillingResponse(BillingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True