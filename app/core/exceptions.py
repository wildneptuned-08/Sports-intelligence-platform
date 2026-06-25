from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse

logger = logging.getLogger(__name__)


class SIPException(Exception):
    """Base exception for all domain errors in this application."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def _error_body(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(SIPException)
    async def sip_handler(request: Request, exc: SIPException) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=404,
            content=_error_body("RESOURCE_NOT_FOUND", "The requested resource was not found."),
        )

    @app.exception_handler(500)
    async def internal_handler(request: Request, exc: Exception) -> ORJSONResponse:
        logger.error("Unhandled server error", exc_info=exc)
        return ORJSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred."),
        )


# ── Pre-defined domain exceptions ────────────────────────────────────────────

class NotFoundError(SIPException):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} '{identifier}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class DuplicateResourceError(SIPException):
    def __init__(self, resource: str, field: str) -> None:
        super().__init__(
            code="DUPLICATE_RESOURCE",
            message=f"{resource} with this {field} already exists.",
            status_code=status.HTTP_409_CONFLICT,
        )


class UnauthorizedError(SIPException):
    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(SIPException):
    def __init__(self, message: str = "Insufficient permissions.") -> None:
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )
