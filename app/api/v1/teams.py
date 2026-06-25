from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.team import TeamRepository
from app.schemas.team import PaginatedTeams, TeamResponse

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedTeams,
    summary="List teams",
)
async def list_teams(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedTeams:
    repo = TeamRepository(db)
    teams = await repo.list_all(offset=offset, limit=limit)
    total = await repo.count()
    return PaginatedTeams(
        items=[TeamResponse.model_validate(t) for t in teams],
        total=total,
        offset=offset,
        limit=limit,
    )
