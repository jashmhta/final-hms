from typing import List
import crud
import models
import schemas
import uvicorn
from database import Base, SessionLocal, engine
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="IPD Management Service",
    description="Enterprise-grade Inpatient Department management system",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get("/")
async def root():
    return {"message": "IPD Management Service - Enterprise Grade"}
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ipd-management"}
@app.post("/admissions/", response_model=schemas.IPDAdmission)
async def create_admission(
    admission: schemas.IPDAdmissionCreate, db: Session = Depends(get_db)
):
    return crud.create_ipd_admission(db, admission)
@app.get("/admissions/", response_model=List[schemas.IPDAdmission])
async def get_admissions(db: Session = Depends(get_db)):
    return crud.get_all_admissions(db)
@app.get("/admissions/{admission_id}", response_model=schemas.IPDAdmission)
async def get_admission(admission_id: int, db: Session = Depends(get_db)):
    admission = (
        db.query(models.IPDAdmission)
        .filter(models.IPDAdmission.id == admission_id)
        .first()
    )
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    return admission
@app.post("/beds/", response_model=schemas.IPDBed)
async def create_bed(bed: schemas.IPDBedCreate, db: Session = Depends(get_db)):
    return crud.create_ipd_bed(db, bed)
@app.get("/beds/{bed_id}", response_model=schemas.IPDBed)
async def get_bed(bed_id: int, db: Session = Depends(get_db)):
    bed = db.query(models.IPDBed).filter(models.IPDBed.id == bed_id).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    return bed
@app.post("/nursing-care/", response_model=schemas.NursingCare)
async def create_nursing_care(
    care: schemas.NursingCareCreate, db: Session = Depends(get_db)
):
    return crud.create_nursing_care(db, care)
@app.get("/nursing-care/{care_id}", response_model=schemas.NursingCare)
async def get_nursing_care(care_id: int, db: Session = Depends(get_db)):
    care = db.query(models.NursingCare).filter(models.NursingCare.id == care_id).first()
    if not care:
        raise HTTPException(status_code=404, detail="Nursing care record not found")
    return care
@app.post("/discharge-summaries/", response_model=schemas.DischargeSummary)
async def create_discharge_summary(
    summary: schemas.DischargeSummaryCreate, db: Session = Depends(get_db)
):
    return crud.create_discharge_summary(db, summary)
@app.get("/discharge-summaries/{summary_id}", response_model=schemas.DischargeSummary)
async def get_discharge_summary(summary_id: int, db: Session = Depends(get_db)):
    summary = (
        db.query(models.DischargeSummary)
        .filter(models.DischargeSummary.id == summary_id)
        .first()
    )
    if not summary:
        raise HTTPException(status_code=404, detail="Discharge summary not found")
    return summary
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)