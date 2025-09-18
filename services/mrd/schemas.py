from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class MrdBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class MrdCreate(MrdBase):
    pass
class MrdUpdate(MrdBase):
    pass
class MrdResponse(MrdBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True