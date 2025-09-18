import pytest
from datetime import datetime, timedelta
from app.main import AppointmentModel, AppointmentIn
def test_appointment_model_creation(db):
    appointment_data = AppointmentIn(
        patient=1,
        doctor=1,
        start_at=datetime(2025, 1, 1, 10, 0),
        end_at=datetime(2025, 1, 1, 11, 0),
    )
    obj = AppointmentModel(**appointment_data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    assert obj.id is not None
    assert obj.patient == 1
    assert obj.doctor == 1
    assert obj.status == "SCHEDULED"