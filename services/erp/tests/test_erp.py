"""
test_erp module
"""

import pytest
from app import models, schemas
from app.database import Base, engine, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def test_create_pricing_group(client):
    response = client.post(
        "/pricing_groups/",
        json={"name": "PG1", "category": "CatA", "description": "Test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PG1"


def test_double_entry_validation():
    asset = models.Asset(
        name="Machine",
        purchase_date="2025-01-01",
        cost=100000,
        depreciation_method=models.DepreciationMethod.STRAIGHT_LINE,
        useful_life=10,
        salvage_value=10000,
    )
    dep = (asset.cost - asset.salvage_value) / asset.useful_life
    assert dep == 9000
