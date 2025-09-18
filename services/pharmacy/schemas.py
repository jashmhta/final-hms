from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class PharmacyBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class PharmacyCreate(PharmacyBase):
    pass
class PharmacyUpdate(PharmacyBase):
    pass
class PharmacyResponse(PharmacyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True