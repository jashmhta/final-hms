import models
import pytest
from database import Base
from fastapi.testclient import TestClient
from main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_prescription.db"
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
    assert response.json()["status"] == "healthy"
def test_create_and_get_medication():
    medication_data = {
        "name": "Test Medication",
        "generic_name": "Test Generic",
        "dosage_form": "Tablet",
        "strength": "500mg",
        "manufacturer": "Test Pharma",
        "ndc_code": "12345-6789-01",
        "is_controlled": False,
    }
    response = client.post("/medications/", json=medication_data)
    assert response.status_code == 200
    medication_id = response.json()["id"]
    response = client.get(f"/medications/{medication_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Medication"
def test_create_prescription():
    medication_data = {
        "name": "Aspirin",
        "generic_name": "Acetylsalicylic Acid",
        "dosage_form": "Tablet",
        "strength": "81mg",
        "manufacturer": "Bayer",
        "ndc_code": "12345-6789-02",
        "is_controlled": False,
    }
    medication_response = client.post("/medications/", json=medication_data)
    medication_id = medication_response.json()["id"]
    prescription_data = {
        "patient_id": 1,
        "doctor_id": 1,
        "medication_id": medication_id,
        "dosage": "1 tablet",
        "frequency": "daily",
        "duration": 30,
        "quantity": 30,
        "instructions": "Take with food",
        "refills_allowed": 2,
    }
    response = client.post("/prescriptions/", json=prescription_data)
    assert response.status_code == 200
    assert response.json()["prescription_number"].startswith("RX-")
def test_safety_check():
    med1_data = {
        "name": "Medication A",
        "generic_name": "Generic A",
        "dosage_form": "Tablet",
        "strength": "100mg",
        "manufacturer": "Pharma A",
        "ndc_code": "12345-6789-03",
        "is_controlled": False,
    }
    med2_data = {
        "name": "Medication B",
        "generic_name": "Generic B",
        "dosage_form": "Tablet",
        "strength": "200mg",
        "manufacturer": "Pharma B",
        "ndc_code": "12345-6789-04",
        "is_controlled": False,
    }
    med1_response = client.post("/medications/", json=med1_data)
    med2_response = client.post("/medications/", json=med2_data)
    med1_id = med1_response.json()["id"]
    med2_id = med2_response.json()["id"]
    safety_data = {
        "patient_id": 1,
        "medication_ids": [med1_id, med2_id],
        "existing_prescriptions": [],
    }
    response = client.post("/safety/check", json=safety_data)
    assert response.status_code == 200
    assert "has_interactions" in response.json()
def test_pharmacy_operations():
    pharmacy_data = {
        "name": "Test Pharmacy",
        "address": "123 Test St",
        "phone": "555-1234",
        "email": "test@pharmacy.com",
        "license_number": "PH12345",
    }
    response = client.post("/pharmacies/", json=pharmacy_data)
    assert response.status_code == 200
    response = client.get("/pharmacies/")
    assert response.status_code == 200
    assert len(response.json()) > 0
if __name__ == "__main__":
    pytest.main(["-v"])