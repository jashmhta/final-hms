from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class OperationTheatreBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class OperationTheatreCreate(OperationTheatreBase):
    pass
class OperationTheatreUpdate(OperationTheatreBase):
    pass
class OperationTheatreResponse(OperationTheatreBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True