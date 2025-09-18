from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import models
import schemas
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
def get_patient(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()
def get_patient_by_patient_id(db: Session, patient_id_str: str):
    return (
        db.query(models.Patient)
        .filter(models.Patient.patient_id == patient_id_str)
        .first()
    )
def get_patients(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Patient)
        .filter(models.Patient.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )
def create_patient(db: Session, patient: schemas.PatientCreate):
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient
def update_patient(db: Session, patient_id: int, patient_update: Dict[str, Any]):
    db_patient = (
        db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    )
    if db_patient:
        for key, value in patient_update.items():
            setattr(db_patient, key, value)
        db_patient.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_patient)
    return db_patient
def get_doctor(db: Session, doctor_id: int):
    return db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
def get_doctors(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Doctor)
        .filter(models.Doctor.is_available == True)
        .offset(skip)
        .limit(limit)
        .all()
    )
def create_doctor(db: Session, doctor: schemas.DoctorCreate):
    db_doctor = models.Doctor(**doctor.dict())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor
def get_appointment(db: Session, appointment_id: int):
    return (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id)
        .first()
    )
def get_appointments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Appointment).offset(skip).limit(limit).all()
def get_appointments_by_patient(db: Session, patient_id: int):
    return (
        db.query(models.Appointment)
        .filter(models.Appointment.patient_id == patient_id)
        .all()
    )
def get_appointments_by_doctor(
    db: Session, doctor_id: int, date: Optional[datetime] = None
):
    query = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id
    )
    if date:
        query = query.filter(
            models.Appointment.appointment_date >= date,
            models.Appointment.appointment_date < date + timedelta(days=1),
        )
    return query.all()
def create_appointment(db: Session, appointment: schemas.AppointmentCreate):
    db_appointment = models.Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment
def update_appointment_status(
    db: Session, appointment_id: int, status: schemas.AppointmentStatus
):
    db_appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id)
        .first()
    )
    if db_appointment:
        db_appointment.status = status
        db_appointment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_appointment)
    return db_appointment
def get_consultation(db: Session, consultation_id: int):
    return (
        db.query(models.Consultation)
        .filter(models.Consultation.id == consultation_id)
        .first()
    )
def get_consultations_by_patient(db: Session, patient_id: int):
    return (
        db.query(models.Consultation)
        .filter(models.Consultation.patient_id == patient_id)
        .all()
    )
def create_consultation(db: Session, consultation: schemas.ConsultationCreate):
    db_consultation = models.Consultation(**consultation.dict())
    db.add(db_consultation)
    db.commit()
    db.refresh(db_consultation)
    return db_consultation
def get_opd_bill(db: Session, bill_id: int):
    return db.query(models.OPDBill).filter(models.OPDBill.id == bill_id).first()
def create_opd_bill(db: Session, bill: schemas.OPDBillCreate):
    db_bill = models.OPDBill(**bill.dict())
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill
def get_doctor_availability(db: Session, doctor_id: int, date: datetime):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor or not doctor.is_available:
        return None
    appointments = get_appointments_by_doctor(db, doctor_id, date)
    working_hours = doctor.working_hours
    available_slots = []
    current_time = datetime.combine(date.date(), datetime.min.time())
    for hour_range in working_hours.get("hours", []):
        start_time = datetime.strptime(hour_range["start"], "%H:%M")
        end_time = datetime.strptime(hour_range["end"], "%H:%M")
        current_slot = current_time.replace(
            hour=start_time.hour, minute=start_time.minute
        )
        while current_slot.hour < end_time.hour or (
            current_slot.hour == end_time.hour and current_slot.minute < end_time.minute
        ):
            slot_end = current_slot + timedelta(minutes=30)
            slot_available = True
            for appointment in appointments:
                if (
                    current_slot <= appointment.appointment_date < slot_end
                    or current_slot
                    <= appointment.appointment_date
                    + timedelta(minutes=appointment.duration_minutes)
                    <= slot_end
                ):
                    slot_available = False
                    break
            if slot_available:
                available_slots.append(
                    {"start": current_slot, "end": slot_end, "duration": 30}
                )
            current_slot = slot_end
    return {
        "doctor_id": doctor_id,
        "date": date,
        "available": len(available_slots) > 0,
        "available_slots": available_slots,
    }
def get_opd_statistics(db: Session, date: datetime):
    total_patients = (
        db.query(models.Patient).filter(models.Patient.is_active == True).count()
    )
    total_appointments = db.query(models.Appointment).count()
    completed_appointments = (
        db.query(models.Appointment)
        .filter(models.Appointment.status == schemas.AppointmentStatus.COMPLETED)
        .count()
    )
    today_bills = (
        db.query(models.OPDBill)
        .filter(
            models.OPDBill.created_at >= date.replace(hour=0, minute=0, second=0),
            models.OPDBill.created_at < date.replace(hour=23, minute=59, second=59),
        )
        .all()
    )
    month_start = date.replace(day=1, hour=0, minute=0, second=0)
    month_bills = (
        db.query(models.OPDBill)
        .filter(
            models.OPDBill.created_at >= month_start,
            models.OPDBill.created_at <= date.replace(hour=23, minute=59, second=59),
        )
        .all()
    )
    revenue_today = sum(bill.final_amount for bill in today_bills)
    revenue_month = sum(bill.final_amount for bill in month_bills)
    return {
        "total_patients": total_patients,
        "total_appointments": total_appointments,
        "completed_appointments": completed_appointments,
        "revenue_today": revenue_today,
        "revenue_month": revenue_month,
        "average_wait_time": 15.0,  
    }