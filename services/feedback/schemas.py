from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class FeedbackBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class FeedbackCreate(FeedbackBase):
    pass
class FeedbackUpdate(FeedbackBase):
    pass
class FeedbackResponse(FeedbackBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True