from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import models
import schemas
from sqlalchemy.orm import Session


def get_donor(db: Session, donor_id: int) -> Optional[models.Donor]:
    return db.query(models.Donor).filter(models.Donor.id == donor_id).first()


def get_donors(db: Session, skip: int = 0, limit: int = 100) -> List[models.Donor]:
    return db.query(models.Donor).offset(skip).limit(limit).all()


def create_donor(db: Session, donor: schemas.DonorCreate) -> models.Donor:
    db_donor = models.Donor(**donor.dict())
    db.add(db_donor)
    db.commit()
    db.refresh(db_donor)
    return db_donor


def get_blood_bag(db: Session, blood_bag_id: int) -> Optional[models.BloodBag]:
    return db.query(models.BloodBag).filter(models.BloodBag.id == blood_bag_id).first()


def get_blood_bags(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.BloodBag]:
    return db.query(models.BloodBag).offset(skip).limit(limit).all()


def create_blood_bag(db: Session, blood_bag: schemas.BloodBagCreate) -> models.BloodBag:
    db_blood_bag = models.BloodBag(**blood_bag.dict())
    db.add(db_blood_bag)
    db.commit()
    db.refresh(db_blood_bag)
    return db_blood_bag


def get_available_blood_bags(
    db: Session, blood_type: models.BloodType, component: models.BloodComponent
) -> List[models.BloodBag]:
    return (
        db.query(models.BloodBag)
        .filter(
            models.BloodBag.blood_type == blood_type,
            models.BloodBag.component == component,
            models.BloodBag.status == "available",
            models.BloodBag.expiration_date > datetime.utcnow(),
        )
        .all()
    )


def create_donation(db: Session, donation: schemas.DonationCreate) -> models.Donation:
    db_donation = models.Donation(**donation.dict())
    db.add(db_donation)
    db.commit()
    db.refresh(db_donation)
    return db_donation


def create_transfusion(
    db: Session, transfusion: schemas.TransfusionCreate
) -> models.Transfusion:
    db_transfusion = models.Transfusion(**transfusion.dict())
    db.add(db_transfusion)
    db.commit()
    db.refresh(db_transfusion)
    return db_transfusion


def create_blood_request(
    db: Session, blood_request: schemas.BloodRequestCreate
) -> models.BloodRequest:
    db_blood_request = models.BloodRequest(**blood_request.dict())
    db.add(db_blood_request)
    db.commit()
    db.refresh(db_blood_request)
    return db_blood_request
