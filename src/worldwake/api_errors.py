"""Safe HTTP error responses shared across WorldWake APIs."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


SAFE_VALIDATION_ERROR_FIELDS = (
    "type",
    "loc",
    "msg",
)


def sanitize_validation_error(
    error: dict[str, Any],
) -> dict[str, Any]:
    """Remove submitted values from a validation error."""

    return {
        field_name: error[field_name]
        for field_name in SAFE_VALIDATION_ERROR_FIELDS
        if field_name in error
    }


def install_error_handlers(app: FastAPI) -> None:
    """Install WorldWake's safe HTTP exception handlers."""

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        _request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        """Return validation details without echoing request input."""

        safe_errors = [
            sanitize_validation_error(item)
            for item in error.errors()
        ]

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": safe_errors,
            },
        )