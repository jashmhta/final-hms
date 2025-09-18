from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class ConsentBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class ConsentCreate(ConsentBase):
    pass
class ConsentUpdate(ConsentBase):
    pass
class ConsentResponse(ConsentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True