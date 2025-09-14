from typing import List

import crud
import database
import models
import schemas
import uvicorn
from database import engine, get_db
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Insurance/TPA Integration Service",
    description="Enterprise-grade insurance claim management and TPA integration system",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "insurance_tpa_integration"}


# Insurance Provider endpoints
@app.post("/providers/", response_model=schemas.InsuranceProvider)
async def create_provider(
    provider: schemas.InsuranceProviderCreate, db: Session = Depends(get_db)
):
    return crud.create_insurance_provider(db, provider)


@app.get("/providers/", response_model=List[schemas.InsuranceProvider])
async def get_providers(db: Session = Depends(get_db)):
    return crud.get_all_insurance_providers(db)


@app.get("/providers/{provider_id}", response_model=schemas.InsuranceProvider)
async def get_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = crud.get_insurance_provider(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Insurance provider not found")
    return provider


# Insurance Policy endpoints
@app.post("/policies/", response_model=schemas.InsurancePolicy)
async def create_policy(
    policy: schemas.InsurancePolicyCreate, db: Session = Depends(get_db)
):
    return crud.create_insurance_policy(db, policy)


@app.get("/policies/{policy_id}", response_model=schemas.InsurancePolicy)
async def get_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = crud.get_insurance_policy(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Insurance policy not found")
    return policy


@app.get(
    "/patients/{patient_id}/policies", response_model=List[schemas.InsurancePolicy]
)
async def get_patient_policies(patient_id: int, db: Session = Depends(get_db)):
    return crud.get_patient_policies(db, patient_id)


# Insurance Claim endpoints
@app.post("/claims/", response_model=schemas.InsuranceClaim)
async def create_claim(
    claim: schemas.InsuranceClaimCreate, db: Session = Depends(get_db)
):
    return crud.create_insurance_claim(db, claim)


@app.get("/claims/{claim_id}", response_model=schemas.InsuranceClaim)
async def get_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = crud.get_insurance_claim(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Insurance claim not found")
    return claim


@app.get("/patients/{patient_id}/claims", response_model=List[schemas.InsuranceClaim])
async def get_patient_claims(patient_id: int, db: Session = Depends(get_db)):
    return crud.get_patient_claims(db, patient_id)


@app.patch("/claims/{claim_id}/status")
async def update_claim_status(
    claim_id: int, status_update: dict, db: Session = Depends(get_db)
):
    status = status_update.get("status")
    approved_amount = status_update.get("approved_amount")

    if status not in ["submitted", "approved", "denied", "paid"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    claim = crud.update_claim_status(db, claim_id, status, approved_amount)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {"message": f"Claim status updated to {status}", "claim": claim}


# TPA Integration endpoints
@app.post("/eligibility/check")
async def check_eligibility(
    request: schemas.EligibilityRequest, db: Session = Depends(get_db)
):
    result = crud.check_insurance_eligibility(
        db, request.patient_id, request.policy_id, request.service_date
    )
    if not result:
        raise HTTPException(status_code=404, detail="Eligibility check failed")
    return result


@app.post("/claims/{claim_id}/submit")
async def submit_claim_to_tpa(
    claim_id: int, tpa_provider_id: int, db: Session = Depends(get_db)
):
    transaction = crud.submit_claim_to_tpa(db, claim_id, tpa_provider_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Claim or provider not found")
    return {"message": "Claim submitted to TPA", "transaction": transaction}


# Payment endpoints
@app.post("/payments/", response_model=schemas.PaymentRecord)
async def create_payment(
    payment: schemas.PaymentRecordCreate, db: Session = Depends(get_db)
):
    return crud.create_payment_record(db, payment)


@app.get("/claims/{claim_id}/payments", response_model=List[schemas.PaymentRecord])
async def get_claim_payments(claim_id: int, db: Session = Depends(get_db)):
    return crud.get_claim_payments(db, claim_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
