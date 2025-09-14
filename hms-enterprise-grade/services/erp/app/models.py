import enum

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class AccountType(str, enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class ChartOfAccounts(Base):
    __tablename__ = "chart_of_accounts"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    type = Column(Enum(AccountType), nullable=False)
    parent_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=True)
    parent = relationship("ChartOfAccounts", remote_side=[id])
    ledger_entries = relationship("LedgerEntry", back_populates="account")


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    description = Column(Text)
    ledger_entries = relationship("LedgerEntry", back_populates="journal_entry")


class PricingGroup(Base):
    __tablename__ = "pricing_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(255))
    description = Column(Text)
    ledger_entries = relationship("LedgerEntry", back_populates="pricing_group")


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    ledger_entries = relationship("LedgerEntry", back_populates="department")


class ReferralIncome(Base):
    __tablename__ = "referral_income"
    id = Column(Integer, primary_key=True)
    source = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(Date, nullable=False)


class OutsourcedService(Base):
    __tablename__ = "outsourced_services"
    id = Column(Integer, primary_key=True)
    service_name = Column(String(255), nullable=False)
    provider = Column(String(255))
    cost = Column(Numeric(12, 2), nullable=False)
    date = Column(Date, nullable=False)


class DepreciationMethod(str, enum.Enum):
    STRAIGHT_LINE = "STRAIGHT_LINE"
    DECLINING_BALANCE = "DECLINING_BALANCE"


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    purchase_date = Column(Date, nullable=False)
    cost = Column(Numeric(12, 2), nullable=False)
    depreciation_method = Column(Enum(DepreciationMethod), nullable=False)
    useful_life = Column(Integer, nullable=False)  # in years
    salvage_value = Column(Numeric(12, 2), nullable=False)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(Integer, primary_key=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"))
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"))
    pricing_group_id = Column(Integer, ForeignKey("pricing_groups.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    debit = Column(Numeric(12, 2), default=0)
    credit = Column(Numeric(12, 2), default=0)

    journal_entry = relationship("JournalEntry", back_populates="ledger_entries")
    account = relationship("ChartOfAccounts", back_populates="ledger_entries")
    pricing_group = relationship("PricingGroup", back_populates="ledger_entries")
    department = relationship("Department", back_populates="ledger_entries")
