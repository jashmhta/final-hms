from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cybersecurity Enhancements Service",
    description="Enterprise-grade security monitoring and compliance management",
    version="1.0.0",
)


@app.post("/security-events/", response_model=schemas.SecurityEvent)
def create_security_event(
    event: schemas.SecurityEventCreate, db: Session = Depends(get_db)
):
    return crud.create_security_event(db=db, event=event)


@app.get("/security-events/", response_model=List[schemas.SecurityEvent])
def read_security_events(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return crud.get_security_events(db=db, skip=skip, limit=limit)


@app.post("/audit-logs/", response_model=schemas.AuditLog)
def create_audit_log(log: schemas.AuditLogCreate, db: Session = Depends(get_db)):
    return crud.create_audit_log(db=db, log=log)


@app.get("/audit-logs/", response_model=List[schemas.AuditLog])
def read_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_audit_logs(db=db, skip=skip, limit=limit)


@app.post("/security-policies/", response_model=schemas.SecurityPolicy)
def create_security_policy(
    policy: schemas.SecurityPolicyCreate, db: Session = Depends(get_db)
):
    return crud.create_security_policy(db=db, policy=policy)


@app.get("/security-policies/", response_model=List[schemas.SecurityPolicy])
def read_security_policies(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return crud.get_security_policies(db=db, skip=skip, limit=limit)


@app.post("/access-control-rules/", response_model=schemas.AccessControlRule)
def create_access_control_rule(
    rule: schemas.AccessControlRuleCreate, db: Session = Depends(get_db)
):
    return crud.create_access_control_rule(db=db, rule=rule)


@app.get("/access-control-rules/", response_model=List[schemas.AccessControlRule])
def read_access_control_rules(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return crud.get_access_control_rules(db=db, skip=skip, limit=limit)


@app.post("/incidents/", response_model=schemas.Incident)
def create_incident(incident: schemas.IncidentCreate, db: Session = Depends(get_db)):
    return crud.create_incident(db=db, incident=incident)


@app.get("/incidents/", response_model=List[schemas.Incident])
def read_incidents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_incidents(db=db, skip=skip, limit=limit)


@app.post("/compliance-checks/", response_model=schemas.ComplianceCheck)
def create_compliance_check(
    check: schemas.ComplianceCheckCreate, db: Session = Depends(get_db)
):
    return crud.create_compliance_check(db=db, check=check)


@app.get("/compliance-checks/", response_model=List[schemas.ComplianceCheck])
def read_compliance_checks(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return crud.get_compliance_checks(db=db, skip=skip, limit=limit)


@app.post("/encryption-keys/", response_model=schemas.EncryptionKey)
def create_encryption_key(
    key: schemas.EncryptionKeyCreate, db: Session = Depends(get_db)
):
    return crud.create_encryption_key(db=db, key=key)


@app.get("/encryption-keys/", response_model=List[schemas.EncryptionKey])
def read_encryption_keys(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return crud.get_encryption_keys(db=db, skip=skip, limit=limit)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "cybersecurity-enhancements"}
