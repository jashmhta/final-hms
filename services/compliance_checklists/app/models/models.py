from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ComplianceChecklist(Base):
    __tablename__ = "compliance_checklists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    standard = Column(String)
    category = Column(String)
    version = Column(String)


class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, index=True)
    item_text = Column(Text)
    required = Column(Boolean, default=True)
    evidence_required = Column(Boolean, default=False)
    frequency = Column(String)


class ComplianceAudit(Base):
    __tablename__ = "compliance_audits"
    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer)
    item_id = Column(Integer)
    compliant = Column(Boolean)
    notes = Column(Text)
    auditor_id = Column(Integer)
    audit_date = Column(DateTime, default=datetime.utcnow)


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
