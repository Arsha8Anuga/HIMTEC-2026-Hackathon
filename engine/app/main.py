"""FastAPI entry point. Run: uvicorn app.main:app --host 0.0.0.0 --port 8001"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.errors import handle_not_found, handle_request_validation, handle_who_unavailable, handle_internal
from app.api.evaluation import router as evaluation_router
from app.api.health import router as health_router
from app.core.who_tables import WHODataError


def create_app() -> FastAPI:
    app = FastAPI(title="HIMTEC Growth Engine", version="0.4.0")
    app.add_exception_handler(RequestValidationError, handle_request_validation)
    app.add_exception_handler(404, handle_not_found)
    app.add_exception_handler(WHODataError, handle_who_unavailable)
    app.add_exception_handler(Exception, handle_internal)
    app.include_router(health_router, prefix="/engine/v1")
    app.include_router(evaluation_router, prefix="/engine/v1")
    return app


app = create_app()

