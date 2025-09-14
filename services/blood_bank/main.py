from typing import List

import crud
import models
import schemas
import uvicorn
from database import SessionLocal, engine
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Blood Bank Service", version="1.0.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/donors/", response_model=schemas.Donor)
async def create_donor(donor: schemas.DonorCreate, db: Session = Depends(get_db)):
    return crud.create_donor(db=db, donor=donor)


@app.get("/donors/", response_model=List[schemas.Donor])
async def read_donors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    donors = crud.get_donors(db, skip=skip, limit=limit)
    return donors


@app.post("/blood-bags/", response_model=schemas.BloodBag)
async def create_blood_bag(
    blood_bag: schemas.BloodBagCreate, db: Session = Depends(get_db)
):
    return crud.create_blood_bag(db=db, blood_bag=blood_bag)


@app.get(
    "/blood-bags/available/{blood_type}/{component}",
    response_model=List[schemas.BloodBag],
)
async def get_available_blood_bags(
    blood_type: schemas.BloodType,
    component: schemas.BloodComponent,
    db: Session = Depends(get_db),
):
    return crud.get_available_blood_bags(db, blood_type, component)


@app.post("/donations/", response_model=schemas.Donation)
async def create_donation(
    donation: schemas.DonationCreate, db: Session = Depends(get_db)
):
    return crud.create_donation(db=db, donation=donation)


@app.post("/transfusions/", response_model=schemas.Transfusion)
async def create_transfusion(
    transfusion: schemas.TransfusionCreate, db: Session = Depends(get_db)
):
    return crud.create_transfusion(db=db, transfusion=transfusion)


@app.post("/blood-requests/", response_model=schemas.BloodRequest)
async def create_blood_request(
    blood_request: schemas.BloodRequestCreate, db: Session = Depends(get_db)
):
    return crud.create_blood_request(db=db, blood_request=blood_request)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
