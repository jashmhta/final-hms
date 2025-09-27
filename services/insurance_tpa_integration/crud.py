"""
crud module
"""

from datetime import datetime

import models
import schemas
from sqlalchemy.orm import Session


def create_insurance_provider(db: Session, provider: schemas.InsuranceProviderCreate):
    db_provider = models.InsuranceProvider(**provider.dict())
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider


def get_insurance_provider(db: Session, provider_id: int):
    return (
        db.query(models.InsuranceProvider)
        .filter(models.InsuranceProvider.id == provider_id)
        .first()
    )


def get_all_insurance_providers(db: Session):
    return (
        db.query(models.InsuranceProvider)
        .filter(models.InsuranceProvider.is_active == True)
        .all()
    )


def create_insurance_policy(db: Session, policy: schemas.InsurancePolicyCreate):
    db_policy = models.InsurancePolicy(**policy.dict())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy


def get_insurance_policy(db: Session, policy_id: int):
    return (
        db.query(models.InsurancePolicy)
        .filter(models.InsurancePolicy.id == policy_id)
        .first()
    )


def get_patient_policies(db: Session, patient_id: int):
    return (
        db.query(models.InsurancePolicy)
        .filter(models.InsurancePolicy.patient_id == patient_id)
        .all()
    )


def create_insurance_claim(db: Session, claim: schemas.InsuranceClaimCreate):
    from datetime import datetime

    claim_number = f"CLM-{datetime.now().strftime('%Y%m%d')}-{db.query(models.InsuranceClaim).count() + 1:06d}"
    db_claim = models.InsuranceClaim(
        **claim.dict(),
        claim_number=claim_number,
        submission_date=datetime.utcnow(),
        status="submitted",
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim


def get_insurance_claim(db: Session, claim_id: int):
    return (
        db.query(models.InsuranceClaim)
        .filter(models.InsuranceClaim.id == claim_id)
        .first()
    )


def get_patient_claims(db: Session, patient_id: int):
    return (
        db.query(models.InsuranceClaim)
        .filter(models.InsuranceClaim.patient_id == patient_id)
        .all()
    )


def update_claim_status(
    db: Session, claim_id: int, status: str, approved_amount: float = None
):
    claim = (
        db.query(models.InsuranceClaim)
        .filter(models.InsuranceClaim.id == claim_id)
        .first()
    )
    if claim:
        claim.status = status
        claim.updated_at = datetime.utcnow()
        if status == "approved" and approved_amount:
            claim.approved_amount = approved_amount
            claim.approval_date = datetime.utcnow()
        elif status == "paid":
            claim.payment_date = datetime.utcnow()
        elif status == "denied":
            claim.denial_reason = "Claim denied by insurance provider"
        db.commit()
        db.refresh(claim)
    return claim


def create_tpa_transaction(db: Session, transaction: schemas.TPATransactionCreate):
    db_transaction = models.TPATransaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_claim_transactions(db: Session, claim_id: int):
    return (
        db.query(models.TPATransaction)
        .filter(models.TPATransaction.claim_id == claim_id)
        .all()
    )


def create_payment_record(db: Session, payment: schemas.PaymentRecordCreate):
    db_payment = models.PaymentRecord(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


def get_claim_payments(db: Session, claim_id: int):
    return (
        db.query(models.PaymentRecord)
        .filter(models.PaymentRecord.claim_id == claim_id)
        .all()
    )


def check_insurance_eligibility(
    db: Session, patient_id: int, policy_id: int, service_date: datetime
):
    policy = get_insurance_policy(db, policy_id)
    if not policy or policy.patient_id != patient_id:
        return None
    return {
        "is_eligible": True,
        "coverage_details": policy.coverage_details,
        "requires_preauth": policy.coverage_details.get(
            "requires_preauthorization", False
        ),
        "limitations": ["Pre-authorization required for surgical procedures"],
    }


def submit_claim_to_tpa(db: Session, claim_id: int, tpa_provider_id: int):
    claim = get_insurance_claim(db, claim_id)
    provider = get_insurance_provider(db, tpa_provider_id)
    if not claim or not provider:
        return None
    tpa_reference = f"TPA-{datetime.now().strftime('%Y%m%d')}-{claim_id:06d}"
    transaction_data = {
        "claim_id": claim_id,
        "tpa_reference": tpa_reference,
        "transaction_type": "claim_submission",
        "request_data": {
            "claim_number": claim.claim_number,
            "patient_id": claim.patient_id,
            "total_amount": claim.total_amount,
        },
        "response_data": {
            "status": "submitted",
            "tpa_reference": tpa_reference,
            "estimated_processing_time": "7-10 business days",
        },
        "status_code": 200,
    }
    transaction = create_tpa_transaction(
        db, schemas.TPATransactionCreate(**transaction_data)
    )
    return transaction
