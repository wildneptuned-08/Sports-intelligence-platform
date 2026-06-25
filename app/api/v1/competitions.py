from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.competition import League
from app.repositories.competition import LeagueRepository
from app.schemas.competition import LeagueResponse, PaginatedLeagues

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedLeagues,
    summary="List competitions",
)
async def list_competitions(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedLeagues:
    repo = LeagueRepository(db)
    leagues = await repo.list_all(offset=offset, limit=limit)
    total = await repo.count()
    return PaginatedLeagues(
        items=[LeagueResponse.model_validate(l) for l in leagues],
        total=total,
        offset=offset,
        limit=limit,
    )
