import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..database import Base, get_db
from ..main import app

SQLITE_TEST_DB = "sqlite:///:memory:"

engine = create_engine(
    SQLITE_TEST_DB,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_security_event():
    event_data = {
        "event_id": "sec-001",
        "event_type": "login_attempt",
        "severity": "medium",
        "timestamp": "2024-01-01T10:00:00",
        "user_id": 1,
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "resource": "/api/login",
        "action": "login",
        "details": {"attempts": 3},
        "status": "new",
    }
    response = client.post("/security-events/", json=event_data)
    assert response.status_code == 200
    assert response.json()["event_id"] == "sec-001"


def test_get_security_events():
    response = client.get("/security-events/")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_create_audit_log():
    log_data = {
        "log_id": "audit-001",
        "timestamp": "2024-01-01T10:00:00",
        "user_id": 1,
        "user_role": "admin",
        "action": "create",
        "resource_type": "patient",
        "resource_id": 123,
        "resource_name": "John Doe",
        "changes": {"status": "active"},
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "status": "success",
        "details": "Patient record created",
    }
    response = client.post("/audit-logs/", json=log_data)
    assert response.status_code == 200
    assert response.json()["log_id"] == "audit-001"


def test_create_security_policy():
    policy_data = {
        "policy_id": "policy-001",
        "name": "Password Policy",
        "description": "Minimum password requirements",
        "policy_type": "access_control",
        "rules": {"min_length": 12, "complexity": True},
        "created_by": "admin",
    }
    response = client.post("/security-policies/", json=policy_data)
    assert response.status_code == 200
    assert response.json()["policy_id"] == "policy-001"


def test_create_incident():
    incident_data = {
        "incident_id": "inc-001",
        "title": "Unauthorized Access Attempt",
        "description": "Multiple failed login attempts",
        "severity": "high",
        "status": "investigating",
        "reported_by": "security-system",
        "reported_at": "2024-01-01T10:00:00",
        "affected_systems": {"systems": ["auth-service"]},
    }
    response = client.post("/incidents/", json=incident_data)
    assert response.status_code == 200
    assert response.json()["incident_id"] == "inc-001"
