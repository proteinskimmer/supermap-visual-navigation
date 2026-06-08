from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.responses import fail


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content=fail(message))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(item) for item in first_error.get("loc", []))
    detail = first_error.get("msg", "invalid request")
    message = f"request validation failed at {location}: {detail}" if location else detail
    return JSONResponse(status_code=422, content=fail(message, data={"errors": exc.errors()}))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=fail(f"internal server error: {exc.__class__.__name__}"))
