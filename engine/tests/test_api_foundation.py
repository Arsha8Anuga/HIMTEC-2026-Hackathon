"""Test the health endpoint and the shared validation error envelope."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.mark.parametrize("loaded", [False, True])
def test_health_reports_table_availability(monkeypatch, loaded: bool) -> None:
    monkeypatch.setattr("app.api.health.who_tables_loaded", lambda: loaded)
    with TestClient(create_app()) as client:
        response = client.get("/engine/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "data": {"status": "ok", "who_tables_loaded": loaded},
        "error": None,
    }


def test_health_route_has_contract_prefix() -> None:
    with TestClient(create_app()) as client:
        unknown = client.get("/health")
        assert unknown.status_code == 404
        assert unknown.json()["error"]["code"] == "NOT_FOUND"
        openapi = client.get("/openapi.json").json()
    assert "/engine/v1/health" in openapi["paths"]
    assert "/engine/v1/growth/evaluate" in openapi["paths"]


def test_validation_error_uses_contract_envelope() -> None:
    application = create_app()


    with TestClient(application) as client:
        response = client.post("/engine/v1/growth/evaluate", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "food_recalls" in body["error"]["fields"]
    assert "child" in body["error"]["fields"]
    assert "detail" not in body
