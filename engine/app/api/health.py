"""Engine health endpoint defined in CONTRACT.md v0.4."""

from fastapi import APIRouter

from app.core.who_tables import who_tables_loaded
from app.schemas.common import Envelope, HealthData

router = APIRouter()


@router.get("/health", response_model=Envelope[HealthData])
def health() -> Envelope[HealthData]:
    # Only verified, complete WHO tables may set this to true.
    return Envelope(data=HealthData(who_tables_loaded=who_tables_loaded()), error=None)
