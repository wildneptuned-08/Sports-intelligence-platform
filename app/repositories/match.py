from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.match import Match
from app.repositories.base import BaseRepository


class MatchRepository(BaseRepository[Match]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Match, session)

    async def get_by_external_id_with_teams(self, external_id: str) -> Match | None:
        stmt = (
            select(Match)
            .where(Match.external_id == external_id)
            .options(joinedload(Match.home_team), joinedload(Match.away_team))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_league_season(
        self, league_season_id: int, offset: int = 0, limit: int = 50
    ) -> list[Match]:
        stmt = (
            select(Match)
            .where(Match.league_season_id == league_season_id)
            .order_by(Match.kickoff_utc)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
