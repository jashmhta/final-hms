from core.auth.dependencies import get_current_user, require_roles
from core.db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models import models
from ..schemas import (
    AssetUpkeepCreate,
    AssetUpkeepRead,
    AssetUpkeepUpdate,
    CleaningTaskCreate,
    CleaningTaskRead,
    CleaningTaskUpdate,
    MaintenanceRequestCreate,
    MaintenanceRequestRead,
    MaintenanceRequestUpdate,
)

router = APIRouter()


# CleaningTask Endpoints
@router.post("/cleaning_tasks", response_model=CleaningTaskRead)
@require_roles("admin", "staff")
def create_cleaning_task(
    task: CleaningTaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_task = models.CleaningTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/cleaning_tasks", response_model=list[CleaningTaskRead])
@require_roles("admin", "staff")
def list_cleaning_tasks(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    return db.query(models.CleaningTask).all()


@router.put("/cleaning_tasks/{task_id}", response_model=CleaningTaskRead)
@require_roles("admin", "staff")
def update_cleaning_task(
    task_id: int,
    task: CleaningTaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_task = db.query(models.CleaningTask).get(task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/cleaning_tasks/{task_id}")
@require_roles("admin", "staff")
def delete_cleaning_task(
    task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    db_task = db.query(models.CleaningTask).get(task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"detail": "Deleted"}


# MaintenanceRequest Endpoints
@router.post("/maintenance_requests", response_model=MaintenanceRequestRead)
@require_roles("admin", "staff")
def create_maintenance_request(
    req: MaintenanceRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_req = models.MaintenanceRequest(**req.dict())
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req


@router.get("/maintenance_requests", response_model=list[MaintenanceRequestRead])
@require_roles("admin", "staff")
def list_maintenance_requests(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    return db.query(models.MaintenanceRequest).all()


# AssetUpkeep Endpoints
@router.post("/asset_upkeep", response_model=AssetUpkeepRead)
@require_roles("admin", "staff")
def create_asset_upkeep(
    upkeep: AssetUpkeepCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_upkeep = models.AssetUpkeep(**upkeep.dict())
    db.add(db_upkeep)
    db.commit()
    db.refresh(db_upkeep)
    return db_upkeep


@router.get("/asset_upkeep", response_model=list[AssetUpkeepRead])
@require_roles("admin", "staff")
def list_asset_upkeep(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    return db.query(models.AssetUpkeep).all()
