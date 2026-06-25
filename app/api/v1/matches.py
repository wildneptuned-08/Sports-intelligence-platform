from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.match import MatchRepository
from app.schemas.match import MatchResponse, PaginatedMatches

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedMatches,
    summary="List matches",
)
async def list_matches(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedMatches:
    repo = MatchRepository(db)
    matches = await repo.list_all(offset=offset, limit=limit)
    total = await repo.count()
    return PaginatedMatches(
        items=[MatchResponse.model_validate(m) for m in matches],
        total=total,
        offset=offset,
        limit=limit,
    )
