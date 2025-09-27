"""
main module
"""

import os
import uuid
from datetime import datetime

import boto3
import crud
import models
import schemas
from botocore.exceptions import ClientError
from database import engine, get_db
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Backup & Disaster Recovery Service",
    description="Enterprise-grade backup and disaster recovery management system",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/backup-jobs/", response_model=schemas.BackupJob)
def create_backup_job(
    backup_job: schemas.BackupJobCreate, db: Session = Depends(get_db)
):
    return crud.create_backup_job(db, backup_job)


@app.get("/backup-jobs/", response_model=list[schemas.BackupJob])
def get_backup_jobs(db: Session = Depends(get_db)):
    return crud.get_all_backup_jobs(db)


@app.get("/backup-jobs/{job_id}", response_model=schemas.BackupJob)
def get_backup_job(job_id: int, db: Session = Depends(get_db)):
    job = crud.get_backup_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")
    return job


@app.put("/backup-jobs/{job_id}", response_model=schemas.BackupJob)
def update_backup_job(
    job_id: int, backup_job: schemas.BackupJobCreate, db: Session = Depends(get_db)
):
    job = crud.update_backup_job(db, job_id, backup_job)
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")
    return job


@app.delete("/backup-jobs/{job_id}")
def delete_backup_job(job_id: int, db: Session = Depends(get_db)):
    job = crud.delete_backup_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")
    return {"message": "Backup job deleted successfully"}


@app.post("/backup-executions/", response_model=schemas.BackupExecution)
def create_backup_execution(
    execution: schemas.BackupExecutionCreate, db: Session = Depends(get_db)
):
    return crud.create_backup_execution(db, execution)


@app.get("/backup-executions/{execution_id}", response_model=schemas.BackupExecution)
def get_backup_execution(execution_id: int, db: Session = Depends(get_db)):
    execution = crud.get_backup_execution(db, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Backup execution not found")
    return execution


@app.get("/jobs/{job_id}/executions", response_model=list[schemas.BackupExecution])
def get_job_executions(job_id: int, db: Session = Depends(get_db)):
    return crud.get_job_executions(db, job_id)


@app.post("/recovery-jobs/", response_model=schemas.RecoveryJob)
def create_recovery_job(
    recovery_job: schemas.RecoveryJobCreate, db: Session = Depends(get_db)
):
    return crud.create_recovery_job(db, recovery_job)


@app.get("/recovery-jobs/{recovery_id}", response_model=schemas.RecoveryJob)
def get_recovery_job(recovery_id: int, db: Session = Depends(get_db)):
    recovery = crud.get_recovery_job(db, recovery_id)
    if not recovery:
        raise HTTPException(status_code=404, detail="Recovery job not found")
    return recovery


@app.post("/disaster-recovery-plans/", response_model=schemas.DisasterRecoveryPlan)
def create_disaster_recovery_plan(
    plan: schemas.DisasterRecoveryPlanCreate, db: Session = Depends(get_db)
):
    return crud.create_disaster_recovery_plan(db, plan)


@app.get("/disaster-recovery-plans/", response_model=list[schemas.DisasterRecoveryPlan])
def get_disaster_recovery_plans(db: Session = Depends(get_db)):
    return crud.get_all_disaster_recovery_plans(db)


@app.get(
    "/disaster-recovery-plans/{plan_id}", response_model=schemas.DisasterRecoveryPlan
)
def get_disaster_recovery_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = crud.get_disaster_recovery_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Disaster recovery plan not found")
    return plan


@app.post("/storage-configurations/", response_model=schemas.StorageConfiguration)
def create_storage_configuration(
    config: schemas.StorageConfigurationCreate, db: Session = Depends(get_db)
):
    return crud.create_storage_configuration(db, config)


@app.get("/storage-configurations/", response_model=list[schemas.StorageConfiguration])
def get_storage_configurations(db: Session = Depends(get_db)):
    return crud.get_all_storage_configurations(db)


@app.get("/storage-configurations/default", response_model=schemas.StorageConfiguration)
def get_default_storage_configuration(db: Session = Depends(get_db)):
    config = crud.get_default_storage_configuration(db)
    if not config:
        raise HTTPException(
            status_code=404, detail="Default storage configuration not found"
        )
    return config


async def perform_backup_operation(backup_request: schemas.BackupRequest, db: Session):
    pass


@app.post("/backup/execute")
async def execute_backup(
    backup_request: schemas.BackupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    background_tasks.add_task(perform_backup_operation, backup_request, db)
    return {"message": "Backup operation started", "request_id": str(uuid.uuid4())}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8006)
