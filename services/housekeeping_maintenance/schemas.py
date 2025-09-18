from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
class MaintenanceStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
class MaintenanceType(str, Enum):
    CLEANING = "cleaning"
    REPAIR = "repair"
    INSPECTION = "inspection"
    PREVENTIVE = "preventive"
    EMERGENCY = "emergency"
class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
class HousekeepingTaskBase(BaseModel):
    task_id: str
    task_name: str
    description: str
    task_type: str
    assigned_to: str
    location: str
    priority: TaskPriority = TaskPriority.MEDIUM
    scheduled_date: datetime
    estimated_duration: int
class HousekeepingTaskCreate(HousekeepingTaskBase):
    pass
class HousekeepingTask(HousekeepingTaskBase):
    id: int
    completed_date: Optional[datetime] = None
    status: str
    actual_duration: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class MaintenanceRequestBase(BaseModel):
    request_id: str
    request_type: MaintenanceType
    title: str
    description: str
    location: str
    priority: TaskPriority = TaskPriority.MEDIUM
    requested_by: str
    assigned_to: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    estimated_cost: Optional[float] = None
class MaintenanceRequestCreate(MaintenanceRequestBase):
    pass
class MaintenanceRequest(MaintenanceRequestBase):
    id: int
    completed_date: Optional[datetime] = None
    status: MaintenanceStatus
    actual_cost: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class EquipmentBase(BaseModel):
    equipment_id: str
    equipment_name: str
    equipment_type: str
    location: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None
class EquipmentCreate(EquipmentBase):
    pass
class Equipment(EquipmentBase):
    id: int
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class StaffBase(BaseModel):
    staff_id: str
    first_name: str
    last_name: str
    role: str
    department: str
    contact_number: str
    email: Optional[str] = None
    shift: str
class StaffCreate(StaffBase):
    pass
class Staff(StaffBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class CleaningScheduleBase(BaseModel):
    schedule_id: str
    area: str
    cleaning_type: str
    assigned_staff: str
    scheduled_time: str
    frequency: str
class CleaningScheduleCreate(CleaningScheduleBase):
    pass
class CleaningSchedule(CleaningScheduleBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class MaintenanceStatistics(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    total_requests: int
    completed_requests: int
    pending_requests: int
    total_equipment: int
    operational_equipment: int
    maintenance_required: int
class TaskDashboard(BaseModel):
    today_tasks: int
    overdue_tasks: int
    completed_today: int
    pending_high_priority: int
    staff_utilization: float