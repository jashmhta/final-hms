from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class OtSchedulingBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class OtSchedulingCreate(OtSchedulingBase):
    pass
class OtSchedulingUpdate(OtSchedulingBase):
    pass
class OtSchedulingResponse(OtSchedulingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True