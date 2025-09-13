from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BedStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"

class BedType(str, Enum):
    GENERAL = "general"
    ICU = "icu"
    CCU = "ccu"
    PRIVATE = "private"
    SEMI_PRIVATE = "semi_private"

class BedBase(BaseModel):
    bed_number: str
    bed_type: BedType
    ward_id: int
    floor_number: int
    room_number: str
    status: BedStatus = BedStatus.AVAILABLE

class BedCreate(BedBase):
    pass

class Bed(BedBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WardBase(BaseModel):
    ward_name: str
    ward_type: str
    total_beds: int
    available_beds: int

class WardCreate(WardBase):
    pass

class Ward(WardBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BedAssignmentBase(BaseModel):
    bed_id: int
    patient_id: str
    admission_id: str
    notes: Optional[str] = None

class BedAssignmentCreate(BedAssignmentBase):
    pass

class BedAssignment(BedAssignmentBase):
    id: int
    assigned_at: datetime
    discharged_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BedMaintenanceBase(BaseModel):
    bed_id: int
    maintenance_type: str
    description: str
    scheduled_date: datetime

class BedMaintenanceCreate(BedMaintenanceBase):
    pass

class BedMaintenance(BedMaintenanceBase):
    id: int
    completed_date: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BedAvailability(BaseModel):
    ward_id: int
    ward_name: str
    total_beds: int
    available_beds: int
    occupied_beds: int
    maintenance_beds: int

class BedStatistics(BaseModel):
    total_beds: int
    available_beds: int
    occupied_beds: int
    maintenance_beds: int
    occupancy_rate: float