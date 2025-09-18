from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from typing import List, Optional, Dict, Any
import models
import schemas
def get_bed(db: Session, bed_id: int):
    return db.query(models.Bed).filter(models.Bed.id == bed_id).first()
def get_bed_by_number(db: Session, bed_number: str):
    return db.query(models.Bed).filter(models.Bed.bed_number == bed_number).first()
def get_beds(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Bed).filter(models.Bed.is_active == True).offset(skip).limit(limit).all()
def get_available_beds(db: Session, ward_id: Optional[int] = None):
    query = db.query(models.Bed).filter(
        models.Bed.is_active == True,
        models.Bed.status == models.BedStatus.AVAILABLE
    )
    if ward_id:
        query = query.filter(models.Bed.ward_id == ward_id)
    return query.all()
def create_bed(db: Session, bed: schemas.BedCreate):
    db_bed = models.Bed(**bed.dict())
    db.add(db_bed)
    db.commit()
    db.refresh(db_bed)
    return db_bed
def update_bed_status(db: Session, bed_id: int, status: schemas.BedStatus):
    db_bed = db.query(models.Bed).filter(models.Bed.id == bed_id).first()
    if db_bed:
        db_bed.status = status
        db_bed.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_bed)
    return db_bed
def get_ward(db: Session, ward_id: int):
    return db.query(models.Ward).filter(models.Ward.id == ward_id).first()
def get_wards(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Ward).filter(models.Ward.is_active == True).offset(skip).limit(limit).all()
def create_ward(db: Session, ward: schemas.WardCreate):
    db_ward = models.Ward(**ward.dict())
    db.add(db_ward)
    db.commit()
    db.refresh(db_ward)
    return db_ward
def get_bed_assignment(db: Session, assignment_id: int):
    return db.query(models.BedAssignment).filter(models.BedAssignment.id == assignment_id).first()
def get_active_bed_assignments(db: Session, patient_id: Optional[str] = None):
    query = db.query(models.BedAssignment).filter(models.BedAssignment.is_active == True)
    if patient_id:
        query = query.filter(models.BedAssignment.patient_id == patient_id)
    return query.all()
def create_bed_assignment(db: Session, assignment: schemas.BedAssignmentCreate):
    db_assignment = models.BedAssignment(**assignment.dict())
    db.add(db_assignment)
    bed = db.query(models.Bed).filter(models.Bed.id == assignment.bed_id).first()
    if bed:
        bed.status = models.BedStatus.OCCUPIED
        bed.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_assignment)
    return db_assignment
def discharge_patient(db: Session, assignment_id: int):
    db_assignment = db.query(models.BedAssignment).filter(models.BedAssignment.id == assignment_id).first()
    if db_assignment:
        db_assignment.is_active = False
        db_assignment.discharged_at = datetime.utcnow()
        bed = db.query(models.Bed).filter(models.Bed.id == db_assignment.bed_id).first()
        if bed:
            bed.status = models.BedStatus.AVAILABLE
            bed.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_assignment)
    return db_assignment
def get_bed_maintenance(db: Session, maintenance_id: int):
    return db.query(models.BedMaintenance).filter(models.BedMaintenance.id == maintenance_id).first()
def get_pending_maintenance(db: Session):
    return db.query(models.BedMaintenance).filter(
        models.BedMaintenance.status.in_(["scheduled", "in_progress"])
    ).all()
def create_bed_maintenance(db: Session, maintenance: schemas.BedMaintenanceCreate):
    db_maintenance = models.BedMaintenance(**maintenance.dict())
    db.add(db_maintenance)
    bed = db.query(models.Bed).filter(models.Bed.id == maintenance.bed_id).first()
    if bed:
        bed.status = models.BedStatus.MAINTENANCE
        bed.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_maintenance)
    return db_maintenance
def complete_maintenance(db: Session, maintenance_id: int):
    db_maintenance = db.query(models.BedMaintenance).filter(models.BedMaintenance.id == maintenance_id).first()
    if db_maintenance:
        db_maintenance.status = "completed"
        db_maintenance.completed_date = datetime.utcnow()
        bed = db.query(models.Bed).filter(models.Bed.id == db_maintenance.bed_id).first()
        if bed:
            bed.status = models.BedStatus.AVAILABLE
            bed.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_maintenance)
    return db_maintenance
def get_bed_availability(db: Session, ward_id: Optional[int] = None):
    query = db.query(models.Ward)
    if ward_id:
        query = query.filter(models.Ward.id == ward_id)
    wards = query.all()
    availability = []
    for ward in wards:
        total_beds = db.query(models.Bed).filter(models.Bed.ward_id == ward.id).count()
        available_beds = db.query(models.Bed).filter(
            models.Bed.ward_id == ward.id,
            models.Bed.status == models.BedStatus.AVAILABLE
        ).count()
        occupied_beds = db.query(models.Bed).filter(
            models.Bed.ward_id == ward.id,
            models.Bed.status == models.BedStatus.OCCUPIED
        ).count()
        maintenance_beds = db.query(models.Bed).filter(
            models.Bed.ward_id == ward.id,
            models.Bed.status == models.BedStatus.MAINTENANCE
        ).count()
        availability.append({
            "ward_id": ward.id,
            "ward_name": ward.ward_name,
            "total_beds": total_beds,
            "available_beds": available_beds,
            "occupied_beds": occupied_beds,
            "maintenance_beds": maintenance_beds
        })
    return availability
def get_bed_statistics(db: Session):
    total_beds = db.query(models.Bed).filter(models.Bed.is_active == True).count()
    available_beds = db.query(models.Bed).filter(
        models.Bed.is_active == True,
        models.Bed.status == models.BedStatus.AVAILABLE
    ).count()
    occupied_beds = db.query(models.Bed).filter(
        models.Bed.is_active == True,
        models.Bed.status == models.BedStatus.OCCUPIED
    ).count()
    maintenance_beds = db.query(models.Bed).filter(
        models.Bed.is_active == True,
        models.Bed.status == models.BedStatus.MAINTENANCE
    ).count()
    occupancy_rate = (occupied_beds / total_beds) if total_beds > 0 else 0.0
    return {
        "total_beds": total_beds,
        "available_beds": available_beds,
        "occupied_beds": occupied_beds,
        "maintenance_beds": maintenance_beds,
        "occupancy_rate": occupancy_rate
    }