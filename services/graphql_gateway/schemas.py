from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class GraphqlGatewayBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
class GraphqlGatewayCreate(GraphqlGatewayBase):
    pass
class GraphqlGatewayUpdate(GraphqlGatewayBase):
    pass
class GraphqlGatewayResponse(GraphqlGatewayBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True