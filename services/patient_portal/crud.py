from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import models
import schemas
import hashlib
def get_patient(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()
def get_patient_by_patient_id(db: Session, patient_id_str: str):
    return db.query(models.Patient).filter(models.Patient.patient_id == patient_id_str).first()
def get_patients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Patient).filter(models.Patient.is_active == True).offset(skip).limit(limit).all()
def create_patient(db: Session, patient: schemas.PatientCreate):
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient
def update_patient(db: Session, patient_id: int, patient_update: Dict[str, Any]):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if db_patient:
        for key, value in patient_update.items():
            setattr(db_patient, key, value)
        db_patient.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_patient)
    return db_patient
def create_patient_login(db: Session, login: schemas.PatientLoginCreate):
    password_hash = hashlib.sha256(login.password.encode()).hexdigest()
    db_login = models.PatientLogin(
        patient_id=login.patient_id,
        username=login.username,
        password_hash=password_hash
    )
    db.add(db_login)
    db.commit()
    db.refresh(db_login)
    return db_login
def authenticate_patient(db: Session, username: str, password: str):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    login = db.query(models.PatientLogin).filter(
        models.PatientLogin.username == username,
        models.PatientLogin.password_hash == password_hash,
        models.PatientLogin.is_active == True
    ).first()
    if login:
        login.last_login = datetime.utcnow()
        db.commit()
        db.refresh(login)
    return login
def get_patient_appointments(db: Session, patient_id: int, status: Optional[str] = None):
    query = db.query(models.PatientAppointment).filter(models.PatientAppointment.patient_id == patient_id)
    if status:
        query = query.filter(models.PatientAppointment.status == status)
    return query.all()
def create_patient_appointment(db: Session, appointment: schemas.PatientAppointmentCreate):
    db_appointment = models.PatientAppointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment
def update_appointment_status(db: Session, appointment_id: str, status: str):
    db_appointment = db.query(models.PatientAppointment).filter(
        models.PatientAppointment.appointment_id == appointment_id
    ).first()
    if db_appointment:
        db_appointment.status = status
        db_appointment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_appointment)
    return db_appointment
def get_patient_medical_records(db: Session, patient_id: int, record_type: Optional[str] = None):
    query = db.query(models.PatientMedicalRecord).filter(models.PatientMedicalRecord.patient_id == patient_id)
    if record_type:
        query = query.filter(models.PatientMedicalRecord.record_type == record_type)
    return query.order_by(models.PatientMedicalRecord.date.desc()).all()
def create_patient_medical_record(db: Session, record: schemas.PatientMedicalRecordCreate):
    db_record = models.PatientMedicalRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record
def get_patient_feedback(db: Session, patient_id: int, service_type: Optional[str] = None):
    query = db.query(models.PatientFeedback).filter(models.PatientFeedback.patient_id == patient_id)
    if service_type:
        query = query.filter(models.PatientFeedback.service_type == service_type)
    return query.order_by(models.PatientFeedback.created_at.desc()).all()
def create_patient_feedback(db: Session, feedback: schemas.PatientFeedbackCreate):
    db_feedback = models.PatientFeedback(**feedback.dict())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback
def get_patient_notifications(db: Session, patient_id: int, is_read: Optional[bool] = None):
    query = db.query(models.PatientNotification).filter(models.PatientNotification.patient_id == patient_id)
    if is_read is not None:
        query = query.filter(models.PatientNotification.is_read == is_read)
    return query.order_by(models.PatientNotification.created_at.desc()).all()
def create_patient_notification(db: Session, notification: schemas.PatientNotificationCreate):
    db_notification = models.PatientNotification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification
def mark_notification_read(db: Session, notification_id: str):
    db_notification = db.query(models.PatientNotification).filter(
        models.PatientNotification.notification_id == notification_id
    ).first()
    if db_notification:
        db_notification.is_read = True
        db_notification.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_notification)
    return db_notification
def get_patient_dashboard(db: Session, patient_id: int):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        return None
    upcoming_appointments = db.query(models.PatientAppointment).filter(
        models.PatientAppointment.patient_id == patient_id,
        models.PatientAppointment.appointment_date > datetime.utcnow(),
        models.PatientAppointment.status.in_(["scheduled", "confirmed"])
    ).count()
    pending_results = db.query(models.PatientMedicalRecord).filter(
        models.PatientMedicalRecord.patient_id == patient_id,
        models.PatientMedicalRecord.record_type == "lab_result",
        models.PatientMedicalRecord.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    unread_notifications = db.query(models.PatientNotification).filter(
        models.PatientNotification.patient_id == patient_id,
        models.PatientNotification.is_read == False
    ).count()
    recent_consultations = db.query(models.PatientMedicalRecord).filter(
        models.PatientMedicalRecord.patient_id == patient_id,
        models.PatientMedicalRecord.record_type == "consultation",
        models.PatientMedicalRecord.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    health_summary = {
        "blood_group": patient.blood_group.value if patient.blood_group else "Unknown",
        "allergies": patient.allergies or [],
        "last_visit": None  
    }
    return {
        "patient_id": patient_id,
        "patient_name": f"{patient.first_name} {patient.last_name}",
        "upcoming_appointments": upcoming_appointments,
        "pending_results": pending_results,
        "unread_notifications": unread_notifications,
        "recent_consultations": recent_consultations,
        "health_summary": health_summary
    }
def get_patient_statistics(db: Session):
    total_patients = db.query(models.Patient).filter(models.Patient.is_active == True).count()
    active_patients = db.query(models.Patient).filter(
        models.Patient.is_active == True,
        models.Patient.status == models.PatientStatus.ACTIVE
    ).count()
    today = datetime.utcnow().date()
    new_registrations_today = db.query(models.Patient).filter(
        models.Patient.created_at >= today,
        models.Patient.created_at < today + timedelta(days=1)
    ).count()
    feedbacks = db.query(models.PatientFeedback).all()
    avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks) if feedbacks else 0.0
    return {
        "total_patients": total_patients,
        "active_patients": active_patients,
        "new_registrations_today": new_registrations_today,
        "average_rating": avg_rating
    }