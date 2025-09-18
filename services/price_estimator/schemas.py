from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class PriceEstimatorBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class PriceEstimatorCreate(PriceEstimatorBase):
    pass
class PriceEstimatorUpdate(PriceEstimatorBase):
    pass
class PriceEstimatorResponse(PriceEstimatorBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True