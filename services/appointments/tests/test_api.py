import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_create_appointment():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        payload = {
            "patient": 1,
            "doctor": 1,
            "start_at": "2025-01-01T10:00:00",
            "end_at": "2025-01-01T11:00:00",
        }
        response = await client.post("/api/appointments", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["patient"] == 1
        assert data["status"] == "SCHEDULED"


@pytest.mark.asyncio
async def test_list_appointments():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/api/appointments")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_available_slots():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/api/appointments/available_slots?doctor=1&date=2025-01-01"
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
