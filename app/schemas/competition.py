from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CountryResponse(BaseModel):
    id: int
    name: str
    code: str
    flag_url: str | None = None

    model_config = {"from_attributes": True}


class LeagueResponse(BaseModel):
    id: int
    external_id: str | None = None
    name: str
    slug: str
    country: CountryResponse | None = None
    league_type: str
    logo_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedLeagues(BaseModel):
    items: list[LeagueResponse]
    total: int
    offset: int
    limit: int
