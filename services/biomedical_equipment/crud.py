"""
crud module
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import models
import schemas
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session


def get_equipment(db: Session, equipment_id: int):
    return (
        db.query(models.BiomedicalEquipment)
        .filter(models.BiomedicalEquipment.id == equipment_id)
        .first()
    )


def get_equipment_by_equipment_id(db: Session, equipment_id_str: str):
    return (
        db.query(models.BiomedicalEquipment)
        .filter(models.BiomedicalEquipment.equipment_id == equipment_id_str)
        .first()
    )


def get_equipment_list(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.BiomedicalEquipment)
        .filter(models.BiomedicalEquipment.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_equipment_by_status(db: Session, status: schemas.EquipmentStatus):
    return (
        db.query(models.BiomedicalEquipment)
        .filter(
            models.BiomedicalEquipment.status == status,
            models.BiomedicalEquipment.is_active == True,
        )
        .all()
    )


def get_equipment_by_category(db: Session, category: schemas.EquipmentCategory):
    return (
        db.query(models.BiomedicalEquipment)
        .filter(
            models.BiomedicalEquipment.category == category,
            models.BiomedicalEquipment.is_active == True,
        )
        .all()
    )


def get_equipment_by_department(db: Session, department: str):
    return (
        db.query(models.BiomedicalEquipment)
        .filter(
            models.BiomedicalEquipment.department == department,
            models.BiomedicalEquipment.is_active == True,
        )
        .all()
    )


def create_equipment(db: Session, equipment: schemas.BiomedicalEquipmentCreate):
    db_equipment = models.BiomedicalEquipment(**equipment.dict())
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment


def update_equipment_status(
    db: Session, equipment_id: int, status: schemas.EquipmentStatus
):
    db_equipment = (
        db.query(models.BiomedicalEquipment)
        .filter(models.BiomedicalEquipment.id == equipment_id)
        .first()
    )
    if db_equipment:
        db_equipment.status = status
        db_equipment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_equipment)
    return db_equipment


def get_maintenance(db: Session, maintenance_id: int):
    return (
        db.query(models.EquipmentMaintenance)
        .filter(models.EquipmentMaintenance.id == maintenance_id)
        .first()
    )


def get_maintenance_by_equipment(db: Session, equipment_id: int):
    return (
        db.query(models.EquipmentMaintenance)
        .filter(models.EquipmentMaintenance.equipment_id == equipment_id)
        .all()
    )


def get_upcoming_maintenance(db: Session, days_ahead: int = 30):
    end_date = datetime.utcnow() + timedelta(days=days_ahead)
    return (
        db.query(models.EquipmentMaintenance)
        .filter(
            models.EquipmentMaintenance.scheduled_date <= end_date,
            models.EquipmentMaintenance.status.in_(["scheduled", "in_progress"]),
        )
        .all()
    )


def get_overdue_maintenance(db: Session):
    today = datetime.utcnow().date()
    return (
        db.query(models.EquipmentMaintenance)
        .filter(
            models.EquipmentMaintenance.scheduled_date < today,
            models.EquipmentMaintenance.status.in_(["scheduled", "in_progress"]),
        )
        .all()
    )


def create_maintenance(db: Session, maintenance: schemas.EquipmentMaintenanceCreate):
    db_maintenance = models.EquipmentMaintenance(**maintenance.dict())
    db.add(db_maintenance)
    db.commit()
    db.refresh(db_maintenance)
    return db_maintenance


def complete_maintenance(
    db: Session,
    maintenance_id: int,
    findings: str,
    actions_taken: str,
    next_maintenance_date: Optional[datetime] = None,
):
    db_maintenance = (
        db.query(models.EquipmentMaintenance)
        .filter(models.EquipmentMaintenance.id == maintenance_id)
        .first()
    )
    if db_maintenance:
        db_maintenance.status = "completed"
        db_maintenance.completed_date = datetime.utcnow()
        db_maintenance.findings = findings
        db_maintenance.actions_taken = actions_taken
        if next_maintenance_date:
            db_maintenance.next_maintenance_date = next_maintenance_date
        db_maintenance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_maintenance)
    return db_maintenance


def get_calibration(db: Session, calibration_id: int):
    return (
        db.query(models.EquipmentCalibration)
        .filter(models.EquipmentCalibration.id == calibration_id)
        .first()
    )


def get_calibration_by_equipment(db: Session, equipment_id: int):
    return (
        db.query(models.EquipmentCalibration)
        .filter(models.EquipmentCalibration.equipment_id == equipment_id)
        .all()
    )


def get_overdue_calibrations(db: Session):
    today = datetime.utcnow().date()
    return (
        db.query(models.EquipmentCalibration)
        .filter(models.EquipmentCalibration.next_calibration_date < today)
        .all()
    )


def create_calibration(db: Session, calibration: schemas.EquipmentCalibrationCreate):
    db_calibration = models.EquipmentCalibration(**calibration.dict())
    db.add(db_calibration)
    db.commit()
    db.refresh(db_calibration)
    return db_calibration


def get_incident(db: Session, incident_id: int):
    return (
        db.query(models.EquipmentIncident)
        .filter(models.EquipmentIncident.id == incident_id)
        .first()
    )


def get_incidents_by_equipment(db: Session, equipment_id: int):
    return (
        db.query(models.EquipmentIncident)
        .filter(models.EquipmentIncident.equipment_id == equipment_id)
        .all()
    )


def get_open_incidents(db: Session):
    return (
        db.query(models.EquipmentIncident)
        .filter(models.EquipmentIncident.status.in_(["open", "investigating"]))
        .all()
    )


def create_incident(db: Session, incident: schemas.EquipmentIncidentCreate):
    db_incident = models.EquipmentIncident(**incident.dict())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident


def resolve_incident(db: Session, incident_id: int, resolution: str):
    db_incident = (
        db.query(models.EquipmentIncident)
        .filter(models.EquipmentIncident.id == incident_id)
        .first()
    )
    if db_incident:
        db_incident.status = "resolved"
        db_incident.resolution = resolution
        db_incident.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_incident)
    return db_incident


def get_training(db: Session, training_id: int):
    return (
        db.query(models.EquipmentTraining)
        .filter(models.EquipmentTraining.id == training_id)
        .first()
    )


def get_training_by_equipment(db: Session, equipment_id: int):
    return (
        db.query(models.EquipmentTraining)
        .filter(models.EquipmentTraining.equipment_id == equipment_id)
        .all()
    )


def get_training_by_staff(db: Session, staff_member: str):
    return (
        db.query(models.EquipmentTraining)
        .filter(models.EquipmentTraining.staff_member == staff_member)
        .all()
    )


def create_training(db: Session, training: schemas.EquipmentTrainingCreate):
    db_training = models.EquipmentTraining(**training.dict())
    db.add(db_training)
    db.commit()
    db.refresh(db_training)
    return db_training


def get_vendor(db: Session, vendor_id: int):
    return db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()


def get_vendors(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Vendor)
        .filter(models.Vendor.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_vendor(db: Session, vendor: schemas.VendorCreate):
    db_vendor = models.Vendor(**vendor.dict())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor


def get_equipment_statistics(db: Session):
    total_equipment = (
        db.query(models.BiomedicalEquipment)
        .filter(models.BiomedicalEquipment.is_active == True)
        .count()
    )
    operational_equipment = (
        db.query(models.BiomedicalEquipment)
        .filter(
            models.BiomedicalEquipment.status == models.EquipmentStatus.OPERATIONAL,
            models.BiomedicalEquipment.is_active == True,
        )
        .count()
    )
    maintenance_required = (
        db.query(models.BiomedicalEquipment)
        .filter(
            models.BiomedicalEquipment.status == models.EquipmentStatus.MAINTENANCE,
            models.BiomedicalEquipment.is_active == True,
        )
        .count()
    )
    out_of_order = (
        db.query(models.BiomedicalEquipment)
        .filter(
            models.BiomedicalEquipment.status == models.EquipmentStatus.OUT_OF_ORDER,
            models.BiomedicalEquipment.is_active == True,
        )
        .count()
    )
    overdue_maintenance = len(get_overdue_maintenance(db))
    overdue_calibrations = len(get_overdue_calibrations(db))
    total_incidents = db.query(models.EquipmentIncident).count()
    open_incidents = len(get_open_incidents(db))
    return {
        "total_equipment": total_equipment,
        "operational_equipment": operational_equipment,
        "maintenance_required": maintenance_required,
        "out_of_order": out_of_order,
        "overdue_maintenance": overdue_maintenance,
        "overdue_calibration": overdue_calibrations,
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
    }


def get_equipment_dashboard(db: Session):
    status_counts = {}
    for status in models.EquipmentStatus:
        count = (
            db.query(models.BiomedicalEquipment)
            .filter(
                models.BiomedicalEquipment.status == status,
                models.BiomedicalEquipment.is_active == True,
            )
            .count()
        )
        status_counts[status.value] = count
    upcoming_maintenance = len(get_upcoming_maintenance(db, 7))
    overdue_calibrations = len(get_overdue_calibrations(db))
    recent_incidents = (
        db.query(models.EquipmentIncident)
        .filter(
            models.EquipmentIncident.created_at
            >= datetime.utcnow() - timedelta(days=30)
        )
        .count()
    )
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    monthly_maintenance = (
        db.query(models.EquipmentMaintenance)
        .filter(
            models.EquipmentMaintenance.completed_date >= month_start,
            models.EquipmentMaintenance.cost.isnot(None),
        )
        .all()
    )
    maintenance_cost_monthly = sum(m.cost for m in monthly_maintenance if m.cost)
    return {
        "equipment_status_summary": status_counts,
        "upcoming_maintenance": upcoming_maintenance,
        "overdue_calibrations": overdue_calibrations,
        "recent_incidents": recent_incidents,
        "maintenance_cost_monthly": maintenance_cost_monthly,
    }
