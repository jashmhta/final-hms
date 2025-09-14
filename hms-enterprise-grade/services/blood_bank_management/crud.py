import uuid
from datetime import datetime

import models
import schemas
from sqlalchemy.orm import Session


def create_blood_unit(db: Session, blood_unit: schemas.BloodUnitCreate):
    db_blood_unit = models.BloodUnit(**blood_unit.dict())
    db.add(db_blood_unit)
    db.commit()
    db.refresh(db_blood_unit)
    return db_blood_unit


def get_blood_unit(db: Session, unit_id: int):
    return db.query(models.BloodUnit).filter(models.BloodUnit.id == unit_id).first()


def get_blood_units_by_type(db: Session, blood_type: schemas.BloodType, rh_factor: str):
    return (
        db.query(models.BloodUnit)
        .filter(
            models.BloodUnit.blood_type == blood_type,
            models.BloodUnit.rh_factor == rh_factor,
            models.BloodUnit.status == "available",
        )
        .all()
    )


def update_blood_unit_status(db: Session, unit_id: int, status: str):
    unit = db.query(models.BloodUnit).filter(models.BloodUnit.id == unit_id).first()
    if unit:
        unit.status = status
        unit.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(unit)
    return unit


def create_donor(db: Session, donor: schemas.DonorCreate):
    db_donor = models.Donor(**donor.dict())
    db.add(db_donor)
    db.commit()
    db.refresh(db_donor)
    return db_donor


def get_donor(db: Session, donor_id: int):
    return db.query(models.Donor).filter(models.Donor.id == donor_id).first()


def get_donors_by_blood_type(db: Session, blood_type: schemas.BloodType):
    return (
        db.query(models.Donor)
        .filter(models.Donor.blood_type == blood_type, models.Donor.is_active == True)
        .all()
    )


def create_donation(db: Session, donation: schemas.DonationCreate):
    db_donation = models.Donation(**donation.dict())
    db.add(db_donation)
    db.commit()
    db.refresh(db_donation)
    return db_donation


def get_donation(db: Session, donation_id: int):
    return db.query(models.Donation).filter(models.Donation.id == donation_id).first()


def get_donor_donations(db: Session, donor_id: int):
    return db.query(models.Donation).filter(models.Donation.donor_id == donor_id).all()


def create_transfusion_request(db: Session, request: schemas.TransfusionRequestCreate):
    db_request = models.TransfusionRequest(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


def get_transfusion_request(db: Session, request_id: int):
    return (
        db.query(models.TransfusionRequest)
        .filter(models.TransfusionRequest.id == request_id)
        .first()
    )


def update_transfusion_request_status(
    db: Session, request_id: int, status: str, approved_units: int = None
):
    request = (
        db.query(models.TransfusionRequest)
        .filter(models.TransfusionRequest.id == request_id)
        .first()
    )
    if request:
        request.status = status
        if approved_units is not None:
            request.approved_units = approved_units
        request.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(request)
    return request


def create_transfusion(db: Session, transfusion: schemas.TransfusionCreate):
    db_transfusion = models.Transfusion(**transfusion.dict())
    db.add(db_transfusion)
    db.commit()
    db.refresh(db_transfusion)
    return db_transfusion


def get_transfusion(db: Session, transfusion_id: int):
    return (
        db.query(models.Transfusion)
        .filter(models.Transfusion.id == transfusion_id)
        .first()
    )


def create_blood_test(db: Session, blood_test: schemas.BloodTestCreate):
    db_blood_test = models.BloodTest(**blood_test.dict())
    db.add(db_blood_test)
    db.commit()
    db.refresh(db_blood_test)
    return db_blood_test


def get_blood_tests_for_unit(db: Session, blood_unit_id: int):
    return (
        db.query(models.BloodTest)
        .filter(models.BloodTest.blood_unit_id == blood_unit_id)
        .all()
    )


def create_inventory_alert(db: Session, alert: schemas.InventoryAlertCreate):
    db_alert = models.InventoryAlert(**alert.dict())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_active_alerts(db: Session):
    return (
        db.query(models.InventoryAlert)
        .filter(models.InventoryAlert.is_resolved == False)
        .all()
    )


def resolve_alert(db: Session, alert_id: int, resolved_by: str):
    alert = (
        db.query(models.InventoryAlert)
        .filter(models.InventoryAlert.id == alert_id)
        .first()
    )
    if alert:
        alert.is_resolved = True
        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
    return alert


def get_blood_inventory_summary(db: Session):
    # Implementation for inventory summary
    pass


def get_donation_statistics(db: Session):
    # Implementation for donation statistics
    pass


def get_transfusion_statistics(db: Session):
    # Implementation for transfusion statistics
    pass
