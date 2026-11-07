"""Test the health endpoint and the shared validation error envelope."""

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.growth import GrowthEvaluateRequest


def test_health_reports_missing_who_tables_honestly() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/engine/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "data": {"status": "ok", "who_tables_loaded": False},
        "error": None,
    }


def test_health_route_has_contract_prefix() -> None:
    with TestClient(create_app()) as client:
        unknown = client.get("/health")
        assert unknown.status_code == 404
        assert unknown.json()["error"]["code"] == "NOT_FOUND"
        openapi = client.get("/openapi.json").json()
    assert "/engine/v1/health" in openapi["paths"]
    assert "/engine/v1/growth/evaluate" not in openapi["paths"]


def test_validation_error_uses_contract_envelope() -> None:
    application = create_app()

    # Test-only route: production must not advertise an unimplemented
    # clinical endpoint as ready.
    @application.post("/engine/v1/growth/evaluate")
    def test_only_endpoint(payload: GrowthEvaluateRequest) -> dict[str, bool]:
        return {"valid": True}

    with TestClient(application) as client:
        response = client.post("/engine/v1/growth/evaluate", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "food_recalls" in body["error"]["fields"]
    assert "child" in body["error"]["fields"]
    assert "detail" not in body
