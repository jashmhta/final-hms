"""
crud module
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import models
import schemas
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session


def get_doctor(db: Session, doctor_id: int):
    return db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()


def get_doctor_by_doctor_id(db: Session, doctor_id_str: str):
    return (
        db.query(models.Doctor).filter(models.Doctor.doctor_id == doctor_id_str).first()
    )


def get_doctors(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Doctor)
        .filter(models.Doctor.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_doctors_by_specialization(
    db: Session, specialization: schemas.DoctorSpecialization
):
    return (
        db.query(models.Doctor)
        .filter(
            models.Doctor.specialization == specialization,
            models.Doctor.is_active == True,
        )
        .all()
    )


def get_available_doctors(
    db: Session, specialization: Optional[schemas.DoctorSpecialization] = None
):
    query = db.query(models.Doctor).filter(
        models.Doctor.is_active == True, models.Doctor.is_available == True
    )
    if specialization:
        query = query.filter(models.Doctor.specialization == specialization)
    return query.all()


def create_doctor(db: Session, doctor: schemas.DoctorCreate):
    db_doctor = models.Doctor(**doctor.dict())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor


def update_doctor(db: Session, doctor_id: int, doctor_update: Dict[str, Any]):
    db_doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if db_doctor:
        for key, value in doctor_update.items():
            setattr(db_doctor, key, value)
        db_doctor.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_doctor)
    return db_doctor


def get_department(db: Session, department_id: int):
    return (
        db.query(models.Department)
        .filter(models.Department.id == department_id)
        .first()
    )


def get_departments(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Department)
        .filter(models.Department.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_department(db: Session, department: schemas.DepartmentCreate):
    db_department = models.Department(**department.dict())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department


def get_doctor_schedule(db: Session, doctor_id: int, day_of_week: Optional[int] = None):
    query = db.query(models.DoctorSchedule).filter(
        models.DoctorSchedule.doctor_id == doctor_id
    )
    if day_of_week is not None:
        query = query.filter(models.DoctorSchedule.day_of_week == day_of_week)
    return query.all()


def create_doctor_schedule(db: Session, schedule: schemas.DoctorScheduleCreate):
    db_schedule = models.DoctorSchedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def get_doctor_leaves(db: Session, doctor_id: int, status: Optional[str] = None):
    query = db.query(models.DoctorLeave).filter(
        models.DoctorLeave.doctor_id == doctor_id
    )
    if status:
        query = query.filter(models.DoctorLeave.status == status)
    return query.all()


def create_doctor_leave(db: Session, leave: schemas.DoctorLeaveCreate):
    db_leave = models.DoctorLeave(**leave.dict())
    db.add(db_leave)
    db.commit()
    db.refresh(db_leave)
    return db_leave


def approve_doctor_leave(db: Session, leave_id: int, approved_by: str):
    db_leave = (
        db.query(models.DoctorLeave).filter(models.DoctorLeave.id == leave_id).first()
    )
    if db_leave:
        db_leave.status = "approved"
        db_leave.approved_by = approved_by
        db_leave.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_leave)
    return db_leave


def get_doctor_performance(
    db: Session,
    doctor_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    query = db.query(models.DoctorPerformance).filter(
        models.DoctorPerformance.doctor_id == doctor_id
    )
    if start_date:
        query = query.filter(models.DoctorPerformance.date >= start_date)
    if end_date:
        query = query.filter(models.DoctorPerformance.date <= end_date)
    return query.all()


def create_doctor_performance(
    db: Session, performance: schemas.DoctorPerformanceCreate
):
    db_performance = models.DoctorPerformance(**performance.dict())
    db.add(db_performance)
    db.commit()
    db.refresh(db_performance)
    return db_performance


def get_doctor_dashboard(db: Session, doctor_id: int):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        return None
    today = datetime.utcnow().date()
    today_appointments = 0
    pending_consultations = 0
    month_start = today.replace(day=1)
    monthly_performance = (
        db.query(models.DoctorPerformance)
        .filter(
            models.DoctorPerformance.doctor_id == doctor_id,
            models.DoctorPerformance.date >= month_start,
        )
        .all()
    )
    monthly_revenue = sum(p.revenue_generated for p in monthly_performance)
    satisfaction_scores = [
        p.patient_satisfaction_score
        for p in monthly_performance
        if p.patient_satisfaction_score
    ]
    avg_satisfaction = (
        sum(satisfaction_scores) / len(satisfaction_scores)
        if satisfaction_scores
        else 0.0
    )
    upcoming_leaves = (
        db.query(models.DoctorLeave)
        .filter(
            models.DoctorLeave.doctor_id == doctor_id,
            models.DoctorLeave.start_date > datetime.utcnow(),
            models.DoctorLeave.status == "approved",
        )
        .count()
    )
    department = (
        db.query(models.Department)
        .filter(models.Department.id == doctor.department_id)
        .first()
    )
    return {
        "doctor_id": doctor_id,
        "doctor_name": f"{doctor.first_name} {doctor.last_name}",
        "specialization": doctor.specialization.value,
        "department": department.department_name if department else "Unknown",
        "today_appointments": today_appointments,
        "pending_consultations": pending_consultations,
        "monthly_revenue": monthly_revenue,
        "patient_satisfaction": avg_satisfaction,
        "upcoming_leaves": upcoming_leaves,
    }


def get_doctor_statistics(db: Session):
    total_doctors = (
        db.query(models.Doctor).filter(models.Doctor.is_active == True).count()
    )
    active_doctors = (
        db.query(models.Doctor)
        .filter(models.Doctor.is_active == True, models.Doctor.is_available == True)
        .count()
    )
    doctors_on_leave = (
        db.query(models.DoctorLeave)
        .filter(
            models.DoctorLeave.start_date <= datetime.utcnow(),
            models.DoctorLeave.end_date >= datetime.utcnow(),
            models.DoctorLeave.status == "approved",
        )
        .count()
    )
    doctors = db.query(models.Doctor).filter(models.Doctor.is_active == True).all()
    avg_consultation_fee = (
        sum(d.consultation_fee for d in doctors) / len(doctors) if doctors else 0.0
    )
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    monthly_performance = (
        db.query(models.DoctorPerformance)
        .filter(models.DoctorPerformance.date >= month_start)
        .all()
    )
    total_monthly_revenue = sum(p.revenue_generated for p in monthly_performance)
    return {
        "total_doctors": total_doctors,
        "active_doctors": active_doctors,
        "doctors_on_leave": doctors_on_leave,
        "average_consultation_fee": avg_consultation_fee,
        "total_monthly_revenue": total_monthly_revenue,
    }
