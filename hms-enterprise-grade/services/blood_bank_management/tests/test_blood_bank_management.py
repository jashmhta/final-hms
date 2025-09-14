import models
import pytest
from database import Base
from fastapi.testclient import TestClient
from main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///./test_blood_bank.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def test_client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        yield client
    Base.metadata.drop_all(bind=engine)


def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_donor(test_client):
    donor_data = {
        "donor_id": "DON001",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01T00:00:00",
        "gender": "Male",
        "blood_type": "A+",
        "rh_factor": "Positive",
        "contact_number": "+1234567890",
        "email": "john.doe@example.com",
        "address": "123 Main St",
        "eligibility_status": "eligible",
        "total_donations": 0,
    }
    response = test_client.post("/donors/", json=donor_data)
    assert response.status_code == 200
    assert response.json()["donor_id"] == "DON001"


def test_create_blood_unit(test_client):
    blood_unit_data = {
        "unit_number": "BLOOD001",
        "blood_type": "A+",
        "rh_factor": "Positive",
        "collection_date": "2024-01-01T10:00:00",
        "expiration_date": "2024-02-01T10:00:00",
        "volume_ml": 450,
        "donor_id": 1,
        "test_results": {"HIV": "negative", "Hepatitis_B": "negative"},
        "status": "available",
        "storage_location": "Fridge A1",
    }
    response = test_client.post("/blood-units/", json=blood_unit_data)
    assert response.status_code == 200
    assert response.json()["unit_number"] == "BLOOD001"


def test_get_blood_unit(test_client):
    response = test_client.get("/blood-units/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_create_transfusion_request(test_client):
    request_data = {
        "request_id": "REQ001",
        "patient_id": 1,
        "patient_blood_type": "A+",
        "patient_rh_factor": "Positive",
        "requested_blood_type": "A+",
        "requested_rh_factor": "Positive",
        "units_requested": 2,
        "urgency": "urgent",
        "requested_by": "Dr. Smith",
        "request_date": "2024-01-01T12:00:00",
        "status": "pending",
    }
    response = test_client.post("/transfusion-requests/", json=request_data)
    assert response.status_code == 200
    assert response.json()["request_id"] == "REQ001"
