"""FastAPI input errors with the JSON envelope defined by the team contract."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def handle_who_unavailable(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content={
        "data": None,
        "error": {"code": "ENGINE_UNAVAILABLE", "message": "Data atau domain referensi WHO belum dapat digunakan untuk permintaan ini", "fields": None},
    })


async def handle_internal(request: Request, exc: Exception) -> JSONResponse:
    # Server logs retain the traceback; the response contains no submitted
    # history, paths or exception internals.
    return JSONResponse(status_code=500, content={
        "data": None,
        "error": {"code": "INTERNAL", "message": "Terjadi kesalahan internal engine", "fields": None},
    })


def _field_path(location: tuple[str | int, ...]) -> str:
    """Render nested field locations without exposing submitted input values."""
    parts = list(location)
    if parts and parts[0] in {"body", "query", "path"}:
        parts.pop(0)
    return ".".join(str(part) for part in parts) or "request"


async def handle_request_validation(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields = {
        _field_path(tuple(error["loc"])): error["msg"]
        for error in exc.errors()
    }
    return JSONResponse(
        status_code=422,
        content={
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input tidak valid",
                "fields": fields,
            },
        },
    )


async def handle_not_found(request: Request, exc: Exception) -> JSONResponse:
    """Wrap 404 with the documented NOT_FOUND code and standard envelope."""
    return JSONResponse(
        status_code=404,
        content={
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Endpoint tidak ditemukan", "fields": None},
        },
    )

