from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application health check",
    description=(
        "Returns the operational status of the API, database connection, "
        "and background scheduler."
    ),
)
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        logger.error("DB health check failed", extra={"error": str(exc)})
        db_status = "error"

    scheduler = getattr(request.app.state, "scheduler", None)
    scheduler_status = "running" if (scheduler and scheduler.running) else "stopped"

    overall = "ok" if db_status == "ok" else "degraded"

    return HealthResponse(
        status=overall,
        db=db_status,
        scheduler=scheduler_status,
        environment=settings.environment.value,
    )


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Returns 200 when the service can accept traffic, 503 otherwise. Used by Render health checks.",
    tags=["Health"],
)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not ready",
        )
