from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TeamResponse(BaseModel):
    id: int
    external_id: str | None = None
    name: str
    short_name: str | None = None
    slug: str
    logo_url: str | None = None
    founded_year: int | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedTeams(BaseModel):
    items: list[TeamResponse]
    total: int
    offset: int
    limit: int
