import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import init_db
from app.main import app


@pytest.fixture()
def client():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        get_settings.cache_clear()
        app.dependency_overrides = {}

        import os

        os.environ["FRIDGE_GPT_DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["FRIDGE_GPT_TOKEN"] = "test-token"
        get_settings.cache_clear()
        init_db()

        with TestClient(app) as test_client:
            yield test_client

        get_settings.cache_clear()


def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}


def valid_payload() -> dict:
    return {
        "source": "nofrills",
        "page_url": "https://www.nofrills.ca/checkout",
        "delivered_at": "2026-05-09T18:30:00Z",
        "subtotal": 12.34,
        "total": 13.94,
        "items": [
            {
                "name": "Bananas",
                "quantity": 2,
                "unit_price": 1.99,
                "line_total": 3.98,
                "shelf_life": 5,
                "amount": "full",
            }
        ],
        "raw_parser_warnings": [],
    }


def test_create_and_read_snapshot(client):
    create_response = client.post(
        "/api/checkout-snapshots",
        json=valid_payload(),
        headers=auth_headers(),
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == 1
    assert created["items"][0]["name"] == "Bananas"
    assert created["items"][0]["shelf_life"] == 5
    assert created["items"][0]["amount"] == "full"
    assert created["delivered_at"] == "2026-05-09T18:30:00Z"

    list_response = client.get("/api/checkout-snapshots", headers=auth_headers())
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(
        "/api/checkout-snapshots/1",
        headers=auth_headers(),
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["total"] == 13.94
    assert detail_response.json()["delivered_at"] == "2026-05-09T18:30:00Z"


def test_rejects_missing_token(client):
    response = client.post("/api/checkout-snapshots", json=valid_payload())

    assert response.status_code == 401


def test_rejects_invalid_payload(client):
    payload = valid_payload()
    payload["items"] = []

    response = client.post(
        "/api/checkout-snapshots",
        json=payload,
        headers=auth_headers(),
    )

    assert response.status_code == 422


def test_rejects_invalid_item_amount(client):
    payload = valid_payload()
    payload["items"][0]["amount"] = "mostly"

    response = client.post(
        "/api/checkout-snapshots",
        json=payload,
        headers=auth_headers(),
    )

    assert response.status_code == 422


def test_returns_404_for_missing_snapshot(client):
    response = client.get("/api/checkout-snapshots/999", headers=auth_headers())

    assert response.status_code == 404
