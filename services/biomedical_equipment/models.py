from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
Base = declarative_base()
class EquipmentStatus(enum.Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OUT_OF_ORDER = "out_of_order"
    RETIRED = "retired"
class EquipmentCategory(enum.Enum):
    DIAGNOSTIC = "diagnostic"
    THERAPEUTIC = "therapeutic"
    MONITORING = "monitoring"
    SURGICAL = "surgical"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
class MaintenanceType(enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    CALIBRATION = "calibration"
class BiomedicalEquipment(Base):
    __tablename__ = "biomedical_equipment"
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String, unique=True)
    equipment_name = Column(String)
    category = Column(Enum(EquipmentCategory))
    manufacturer = Column(String)
    model = Column(String)
    serial_number = Column(String, unique=True)
    location = Column(String)
    department = Column(String)
    purchase_date = Column(DateTime)
    warranty_expiry = Column(DateTime, nullable=True)
    status = Column(Enum(EquipmentStatus), default=EquipmentStatus.OPERATIONAL)
    specifications = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class EquipmentMaintenance(Base):
    __tablename__ = "equipment_maintenance"
    id = Column(Integer, primary_key=True, index=True)
    maintenance_id = Column(String, unique=True)
    equipment_id = Column(Integer, ForeignKey("biomedical_equipment.id"))
    maintenance_type = Column(Enum(MaintenanceType))
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime, nullable=True)
    performed_by = Column(String)  
    description = Column(Text)
    findings = Column(Text, nullable=True)
    actions_taken = Column(Text, nullable=True)
    cost = Column(Float, nullable=True)
    status = Column(String)  
    next_maintenance_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    equipment = relationship("BiomedicalEquipment")
class EquipmentCalibration(Base):
    __tablename__ = "equipment_calibration"
    id = Column(Integer, primary_key=True, index=True)
    calibration_id = Column(String, unique=True)
    equipment_id = Column(Integer, ForeignKey("biomedical_equipment.id"))
    calibration_date = Column(DateTime)
    calibrated_by = Column(String)
    calibration_standard = Column(String)
    results = Column(JSON)  
    status = Column(String)  
    next_calibration_date = Column(DateTime)
    certificate_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    equipment = relationship("BiomedicalEquipment")
class EquipmentIncident(Base):
    __tablename__ = "equipment_incidents"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True)
    equipment_id = Column(Integer, ForeignKey("biomedical_equipment.id"))
    incident_date = Column(DateTime)
    reported_by = Column(String)
    description = Column(Text)
    severity = Column(String)  
    impact = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    status = Column(String)  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    equipment = relationship("BiomedicalEquipment")
class EquipmentTraining(Base):
    __tablename__ = "equipment_training"
    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(String, unique=True)
    equipment_id = Column(Integer, ForeignKey("biomedical_equipment.id"))
    staff_member = Column(String)
    training_date = Column(DateTime)
    trainer = Column(String)
    training_type = Column(String)  
    status = Column(String)  
    certificate_number = Column(String, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    equipment = relationship("BiomedicalEquipment")
class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(String, unique=True)
    vendor_name = Column(String)
    contact_person = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(Text)
    service_type = Column(String)  
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)