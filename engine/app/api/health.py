"""Engine health endpoint defined in CONTRACT.md v0.4."""

from fastapi import APIRouter

from app.schemas.common import Envelope, HealthData

router = APIRouter()


@router.get("/health", response_model=Envelope[HealthData])
def health() -> Envelope[HealthData]:
    # There is no official WHO table loader in this patch. Reporting True
    # would silently imply the medical calculation engine is operational.
    return Envelope(data=HealthData(who_tables_loaded=False), error=None)
