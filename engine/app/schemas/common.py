"""Response envelope and error format from docs/CONTRACT.md v0.4."""

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    """Reject undocumented JSON fields instead of silently accepting drift."""

    model_config = ConfigDict(extra="forbid")


class APIError(ContractModel):
    code: Literal["VALIDATION_ERROR", "NOT_FOUND", "ENGINE_UNAVAILABLE", "INTERNAL"]
    message: str
    fields: dict[str, str] | None = None


T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """Standard envelope used by both Go and Python services."""

    data: T | None
    error: APIError | None


class HealthData(ContractModel):
    status: Literal["ok"] = "ok"
    who_tables_loaded: bool = Field(description="True only after official WHO data is loaded")
