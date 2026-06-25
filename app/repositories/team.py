from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team, Venue
from app.repositories.base import BaseRepository


class VenueRepository(BaseRepository[Venue]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Venue, session)


class TeamRepository(BaseRepository[Team]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Team, session)

    async def get_by_slug(self, slug: str) -> Team | None:
        stmt = select(Team).where(Team.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
