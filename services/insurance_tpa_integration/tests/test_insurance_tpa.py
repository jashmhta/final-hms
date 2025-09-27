"""
test_insurance_tpa module
"""

import models
import pytest
from fastapi.testclient import TestClient
from main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_insurance_provider():
    provider_data = {
        "name": "Test Insurance",
        "code": "TESTINS",
        "tpa_code": "TPA001",
        "api_endpoint": "https://api.test.com",
        "is_active": True,
    }
    response = client.post("/providers/", json=provider_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Insurance"
    assert data["code"] == "TESTINS"


def test_create_insurance_policy():
    policy_data = {
        "patient_id": 1,
        "policy_number": "POL123456",
        "insurance_provider_id": 1,
        "effective_date": "2024-01-01T00:00:00",
        "expiration_date": "2024-12-31T23:59:59",
        "coverage_details": {
            "coverage_type": "comprehensive",
            "max_coverage": 1000000,
            "deductible": 1000,
        },
    }
    response = client.post("/policies/", json=policy_data)
    assert response.status_code == 200
    data = response.json()
    assert data["policy_number"] == "POL123456"


def test_create_insurance_claim():
    claim_data = {
        "patient_id": 1,
        "policy_id": 1,
        "billing_id": 1,
        "total_amount": 1500.0,
        "status": "submitted",
    }
    response = client.post("/claims/", json=claim_data)
    assert response.status_code == 200
    data = response.json()
    assert data["total_amount"] == 1500.0
    assert "CLM-" in data["claim_number"]


def test_eligibility_check():
    eligibility_data = {
        "patient_id": 1,
        "policy_id": 1,
        "service_date": "2024-06-01T10:00:00",
    }
    response = client.post("/eligibility/check", json=eligibility_data)
    assert response.status_code == 200
    data = response.json()
    assert data["is_eligible"] == True


def test_claim_submission():
    response = client.post("/claims/1/submit?tpa_provider_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "transaction" in data
