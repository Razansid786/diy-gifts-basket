"""
app/core/exceptions.py
──────────────────────
Custom exception classes and global exception handlers.

These classes let the service layer raise domain-specific errors
without importing FastAPI's ``HTTPException`` directly, keeping
business logic framework-agnostic.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# =====================================================================
# Custom exception classes
# =====================================================================

class AppException(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource", identifier: str = ""):
        detail = f"{resource} not found."
        if identifier:
            detail = f"{resource} with id '{identifier}' not found."
        super().__init__(detail=detail, status_code=404)


class ConflictError(AppException):
    """Raised when an action conflicts with the current state (e.g. duplicate email)."""

    def __init__(self, detail: str = "Resource already exists."):
        super().__init__(detail=detail, status_code=409)


class ForbiddenError(AppException):
    """Raised when the user lacks permission for the requested action."""

    def __init__(self, detail: str = "You do not have permission to perform this action."):
        super().__init__(detail=detail, status_code=403)


class ValidationError(AppException):
    """Raised when business-rule validation fails (distinct from Pydantic schema errors)."""

    def __init__(self, detail: str = "Validation failed."):
        super().__init__(detail=detail, status_code=422)


# =====================================================================
# Global handler registration
# =====================================================================

def register_exception_handlers(app: FastAPI) -> None:
    """
    Attach custom exception handlers to the FastAPI application.

    This ensures that any ``AppException`` raised anywhere in the
    request lifecycle is converted into a consistent JSON response.
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
