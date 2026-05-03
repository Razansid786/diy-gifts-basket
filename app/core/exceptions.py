
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class AppException(Exception):

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)

class NotFoundError(AppException):

    def __init__(self, resource: str = "Resource", identifier: str = ""):
        detail = f"{resource} not found."
        if identifier:
            detail = f"{resource} with id '{identifier}' not found."
        super().__init__(detail=detail, status_code=404)

class ConflictError(AppException):

    def __init__(self, detail: str = "Resource already exists."):
        super().__init__(detail=detail, status_code=409)

class ForbiddenError(AppException):

    def __init__(self, detail: str = "You do not have permission to perform this action."):
        super().__init__(detail=detail, status_code=403)

class ValidationError(AppException):

    def __init__(self, detail: str = "Validation failed."):
        super().__init__(detail=detail, status_code=422)

def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )