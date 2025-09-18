from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class PatientsBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class PatientsCreate(PatientsBase):
    pass
class PatientsUpdate(PatientsBase):
    pass
class PatientsResponse(PatientsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True