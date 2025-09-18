from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class ErpBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class ErpCreate(ErpBase):
    pass
class ErpUpdate(ErpBase):
    pass
class ErpResponse(ErpBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True