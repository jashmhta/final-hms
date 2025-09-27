"""
crud module
"""

import uuid
from datetime import datetime

import models
import schemas
from sqlalchemy.orm import Session


def create_backup_job(db: Session, backup_job: schemas.BackupJobCreate):
    db_backup_job = models.BackupJob(**backup_job.dict())
    db.add(db_backup_job)
    db.commit()
    db.refresh(db_backup_job)
    return db_backup_job


def get_backup_job(db: Session, job_id: int):
    return db.query(models.BackupJob).filter(models.BackupJob.id == job_id).first()


def get_all_backup_jobs(db: Session):
    return db.query(models.BackupJob).filter(models.BackupJob.is_active == True).all()


def update_backup_job(db: Session, job_id: int, backup_job: schemas.BackupJobCreate):
    db_job = db.query(models.BackupJob).filter(models.BackupJob.id == job_id).first()
    if db_job:
        for key, value in backup_job.dict().items():
            setattr(db_job, key, value)
        db_job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_job)
    return db_job


def delete_backup_job(db: Session, job_id: int):
    db_job = db.query(models.BackupJob).filter(models.BackupJob.id == job_id).first()
    if db_job:
        db_job.is_active = False
        db_job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_job)
    return db_job


def create_backup_execution(db: Session, execution: schemas.BackupExecutionCreate):
    execution_id = f"backup-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    db_execution = models.BackupExecution(**execution.dict(), execution_id=execution_id)
    db.add(db_execution)
    db.commit()
    db.refresh(db_execution)
    return db_execution


def get_backup_execution(db: Session, execution_id: int):
    return (
        db.query(models.BackupExecution)
        .filter(models.BackupExecution.id == execution_id)
        .first()
    )


def get_job_executions(db: Session, job_id: int):
    return (
        db.query(models.BackupExecution)
        .filter(models.BackupExecution.job_id == job_id)
        .all()
    )


def update_execution_status(db: Session, execution_id: int, status: str, **kwargs):
    execution = (
        db.query(models.BackupExecution)
        .filter(models.BackupExecution.id == execution_id)
        .first()
    )
    if execution:
        execution.status = status
        if status == "completed" or status == "failed":
            execution.end_time = datetime.utcnow()
            execution.duration_seconds = (
                execution.end_time - execution.start_time
            ).total_seconds()
        for key, value in kwargs.items():
            if hasattr(execution, key):
                setattr(execution, key, value)
        db.commit()
        db.refresh(execution)
    return execution


def create_recovery_job(db: Session, recovery_job: schemas.RecoveryJobCreate):
    db_recovery_job = models.RecoveryJob(**recovery_job.dict())
    db.add(db_recovery_job)
    db.commit()
    db.refresh(db_recovery_job)
    return db_recovery_job


def get_recovery_job(db: Session, recovery_id: int):
    return (
        db.query(models.RecoveryJob)
        .filter(models.RecoveryJob.id == recovery_id)
        .first()
    )


def update_recovery_status(db: Session, recovery_id: int, status: str, **kwargs):
    recovery = (
        db.query(models.RecoveryJob)
        .filter(models.RecoveryJob.id == recovery_id)
        .first()
    )
    if recovery:
        recovery.status = status
        if status == "completed" or status == "failed":
            recovery.end_time = datetime.utcnow()
        for key, value in kwargs.items():
            if hasattr(recovery, key):
                setattr(recovery, key, value)
        db.commit()
        db.refresh(recovery)
    return recovery


def create_disaster_recovery_plan(
    db: Session, plan: schemas.DisasterRecoveryPlanCreate
):
    db_plan = models.DisasterRecoveryPlan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


def get_disaster_recovery_plan(db: Session, plan_id: int):
    return (
        db.query(models.DisasterRecoveryPlan)
        .filter(models.DisasterRecoveryPlan.id == plan_id)
        .first()
    )


def get_all_disaster_recovery_plans(db: Session):
    return (
        db.query(models.DisasterRecoveryPlan)
        .filter(models.DisasterRecoveryPlan.is_active == True)
        .all()
    )


def update_disaster_recovery_plan(
    db: Session, plan_id: int, plan: schemas.DisasterRecoveryPlanCreate
):
    db_plan = (
        db.query(models.DisasterRecoveryPlan)
        .filter(models.DisasterRecoveryPlan.id == plan_id)
        .first()
    )
    if db_plan:
        for key, value in plan.dict().items():
            setattr(db_plan, key, value)
        db_plan.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_plan)
    return db_plan


def create_storage_configuration(
    db: Session, config: schemas.StorageConfigurationCreate
):
    db_config = models.StorageConfiguration(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def get_storage_configuration(db: Session, config_id: int):
    return (
        db.query(models.StorageConfiguration)
        .filter(models.StorageConfiguration.id == config_id)
        .first()
    )


def get_all_storage_configurations(db: Session):
    return (
        db.query(models.StorageConfiguration)
        .filter(models.StorageConfiguration.is_active == True)
        .all()
    )


def get_default_storage_configuration(db: Session):
    return (
        db.query(models.StorageConfiguration)
        .filter(
            models.StorageConfiguration.is_default == True,
            models.StorageConfiguration.is_active == True,
        )
        .first()
    )
