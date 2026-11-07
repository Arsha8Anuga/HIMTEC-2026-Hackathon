"""Dependency smoke tests for the engine environment.

No medical values, classifications, or API contract details are assumed here.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
import pytest


def test_fastapi_and_httpx_work_together() -> None:
    """FastAPI's TestClient requires a compatible httpx installation."""
    application = FastAPI()

    @application.get("/dependency-smoke-test")
    def probe() -> dict[str, bool]:
        return {"ok": True}

    with TestClient(application) as client:
        response = client.get("/dependency-smoke-test")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_pydantic_v2_validation() -> None:
    """Validate a generic schema without adding fields to the project contract."""
    class SampleModel(BaseModel):
        value: int

    assert SampleModel(value=1).value == 1
    with pytest.raises(ValidationError):
        SampleModel(value="invalid")
