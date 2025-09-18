from templates.service_models import HMSBaseModel, AuditMixin, SoftDeleteMixin
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
class AmbulanceRecord(HMSBaseModel, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "ambulance_records"
    vehicle_number = Column(String(20), nullable=False, unique=True, index=True)
    vehicle_type = Column(String(50), nullable=False)  
    capacity = Column(Integer, nullable=False)  
    current_location = Column(JSON, nullable=True)  
    status = Column(String(20), nullable=False, default="available")  
    equipment = Column(JSON, nullable=True)  
    staff_assigned = Column(JSON, nullable=True)  
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'vehicle_number': self.vehicle_number,
            'vehicle_type': self.vehicle_type,
            'capacity': self.capacity,
            'current_location': self.current_location,
            'status': self.status,
            'equipment': self.equipment,
            'staff_assigned': self.staff_assigned
        })
        return data