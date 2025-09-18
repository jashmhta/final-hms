from datetime import datetime
import models
import schemas
from sqlalchemy.orm import Session
def create_ipd_admission(db: Session, admission: schemas.IPDAdmissionCreate):
    db_admission = models.IPDAdmission(**admission.dict())
    db.add(db_admission)
    db.commit()
    db.refresh(db_admission)
    return db_admission
def get_all_admissions(db: Session):
    return db.query(models.IPDAdmission).all()
def get_admission_by_id(db: Session, admission_id: int):
    return (
        db.query(models.IPDAdmission)
        .filter(models.IPDAdmission.id == admission_id)
        .first()
    )
def create_ipd_bed(db: Session, bed: schemas.IPDBedCreate):
    db_bed = models.IPDBed(**bed.dict())
    db.add(db_bed)
    db.commit()
    db.refresh(db_bed)
    return db_bed
def get_bed_by_id(db: Session, bed_id: int):
    return db.query(models.IPDBed).filter(models.IPDBed.id == bed_id).first()
def create_nursing_care(db: Session, care: schemas.NursingCareCreate):
    db_care = models.NursingCare(**care.dict())
    db.add(db_care)
    db.commit()
    db.refresh(db_care)
    return db_care
def get_nursing_care_by_id(db: Session, care_id: int):
    return db.query(models.NursingCare).filter(models.NursingCare.id == care_id).first()
def create_discharge_summary(db: Session, summary: schemas.DischargeSummaryCreate):
    db_summary = models.DischargeSummary(**summary.dict())
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary
def get_discharge_summary_by_id(db: Session, summary_id: int):
    return (
        db.query(models.DischargeSummary)
        .filter(models.DischargeSummary.id == summary_id)
        .first()
    )
def update_admission_status(db: Session, admission_id: int, status: str):
    admission = (
        db.query(models.IPDAdmission)
        .filter(models.IPDAdmission.id == admission_id)
        .first()
    )
    if admission:
        admission.status = status
        admission.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(admission)
    return admission
def get_active_admissions(db: Session):
    return (
        db.query(models.IPDAdmission)
        .filter(models.IPDAdmission.status == "admitted")
        .all()
    )