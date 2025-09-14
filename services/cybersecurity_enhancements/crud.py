from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from . import models, schemas


def create_security_event(db: Session, event: schemas.SecurityEventCreate):
    db_event = models.SecurityEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_security_events(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.SecurityEvent)
        .order_by(desc(models.SecurityEvent.timestamp))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_security_event_by_id(db: Session, event_id: int):
    return (
        db.query(models.SecurityEvent)
        .filter(models.SecurityEvent.id == event_id)
        .first()
    )


def create_audit_log(db: Session, log: schemas.AuditLogCreate):
    db_log = models.AuditLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_audit_logs(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.AuditLog)
        .order_by(desc(models.AuditLog.timestamp))
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_security_policy(db: Session, policy: schemas.SecurityPolicyCreate):
    db_policy = models.SecurityPolicy(**policy.dict())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy


def get_security_policies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SecurityPolicy).offset(skip).limit(limit).all()


def get_security_policy_by_id(db: Session, policy_id: int):
    return (
        db.query(models.SecurityPolicy)
        .filter(models.SecurityPolicy.id == policy_id)
        .first()
    )


def create_access_control_rule(db: Session, rule: schemas.AccessControlRuleCreate):
    db_rule = models.AccessControlRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


def get_access_control_rules(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AccessControlRule).offset(skip).limit(limit).all()


def create_incident(db: Session, incident: schemas.IncidentCreate):
    db_incident = models.Incident(**incident.dict())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident


def get_incidents(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Incident)
        .order_by(desc(models.Incident.reported_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_incident_by_id(db: Session, incident_id: int):
    return db.query(models.Incident).filter(models.Incident.id == incident_id).first()


def create_compliance_check(db: Session, check: schemas.ComplianceCheckCreate):
    db_check = models.ComplianceCheck(**check.dict())
    db.add(db_check)
    db.commit()
    db.refresh(db_check)
    return db_check


def get_compliance_checks(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.ComplianceCheck)
        .order_by(desc(models.ComplianceCheck.last_check))
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_encryption_key(db: Session, key: schemas.EncryptionKeyCreate):
    db_key = models.EncryptionKey(**key.dict())
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key


def get_encryption_keys(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.EncryptionKey).offset(skip).limit(limit).all()
