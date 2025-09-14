import uuid
from datetime import datetime, timedelta

import models
import schemas
from sqlalchemy.orm import Session


def create_medication(db: Session, medication: schemas.MedicationCreate):
    db_medication = models.Medication(**medication.dict())
    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)
    return db_medication


def get_medication(db: Session, medication_id: int):
    return (
        db.query(models.Medication)
        .filter(models.Medication.id == medication_id)
        .first()
    )


def get_all_medications(db: Session):
    return db.query(models.Medication).all()


def search_medications(db: Session, query: str):
    return (
        db.query(models.Medication)
        .filter(
            (models.Medication.name.ilike(f"%{query}%"))
            | (models.Medication.generic_name.ilike(f"%{query}%"))
        )
        .all()
    )


def create_prescription(db: Session, prescription: schemas.PrescriptionCreate):
    # Generate prescription number
    prescription_number = f"RX-{datetime.now().strftime('%Y%m%d')}-{db.query(models.Prescription).count() + 1:06d}"

    # Calculate expiry date (30 days from issue)
    expiry_date = datetime.utcnow() + timedelta(days=30)

    db_prescription = models.Prescription(
        **prescription.dict(),
        prescription_number=prescription_number,
        status="active",
        issue_date=datetime.utcnow(),
        expiry_date=expiry_date,
    )
    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)
    return db_prescription


def get_prescription(db: Session, prescription_id: int):
    return (
        db.query(models.Prescription)
        .filter(models.Prescription.id == prescription_id)
        .first()
    )


def get_patient_prescriptions(db: Session, patient_id: int):
    return (
        db.query(models.Prescription)
        .filter(models.Prescription.patient_id == patient_id)
        .all()
    )


def get_doctor_prescriptions(db: Session, doctor_id: int):
    return (
        db.query(models.Prescription)
        .filter(models.Prescription.doctor_id == doctor_id)
        .all()
    )


def update_prescription_status(db: Session, prescription_id: int, status: str):
    prescription = (
        db.query(models.Prescription)
        .filter(models.Prescription.id == prescription_id)
        .first()
    )
    if prescription:
        prescription.status = status
        prescription.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(prescription)
    return prescription


def create_pharmacy(db: Session, pharmacy: schemas.PharmacyCreate):
    db_pharmacy = models.Pharmacy(**pharmacy.dict())
    db.add(db_pharmacy)
    db.commit()
    db.refresh(db_pharmacy)
    return db_pharmacy


def get_pharmacy(db: Session, pharmacy_id: int):
    return db.query(models.Pharmacy).filter(models.Pharmacy.id == pharmacy_id).first()


def get_all_pharmacies(db: Session):
    return db.query(models.Pharmacy).filter(models.Pharmacy.is_active == True).all()


def create_prescription_dispatch(
    db: Session, dispatch: schemas.PrescriptionDispatchCreate
):
    db_dispatch = models.PrescriptionDispatch(
        **dispatch.dict(), dispatch_date=datetime.utcnow()
    )
    db.add(db_dispatch)
    db.commit()
    db.refresh(db_dispatch)
    return db_dispatch


def get_prescription_dispatches(db: Session, prescription_id: int):
    return (
        db.query(models.PrescriptionDispatch)
        .filter(models.PrescriptionDispatch.prescription_id == prescription_id)
        .all()
    )


def update_dispatch_status(db: Session, dispatch_id: int, status: str):
    dispatch = (
        db.query(models.PrescriptionDispatch)
        .filter(models.PrescriptionDispatch.id == dispatch_id)
        .first()
    )
    if dispatch:
        dispatch.dispatch_status = status
        dispatch.updated_at = datetime.utcnow()

        if status == "picked_up":
            dispatch.actual_pickup_date = datetime.utcnow()

        db.commit()
        db.refresh(dispatch)
    return dispatch


def create_drug_interaction(db: Session, interaction: schemas.DrugInteractionCreate):
    db_interaction = models.DrugInteraction(**interaction.dict())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction


def check_drug_interactions(db: Session, medication_ids: list):
    interactions = []
    for i in range(len(medication_ids)):
        for j in range(i + 1, len(medication_ids)):
            interaction = (
                db.query(models.DrugInteraction)
                .filter(
                    (
                        (models.DrugInteraction.medication1_id == medication_ids[i])
                        & (models.DrugInteraction.medication2_id == medication_ids[j])
                    )
                    | (
                        (models.DrugInteraction.medication1_id == medication_ids[j])
                        & (models.DrugInteraction.medication2_id == medication_ids[i])
                    )
                )
                .first()
            )
            if interaction:
                interactions.append(interaction)
    return interactions


def check_prescription_safety(db: Session, patient_id: int, medication_ids: list):
    # Check drug interactions
    interactions = check_drug_interactions(db, medication_ids)

    # Check existing prescriptions for same patient
    existing_prescriptions = get_patient_prescriptions(db, patient_id)
    existing_medications = [
        prescription.medication_id for prescription in existing_prescriptions
    ]

    # Check for duplicate medications
    duplicate_medications = set(medication_ids) & set(existing_medications)

    return {
        "has_interactions": len(interactions) > 0,
        "interactions": interactions,
        "has_duplicates": len(duplicate_medications) > 0,
        "duplicate_medications": list(duplicate_medications),
    }
