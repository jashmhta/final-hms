from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class MaintenanceStatus(enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MaintenanceType(enum.Enum):
    CLEANING = "cleaning"
    REPAIR = "repair"
    INSPECTION = "inspection"
    PREVENTIVE = "preventive"
    EMERGENCY = "emergency"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class HousekeepingTask(Base):
    __tablename__ = "housekeeping_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True)
    task_name = Column(String)
    description = Column(Text)
    task_type = Column(String)  # cleaning, sanitization, waste_management, etc.
    assigned_to = Column(String)  # staff member
    location = Column(String)  # ward, room, area
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime, nullable=True)
    status = Column(String)  # pending, in_progress, completed, cancelled
    estimated_duration = Column(Integer)  # minutes
    actual_duration = Column(Integer, nullable=True)  # minutes
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True)
    request_type = Column(Enum(MaintenanceType))
    title = Column(String)
    description = Column(Text)
    location = Column(String)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    requested_by = Column(String)  # staff member or department
    assigned_to = Column(String, nullable=True)  # maintenance staff
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.SCHEDULED)
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String, unique=True)
    equipment_name = Column(String)
    equipment_type = Column(String)
    location = Column(String)
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    purchase_date = Column(DateTime, nullable=True)
    warranty_expiry = Column(DateTime, nullable=True)
    last_maintenance_date = Column(DateTime, nullable=True)
    next_maintenance_date = Column(DateTime, nullable=True)
    status = Column(String)  # operational, maintenance, out_of_order
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Staff(Base):
    __tablename__ = "staff"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(String)  # cleaner, supervisor, maintenance_technician
    department = Column(String)
    contact_number = Column(String)
    email = Column(String, nullable=True)
    shift = Column(String)  # morning, evening, night
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CleaningSchedule(Base):
    __tablename__ = "cleaning_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(String, unique=True)
    area = Column(String)  # ward, room, common_area
    cleaning_type = Column(String)  # daily, weekly, monthly, deep_cleaning
    assigned_staff = Column(String)
    scheduled_time = Column(String)  # time of day
    frequency = Column(String)  # daily, weekly, monthly
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)