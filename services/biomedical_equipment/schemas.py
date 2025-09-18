from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
class EquipmentStatus(str, Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OUT_OF_ORDER = "out_of_order"
    RETIRED = "retired"
class EquipmentCategory(str, Enum):
    DIAGNOSTIC = "diagnostic"
    THERAPEUTIC = "therapeutic"
    MONITORING = "monitoring"
    SURGICAL = "surgical"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
class MaintenanceType(str, Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    CALIBRATION = "calibration"
class BiomedicalEquipmentBase(BaseModel):
    equipment_id: str
    equipment_name: str
    category: EquipmentCategory
    manufacturer: str
    model: str
    serial_number: str
    location: str
    department: str
    purchase_date: datetime
    warranty_expiry: Optional[datetime] = None
    specifications: Optional[Dict[str, Any]] = None
class BiomedicalEquipmentCreate(BiomedicalEquipmentBase):
    pass
class BiomedicalEquipment(BiomedicalEquipmentBase):
    id: int
    status: EquipmentStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class EquipmentMaintenanceBase(BaseModel):
    maintenance_id: str
    equipment_id: int
    maintenance_type: MaintenanceType
    scheduled_date: datetime
    performed_by: str
    description: str
    cost: Optional[float] = None
class EquipmentMaintenanceCreate(EquipmentMaintenanceBase):
    pass
class EquipmentMaintenance(EquipmentMaintenanceBase):
    id: int
    completed_date: Optional[datetime] = None
    findings: Optional[str] = None
    actions_taken: Optional[str] = None
    status: str
    next_maintenance_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class EquipmentCalibrationBase(BaseModel):
    calibration_id: str
    equipment_id: int
    calibration_date: datetime
    calibrated_by: str
    calibration_standard: str
    results: Dict[str, Any]
    next_calibration_date: datetime
    certificate_number: Optional[str] = None
class EquipmentCalibrationCreate(EquipmentCalibrationBase):
    pass
class EquipmentCalibration(EquipmentCalibrationBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class EquipmentIncidentBase(BaseModel):
    incident_id: str
    equipment_id: int
    incident_date: datetime
    reported_by: str
    description: str
    severity: str
    impact: Optional[str] = None
class EquipmentIncidentCreate(EquipmentIncidentBase):
    pass
class EquipmentIncident(EquipmentIncidentBase):
    id: int
    resolution: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class EquipmentTrainingBase(BaseModel):
    training_id: str
    equipment_id: int
    staff_member: str
    training_date: datetime
    trainer: str
    training_type: str
    certificate_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
class EquipmentTrainingCreate(EquipmentTrainingBase):
    pass
class EquipmentTraining(EquipmentTrainingBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class VendorBase(BaseModel):
    vendor_id: str
    vendor_name: str
    contact_person: str
    email: str
    phone: str
    address: str
    service_type: str
class VendorCreate(VendorBase):
    pass
class Vendor(VendorBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class EquipmentStatistics(BaseModel):
    total_equipment: int
    operational_equipment: int
    maintenance_required: int
    out_of_order: int
    overdue_maintenance: int
    overdue_calibration: int
    total_incidents: int
    open_incidents: int
class EquipmentDashboard(BaseModel):
    equipment_status_summary: Dict[str, int]
    upcoming_maintenance: int
    overdue_calibrations: int
    recent_incidents: int
    maintenance_cost_monthly: float