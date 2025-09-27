"""
test_backup_disaster_recovery module
"""

import models
import pytest
from database import Base
from fastapi.testclient import TestClient
from main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_backup.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
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
    assert "healthy" in response.json()["status"]


def test_create_backup_job():
    backup_job_data = {
        "job_name": "test-backup",
        "description": "Test backup job",
        "schedule_type": "daily",
        "schedule_config": {"time": "02:00"},
        "target_type": "database",
        "target_config": {"database": "test_db"},
        "storage_type": "local",
        "storage_config": {"path": "/backups"},
    }
    response = client.post("/backup-jobs/", json=backup_job_data)
    assert response.status_code == 200
    data = response.json()
    assert data["job_name"] == "test-backup"
    assert data["is_active"] == True


def test_get_backup_jobs():
    response = client.get("/backup-jobs/")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_create_disaster_recovery_plan():
    plan_data = {
        "plan_name": "test-plan",
        "description": "Test disaster recovery plan",
        "rpo_minutes": 60,
        "rto_minutes": 120,
        "priority_level": "high",
        "components": {"databases": ["main_db"], "services": ["api"]},
        "procedures": "Recovery procedures",
        "contact_persons": {"primary": "admin@test.com"},
    }
    response = client.post("/disaster-recovery-plans/", json=plan_data)
    assert response.status_code == 200
    data = response.json()
    assert data["plan_name"] == "test-plan"
    assert data["rpo_minutes"] == 60


def test_get_disaster_recovery_plans():
    response = client.get("/disaster-recovery-plans/")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_create_storage_configuration():
    config_data = {
        "name": "test-storage",
        "provider": "aws",
        "config": {"bucket": "test-bucket", "region": "us-east-1"},
    }
    response = client.post("/storage-configurations/", json=config_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-storage"
    assert data["provider"] == "aws"
