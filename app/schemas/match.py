from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MatchResponse(BaseModel):
    id: int
    external_id: str | None = None
    slug: str
    kickoff_utc: datetime
    round: str | None = None
    status: str
    home_score: int | None = None
    away_score: int | None = None
    home_score_ht: int | None = None
    away_score_ht: int | None = None
    referee_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedMatches(BaseModel):
    items: list[MatchResponse]
    total: int
    offset: int
    limit: int
