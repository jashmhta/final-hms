from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel
class AccountType(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"
class DepreciationMethod(str, Enum):
    STRAIGHT_LINE = "STRAIGHT_LINE"
    DECLINING_BALANCE = "DECLINING_BALANCE"
class ChartOfAccountsBase(BaseModel):
    organization_id: int
    name: str
    code: str
    type: AccountType
    parent_id: Optional[int] = None
class ChartOfAccountsCreate(ChartOfAccountsBase):
    pass
class ChartOfAccountsRead(ChartOfAccountsBase):
    id: int
    class Config:
        from_attributes = True
class PricingGroupBase(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
class PricingGroupCreate(PricingGroupBase):
    pass
class PricingGroupRead(PricingGroupBase):
    id: int
    class Config:
        from_attributes = True
class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
class DepartmentCreate(DepartmentBase):
    pass
class DepartmentRead(DepartmentBase):
    id: int
    class Config:
        from_attributes = True
class ReferralIncomeBase(BaseModel):
    source: str
    amount: float
    date: date
class ReferralIncomeCreate(ReferralIncomeBase):
    pass
class ReferralIncomeRead(ReferralIncomeBase):
    id: int
    class Config:
        from_attributes = True
class OutsourcedServiceBase(BaseModel):
    service_name: str
    provider: Optional[str] = None
    cost: float
    date: date
class OutsourcedServiceCreate(OutsourcedServiceBase):
    pass
class OutsourcedServiceRead(OutsourcedServiceBase):
    id: int
    class Config:
        from_attributes = True
class AssetBase(BaseModel):
    name: str
    purchase_date: date
    cost: float
    depreciation_method: DepreciationMethod
    useful_life: int
    salvage_value: float
class AssetCreate(AssetBase):
    pass
class AssetRead(AssetBase):
    id: int
    class Config:
        from_attributes = True
class JournalEntryBase(BaseModel):
    date: date
    description: Optional[str] = None
class JournalEntryCreate(JournalEntryBase):
    pass
class JournalEntryRead(JournalEntryBase):
    id: int
    class Config:
        from_attributes = True
class LedgerEntryBase(BaseModel):
    journal_entry_id: int
    account_id: int
    pricing_group_id: Optional[int] = None
    department_id: Optional[int] = None
    debit: float = 0
    credit: float = 0
class LedgerEntryCreate(LedgerEntryBase):
    pass
class LedgerEntryRead(LedgerEntryBase):
    id: int
    class Config:
        from_attributes = True