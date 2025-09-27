"""
crud module
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import models
import schemas
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session


def get_housekeeping_task(db: Session, task_id: int):
    return (
        db.query(models.HousekeepingTask)
        .filter(models.HousekeepingTask.id == task_id)
        .first()
    )


def get_housekeeping_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.HousekeepingTask).offset(skip).limit(limit).all()


def get_tasks_by_status(db: Session, status: str):
    return (
        db.query(models.HousekeepingTask)
        .filter(models.HousekeepingTask.status == status)
        .all()
    )


def get_tasks_by_priority(db: Session, priority: schemas.TaskPriority):
    return (
        db.query(models.HousekeepingTask)
        .filter(models.HousekeepingTask.priority == priority)
        .all()
    )


def get_tasks_by_staff(db: Session, staff_member: str):
    return (
        db.query(models.HousekeepingTask)
        .filter(models.HousekeepingTask.assigned_to == staff_member)
        .all()
    )


def create_housekeeping_task(db: Session, task: schemas.HousekeepingTaskCreate):
    db_task = models.HousekeepingTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task_status(
    db: Session, task_id: int, status: str, notes: Optional[str] = None
):
    db_task = (
        db.query(models.HousekeepingTask)
        .filter(models.HousekeepingTask.id == task_id)
        .first()
    )
    if db_task:
        db_task.status = status
        if status == "completed":
            db_task.completed_date = datetime.utcnow()
        if notes:
            db_task.notes = notes
        db_task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_task)
    return db_task


def get_maintenance_request(db: Session, request_id: int):
    return (
        db.query(models.MaintenanceRequest)
        .filter(models.MaintenanceRequest.id == request_id)
        .first()
    )


def get_maintenance_requests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.MaintenanceRequest).offset(skip).limit(limit).all()


def get_requests_by_status(db: Session, status: schemas.MaintenanceStatus):
    return (
        db.query(models.MaintenanceRequest)
        .filter(models.MaintenanceRequest.status == status)
        .all()
    )


def get_requests_by_priority(db: Session, priority: schemas.TaskPriority):
    return (
        db.query(models.MaintenanceRequest)
        .filter(models.MaintenanceRequest.priority == priority)
        .all()
    )


def create_maintenance_request(db: Session, request: schemas.MaintenanceRequestCreate):
    db_request = models.MaintenanceRequest(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


def assign_maintenance_request(
    db: Session, request_id: int, assigned_to: str, scheduled_date: datetime
):
    db_request = (
        db.query(models.MaintenanceRequest)
        .filter(models.MaintenanceRequest.id == request_id)
        .first()
    )
    if db_request:
        db_request.assigned_to = assigned_to
        db_request.scheduled_date = scheduled_date
        db_request.status = models.MaintenanceStatus.SCHEDULED
        db_request.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_request)
    return db_request


def complete_maintenance_request(
    db: Session,
    request_id: int,
    actual_cost: Optional[float] = None,
    notes: Optional[str] = None,
):
    db_request = (
        db.query(models.MaintenanceRequest)
        .filter(models.MaintenanceRequest.id == request_id)
        .first()
    )
    if db_request:
        db_request.status = models.MaintenanceStatus.COMPLETED
        db_request.completed_date = datetime.utcnow()
        if actual_cost:
            db_request.actual_cost = actual_cost
        if notes:
            db_request.notes = notes
        db_request.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_request)
    return db_request


def get_equipment(db: Session, equipment_id: int):
    return (
        db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    )


def get_equipment_by_equipment_id(db: Session, equipment_id_str: str):
    return (
        db.query(models.Equipment)
        .filter(models.Equipment.equipment_id == equipment_id_str)
        .first()
    )


def get_equipment_list(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Equipment)
        .filter(models.Equipment.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_equipment_by_status(db: Session, status: str):
    return (
        db.query(models.Equipment)
        .filter(models.Equipment.status == status, models.Equipment.is_active == True)
        .all()
    )


def get_equipment_due_maintenance(db: Session):
    today = datetime.utcnow().date()
    return (
        db.query(models.Equipment)
        .filter(
            models.Equipment.next_maintenance_date <= today,
            models.Equipment.is_active == True,
        )
        .all()
    )


def create_equipment(db: Session, equipment: schemas.EquipmentCreate):
    db_equipment = models.Equipment(**equipment.dict())
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment


def update_equipment_maintenance(
    db: Session,
    equipment_id: int,
    last_maintenance_date: datetime,
    next_maintenance_date: datetime,
):
    db_equipment = (
        db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    )
    if db_equipment:
        db_equipment.last_maintenance_date = last_maintenance_date
        db_equipment.next_maintenance_date = next_maintenance_date
        db_equipment.status = "operational"
        db_equipment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_equipment)
    return db_equipment


def get_staff(db: Session, staff_id: int):
    return db.query(models.Staff).filter(models.Staff.id == staff_id).first()


def get_staff_by_staff_id(db: Session, staff_id_str: str):
    return db.query(models.Staff).filter(models.Staff.staff_id == staff_id_str).first()


def get_staff_list(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Staff)
        .filter(models.Staff.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_staff_by_role(db: Session, role: str):
    return (
        db.query(models.Staff)
        .filter(models.Staff.role == role, models.Staff.is_active == True)
        .all()
    )


def create_staff(db: Session, staff: schemas.StaffCreate):
    db_staff = models.Staff(**staff.dict())
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff


def get_cleaning_schedule(db: Session, schedule_id: int):
    return (
        db.query(models.CleaningSchedule)
        .filter(models.CleaningSchedule.id == schedule_id)
        .first()
    )


def get_cleaning_schedules(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.CleaningSchedule)
        .filter(models.CleaningSchedule.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_schedules_by_area(db: Session, area: str):
    return (
        db.query(models.CleaningSchedule)
        .filter(
            models.CleaningSchedule.area == area,
            models.CleaningSchedule.is_active == True,
        )
        .all()
    )


def create_cleaning_schedule(db: Session, schedule: schemas.CleaningScheduleCreate):
    db_schedule = models.CleaningSchedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def get_maintenance_statistics(db: Session):
    total_tasks = db.query(models.HousekeepingTask).count()
    completed_tasks = (
        db.query(models.HousekeepingTask)
        .filter(models.HousekeepingTask.status == "completed")
        .count()
    )
    pending_tasks = (
        db.query(models.HousekeepingTask)
        .filter(models.HousekeepingTask.status.in_(["pending", "in_progress"]))
        .count()
    )
    today = datetime.utcnow().date()
    overdue_tasks = (
        db.query(models.HousekeepingTask)
        .filter(
            models.HousekeepingTask.scheduled_date < today,
            models.HousekeepingTask.status.in_(["pending", "in_progress"]),
        )
        .count()
    )
    total_requests = db.query(models.MaintenanceRequest).count()
    completed_requests = (
        db.query(models.MaintenanceRequest)
        .filter(models.MaintenanceRequest.status == models.MaintenanceStatus.COMPLETED)
        .count()
    )
    pending_requests = (
        db.query(models.MaintenanceRequest)
        .filter(
            models.MaintenanceRequest.status.in_(
                [
                    models.MaintenanceStatus.SCHEDULED,
                    models.MaintenanceStatus.IN_PROGRESS,
                ]
            )
        )
        .count()
    )
    total_equipment = (
        db.query(models.Equipment).filter(models.Equipment.is_active == True).count()
    )
    operational_equipment = (
        db.query(models.Equipment)
        .filter(
            models.Equipment.status == "operational", models.Equipment.is_active == True
        )
        .count()
    )
    maintenance_required = (
        db.query(models.Equipment)
        .filter(
            models.Equipment.status == "maintenance", models.Equipment.is_active == True
        )
        .count()
    )
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks,
        "total_requests": total_requests,
        "completed_requests": completed_requests,
        "pending_requests": pending_requests,
        "total_equipment": total_equipment,
        "operational_equipment": operational_equipment,
        "maintenance_required": maintenance_required,
    }


def get_task_dashboard(db: Session):
    today = datetime.utcnow().date()
    today_tasks = (
        db.query(models.HousekeepingTask)
        .filter(
            models.HousekeepingTask.scheduled_date >= today,
            models.HousekeepingTask.scheduled_date < today + timedelta(days=1),
        )
        .count()
    )
    overdue_tasks = (
        db.query(models.HousekeepingTask)
        .filter(
            models.HousekeepingTask.scheduled_date < today,
            models.HousekeepingTask.status.in_(["pending", "in_progress"]),
        )
        .count()
    )
    completed_today = (
        db.query(models.HousekeepingTask)
        .filter(
            models.HousekeepingTask.completed_date >= today,
            models.HousekeepingTask.completed_date < today + timedelta(days=1),
        )
        .count()
    )
    pending_high_priority = (
        db.query(models.HousekeepingTask)
        .filter(
            models.HousekeepingTask.priority == models.TaskPriority.HIGH,
            models.HousekeepingTask.status.in_(["pending", "in_progress"]),
        )
        .count()
    )
    total_staff = db.query(models.Staff).filter(models.Staff.is_active == True).count()
    active_staff = (
        db.query(models.HousekeepingTask)
        .filter(models.HousekeepingTask.status == "in_progress")
        .distinct(models.HousekeepingTask.assigned_to)
        .count()
    )
    staff_utilization = (active_staff / total_staff) if total_staff > 0 else 0.0
    return {
        "today_tasks": today_tasks,
        "overdue_tasks": overdue_tasks,
        "completed_today": completed_today,
        "pending_high_priority": pending_high_priority,
        "staff_utilization": staff_utilization,
    }
