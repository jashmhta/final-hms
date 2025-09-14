from datetime import datetime
from typing import List

import crud
import models
import schemas
from database import SessionLocal, engine
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Blood Bank Management Service",
    description="Enterprise-grade blood bank management system for hospitals",
    version="1.0.0",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/blood-units/", response_model=schemas.BloodUnit)
async def create_blood_unit(
    blood_unit: schemas.BloodUnitCreate, db: Session = Depends(get_db)
):
    return crud.create_blood_unit(db, blood_unit)


@app.get("/blood-units/{unit_id}", response_model=schemas.BloodUnit)
async def get_blood_unit(unit_id: int, db: Session = Depends(get_db)):
    unit = crud.get_blood_unit(db, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Blood unit not found")
    return unit


@app.get(
    "/blood-units/type/{blood_type}/{rh_factor}", response_model=List[schemas.BloodUnit]
)
async def get_blood_units_by_type(
    blood_type: schemas.BloodType, rh_factor: str, db: Session = Depends(get_db)
):
    return crud.get_blood_units_by_type(db, blood_type, rh_factor)


@app.patch("/blood-units/{unit_id}/status")
async def update_blood_unit_status(
    unit_id: int, status: str, db: Session = Depends(get_db)
):
    unit = crud.update_blood_unit_status(db, unit_id, status)
    if not unit:
        raise HTTPException(status_code=404, detail="Blood unit not found")
    return {"message": "Status updated successfully"}


@app.post("/donors/", response_model=schemas.Donor)
async def create_donor(donor: schemas.DonorCreate, db: Session = Depends(get_db)):
    return crud.create_donor(db, donor)


@app.get("/donors/{donor_id}", response_model=schemas.Donor)
async def get_donor(donor_id: int, db: Session = Depends(get_db)):
    donor = crud.get_donor(db, donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor


@app.post("/donations/", response_model=schemas.Donation)
async def create_donation(
    donation: schemas.DonationCreate, db: Session = Depends(get_db)
):
    return crud.create_donation(db, donation)


@app.post("/transfusion-requests/", response_model=schemas.TransfusionRequest)
async def create_transfusion_request(
    request: schemas.TransfusionRequestCreate, db: Session = Depends(get_db)
):
    return crud.create_transfusion_request(db, request)


@app.patch("/transfusion-requests/{request_id}/status")
async def update_transfusion_request_status(
    request_id: int,
    status: str,
    approved_units: int = None,
    db: Session = Depends(get_db),
):
    request = crud.update_transfusion_request_status(
        db, request_id, status, approved_units
    )
    if not request:
        raise HTTPException(status_code=404, detail="Transfusion request not found")
    return {"message": "Status updated successfully"}


@app.post("/transfusions/", response_model=schemas.Transfusion)
async def create_transfusion(
    transfusion: schemas.TransfusionCreate, db: Session = Depends(get_db)
):
    return crud.create_transfusion(db, transfusion)


@app.post("/blood-tests/", response_model=schemas.BloodTest)
async def create_blood_test(
    blood_test: schemas.BloodTestCreate, db: Session = Depends(get_db)
):
    return crud.create_blood_test(db, blood_test)


@app.post("/inventory-alerts/", response_model=schemas.InventoryAlert)
async def create_inventory_alert(
    alert: schemas.InventoryAlertCreate, db: Session = Depends(get_db)
):
    return crud.create_inventory_alert(db, alert)


@app.get("/inventory-alerts/active", response_model=List[schemas.InventoryAlert])
async def get_active_alerts(db: Session = Depends(get_db)):
    return crud.get_active_alerts(db)


@app.patch("/inventory-alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, resolved_by: str, db: Session = Depends(get_db)):
    alert = crud.resolve_alert(db, alert_id, resolved_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved successfully"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007)
