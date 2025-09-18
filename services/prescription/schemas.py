from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class PrescriptionBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class PrescriptionCreate(PrescriptionBase):
    pass
class PrescriptionUpdate(PrescriptionBase):
    pass
class PrescriptionResponse(PrescriptionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True