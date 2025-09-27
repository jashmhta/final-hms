"""
main module
"""

from datetime import datetime
from typing import List

import crud
import models
import schemas
import uvicorn
from database import engine, get_db
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="E-Prescription Service",
    description="Enterprise-grade electronic prescription management system",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/medications/", response_model=schemas.Medication)
def create_medication(
    medication: schemas.MedicationCreate, db: Session = Depends(get_db)
):
    return crud.create_medication(db, medication)


@app.get("/medications/", response_model=List[schemas.Medication])
def get_medications(db: Session = Depends(get_db)):
    return crud.get_all_medications(db)


@app.get("/medications/{medication_id}", response_model=schemas.Medication)
def get_medication(medication_id: int, db: Session = Depends(get_db)):
    medication = crud.get_medication(db, medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    return medication


@app.get("/medications/search/{query}", response_model=List[schemas.Medication])
def search_medications(query: str, db: Session = Depends(get_db)):
    return crud.search_medications(db, query)


@app.post("/prescriptions/", response_model=schemas.Prescription)
def create_prescription(
    prescription: schemas.PrescriptionCreate, db: Session = Depends(get_db)
):
    return crud.create_prescription(db, prescription)


@app.get("/prescriptions/{prescription_id}", response_model=schemas.Prescription)
def get_prescription(prescription_id: int, db: Session = Depends(get_db)):
    prescription = crud.get_prescription(db, prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescription


@app.get(
    "/patients/{patient_id}/prescriptions", response_model=List[schemas.Prescription]
)
def get_patient_prescriptions(patient_id: int, db: Session = Depends(get_db)):
    return crud.get_patient_prescriptions(db, patient_id)


@app.get(
    "/doctors/{doctor_id}/prescriptions", response_model=List[schemas.Prescription]
)
def get_doctor_prescriptions(doctor_id: int, db: Session = Depends(get_db)):
    return crud.get_doctor_prescriptions(db, doctor_id)


@app.patch("/prescriptions/{prescription_id}/status")
def update_prescription_status(
    prescription_id: int, status: str, db: Session = Depends(get_db)
):
    prescription = crud.update_prescription_status(db, prescription_id, status)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return {"message": "Prescription status updated successfully"}


@app.post("/pharmacies/", response_model=schemas.Pharmacy)
def create_pharmacy(pharmacy: schemas.PharmacyCreate, db: Session = Depends(get_db)):
    return crud.create_pharmacy(db, pharmacy)


@app.get("/pharmacies/", response_model=List[schemas.Pharmacy])
def get_pharmacies(db: Session = Depends(get_db)):
    return crud.get_all_pharmacies(db)


@app.get("/pharmacies/{pharmacy_id}", response_model=schemas.Pharmacy)
def get_pharmacy(pharmacy_id: int, db: Session = Depends(get_db)):
    pharmacy = crud.get_pharmacy(db, pharmacy_id)
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    return pharmacy


@app.post("/dispatches/", response_model=schemas.PrescriptionDispatch)
def create_dispatch(
    dispatch: schemas.PrescriptionDispatchCreate, db: Session = Depends(get_db)
):
    return crud.create_prescription_dispatch(db, dispatch)


@app.get(
    "/prescriptions/{prescription_id}/dispatches",
    response_model=List[schemas.PrescriptionDispatch],
)
def get_prescription_dispatches(prescription_id: int, db: Session = Depends(get_db)):
    return crud.get_prescription_dispatches(db, prescription_id)


@app.patch("/dispatches/{dispatch_id}/status")
def update_dispatch_status(
    dispatch_id: int, status: str, db: Session = Depends(get_db)
):
    dispatch = crud.update_dispatch_status(db, dispatch_id, status)
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    return {"message": "Dispatch status updated successfully"}


@app.post("/safety/check")
def check_prescription_safety(
    request: schemas.PrescriptionCheckRequest, db: Session = Depends(get_db)
):
    safety_check = crud.check_prescription_safety(
        db, request.patient_id, request.medication_ids
    )
    return safety_check


@app.post("/interactions/")
def create_interaction(
    interaction: schemas.DrugInteractionCreate, db: Session = Depends(get_db)
):
    return crud.create_drug_interaction(db, interaction)


@app.get("/interactions/check")
def check_interactions(
    medication1_id: int, medication2_id: int, db: Session = Depends(get_db)
):
    interactions = crud.check_drug_interactions(db, [medication1_id, medication2_id])
    return {"has_interaction": len(interactions) > 0, "interactions": interactions}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
