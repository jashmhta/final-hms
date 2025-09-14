from datetime import datetime, timedelta

import pytest
from database import Base, get_db
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "OPD Management Service is running"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "healthy" in response.json()["status"]


def test_create_patient():
    patient_data = {
        "patient_id": "PAT001",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01T00:00:00",
        "gender": "Male",
        "contact_number": "+1234567890",
        "email": "john.doe@example.com",
    }
    response = client.post("/patients/", json=patient_data)
    assert response.status_code == 200
    assert response.json()["first_name"] == "John"


def test_create_doctor():
    doctor_data = {
        "doctor_id": "DOC001",
        "first_name": "Jane",
        "last_name": "Smith",
        "specialization": "Cardiology",
        "qualification": "MD",
        "contact_number": "+1234567891",
        "email": "jane.smith@example.com",
        "consultation_fee": 150.0,
        "working_hours": {"hours": [{"start": "09:00", "end": "17:00"}]},
    }
    response = client.post("/doctors/", json=doctor_data)
    assert response.status_code == 200
    assert response.json()["specialization"] == "Cardiology"


def test_create_appointment():
    appointment_data = {
        "appointment_id": "APT001",
        "patient_id": 1,
        "doctor_id": 1,
        "appointment_date": "2024-01-15T10:00:00",
        "status": "scheduled",
        "consultation_type": "general",
        "created_by": "system",
    }
    response = client.post("/appointments/", json=appointment_data)
    assert response.status_code == 200
    assert response.json()["status"] == "scheduled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
