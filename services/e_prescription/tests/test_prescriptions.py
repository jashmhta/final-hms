import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db
import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_prescription():
    response = client.post(
        "/prescriptions/",
        json={
            "patient_id": 1,
            "doctor_id": 1,
            "diagnosis": "Common cold",
            "items": [
                {
                    "drug_id": 1,
                    "dosage": "500mg",
                    "frequency": "twice daily",
                    "duration": "7 days",
                    "quantity": 14,
                    "instructions": "Take after food"
                }
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == 1
    assert data["doctor_id"] == 1
    assert data["diagnosis"] == "Common cold"
    assert len(data["items"]) == 1

def test_get_prescriptions():
    response = client.get("/prescriptions/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
