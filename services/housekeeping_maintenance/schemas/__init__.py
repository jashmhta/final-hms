import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


# CleaningTask Schemas
class CleaningTaskBase(BaseModel):
    description: str
    assigned_to: Optional[int]
    scheduled_date: datetime
    status: Optional[TaskStatus] = TaskStatus.PENDING


class CleaningTaskCreate(CleaningTaskBase):
    pass


class CleaningTaskUpdate(BaseModel):
    description: Optional[str]
    assigned_to: Optional[int]
    scheduled_date: Optional[datetime]
    status: Optional[TaskStatus]


class CleaningTaskRead(CleaningTaskBase):
    id: int

    class Config:
        orm_mode = True


# MaintenanceRequest Schemas
class MaintenanceRequestBase(BaseModel):
    asset_id: int
    description: str
    priority: str
    status: Optional[str] = "OPEN"


class MaintenanceRequestCreate(MaintenanceRequestBase):
    pass


class MaintenanceRequestUpdate(BaseModel):
    asset_id: Optional[int]
    description: Optional[str]
    priority: Optional[str]
    status: Optional[str]


class MaintenanceRequestRead(MaintenanceRequestBase):
    id: int

    class Config:
        orm_mode = True


# AssetUpkeep Schemas
class AssetUpkeepBase(BaseModel):
    asset_name: str
    last_maintenance_date: Optional[datetime]
    next_due_date: Optional[datetime]
    status: Optional[str] = "OK"


class AssetUpkeepCreate(AssetUpkeepBase):
    pass


class AssetUpkeepUpdate(BaseModel):
    asset_name: Optional[str]
    last_maintenance_date: Optional[datetime]
    next_due_date: Optional[datetime]
    status: Optional[str]


class AssetUpkeepRead(AssetUpkeepBase):
    id: int

    class Config:
        orm_mode = True
