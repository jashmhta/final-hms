"""
routes module
"""

import io
from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db

router = APIRouter()


def crud_factory(model, schema_create, schema_read):
    def create(item: schema_create, db: Session = Depends(get_db)):
        db_item = model(**item.dict())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    def list_all(db: Session = Depends(get_db)):
        return db.query(model).all()

    return create, list_all


pg_router = APIRouter(prefix="/pricing_groups", tags=["Pricing Groups"])
create_pg, list_pg = crud_factory(
    models.PricingGroup, schemas.PricingGroupCreate, schemas.PricingGroupRead
)
pg_router.post("/", response_model=schemas.PricingGroupRead)(create_pg)
pg_router.get("/", response_model=list[schemas.PricingGroupRead])(list_pg)
dep_router = APIRouter(prefix="/departments", tags=["Departments"])
create_dep, list_dep = crud_factory(
    models.Department, schemas.DepartmentCreate, schemas.DepartmentRead
)
dep_router.post("/", response_model=schemas.DepartmentRead)(create_dep)
dep_router.get("/", response_model=list[schemas.DepartmentRead])(list_dep)
ri_router = APIRouter(prefix="/referral_income", tags=["Referral Income"])
create_ri, list_ri = crud_factory(
    models.ReferralIncome, schemas.ReferralIncomeCreate, schemas.ReferralIncomeRead
)
ri_router.post("/", response_model=schemas.ReferralIncomeRead)(create_ri)
ri_router.get("/", response_model=list[schemas.ReferralIncomeRead])(list_ri)
os_router = APIRouter(prefix="/outsourced_services", tags=["Outsourced Services"])
create_os, list_os = crud_factory(
    models.OutsourcedService,
    schemas.OutsourcedServiceCreate,
    schemas.OutsourcedServiceRead,
)
os_router.post("/", response_model=schemas.OutsourcedServiceRead)(create_os)
os_router.get("/", response_model=list[schemas.OutsourcedServiceRead])(list_os)
asset_router = APIRouter(prefix="/assets", tags=["Assets"])
create_asset, list_asset = crud_factory(
    models.Asset, schemas.AssetCreate, schemas.AssetRead
)
asset_router.post("/", response_model=schemas.AssetRead)(create_asset)
asset_router.get("/", response_model=list[schemas.AssetRead])(list_asset)
je_router = APIRouter(prefix="/journal_entries", tags=["Journal Entries"])
create_je, list_je = crud_factory(
    models.JournalEntry, schemas.JournalEntryCreate, schemas.JournalEntryRead
)
je_router.post("/", response_model=schemas.JournalEntryRead)(create_je)
je_router.get("/", response_model=list[schemas.JournalEntryRead])(list_je)
le_router = APIRouter(prefix="/ledger_entries", tags=["Ledger Entries"])
create_le, list_le = crud_factory(
    models.LedgerEntry, schemas.LedgerEntryCreate, schemas.LedgerEntryRead
)
le_router.post("/", response_model=schemas.LedgerEntryRead)(create_le)
le_router.get("/", response_model=list[schemas.LedgerEntryRead])(list_le)


def validate_double_entry(journal_entry_id: int, db: Session):
    entries = (
        db.query(models.LedgerEntry).filter_by(journal_entry_id=journal_entry_id).all()
    )
    total_debit = sum(e.debit for e in entries)
    total_credit = sum(e.credit for e in entries)
    if round(total_debit, 2) != round(total_credit, 2):
        raise HTTPException(status_code=400, detail="Double-entry validation failed")


def calculate_depreciation(asset: models.Asset):
    if asset.depreciation_method == models.DepreciationMethod.STRAIGHT_LINE:
        annual_dep = (asset.cost - asset.salvage_value) / asset.useful_life
        return annual_dep
    elif asset.depreciation_method == models.DepreciationMethod.DECLINING_BALANCE:
        rate = 1 - (asset.salvage_value / asset.cost) ** (1 / asset.useful_life)
        return asset.cost * rate


def calculate_roi(gain: float, cost: float):
    return (gain - cost) / cost * 100


def calculate_break_even(
    fixed_costs: float, price_per_unit: float, variable_cost_per_unit: float
):
    return fixed_costs / (price_per_unit - variable_cost_per_unit)


report_router = APIRouter(prefix="/reports", tags=["Reports"])


@report_router.get("/department_pnl")
def department_pnl(db: Session = Depends(get_db)):
    data = (
        db.query(
            models.Department.name, models.LedgerEntry.debit, models.LedgerEntry.credit
        )
        .join(models.LedgerEntry)
        .all()
    )
    return data


@report_router.get("/asset_depreciation")
def asset_depreciation(db: Session = Depends(get_db)):
    assets = db.query(models.Asset).all()
    schedule = []
    for asset in assets:
        dep = calculate_depreciation(asset)
        schedule.append({"asset": asset.name, "annual_depreciation": dep})
    return schedule


export_router = APIRouter(prefix="/export", tags=["Export"])


@export_router.get("/excel")
def export_excel(db: Session = Depends(get_db)):
    data = db.query(models.LedgerEntry).all()
    df = pd.DataFrame([e.__dict__ for e in data])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=export.xlsx"},
    )


router.include_router(pg_router)
router.include_router(dep_router)
router.include_router(ri_router)
router.include_router(os_router)
router.include_router(asset_router)
router.include_router(je_router)
router.include_router(le_router)
router.include_router(report_router)
router.include_router(export_router)
