from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    db: str
    scheduler: str
    environment: str = "development"
    version: str = "0.1.0"

    model_config = {"json_schema_extra": {"example": {
        "status": "ok",
        "db": "ok",
        "scheduler": "running",
        "environment": "production",
        "version": "0.1.0",
    }}}
