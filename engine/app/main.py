"""FastAPI entry point. Run: uvicorn app.main:app --host 0.0.0.0 --port 8001"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.errors import handle_not_found, handle_request_validation
from app.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="HIMTEC Growth Engine", version="0.4.0")
    app.add_exception_handler(RequestValidationError, handle_request_validation)
    app.add_exception_handler(404, handle_not_found)
    app.include_router(health_router, prefix="/engine/v1")
    return app


app = create_app()
