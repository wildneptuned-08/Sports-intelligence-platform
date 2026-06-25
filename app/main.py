from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.config import get_settings
from app.core.exceptions import add_exception_handlers
from app.core.logging import setup_logging
from app.etl.scheduler import create_scheduler

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.log_level)

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
        )
        logger.info("Sentry initialized")

    scheduler = create_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info(
        "Application startup complete",
        extra={
            "environment": settings.environment,
            "scheduler_jobs": len(scheduler.get_jobs()),
        },
    )

    yield

    scheduler.shutdown(wait=False)
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sports Intelligence Platform",
        description=(
            "Plataforma de inteligencia deportiva predictiva para fútbol. "
            "Proporciona predicciones basadas en modelos estadísticos, "
            "analytics de equipos y jugadores, y datos históricos de ligas."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # CORS — development: permissive; production: locked to allowed_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check at root (not under /api/v1/)
    app.include_router(health_router)

    # All REST API routes under /api/v1/
    app.include_router(api_router, prefix=settings.api_prefix)

    add_exception_handlers(app)

    return app


app = create_app()
