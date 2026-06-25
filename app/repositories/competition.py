from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competition import Country, League, LeagueSeason, Season
from app.repositories.base import BaseRepository


class CountryRepository(BaseRepository[Country]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Country, session)

    async def get_by_code(self, code: str) -> Country | None:
        stmt = select(Country).where(Country.code == code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_by_code(self, code: str, **kwargs) -> tuple[Country, bool]:
        existing = await self.get_by_code(code)
        if existing:
            instance = await self.update(existing, **kwargs)
            return instance, False
        instance = await self.create(code=code, **kwargs)
        return instance, True


class LeagueRepository(BaseRepository[League]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(League, session)

    async def get_by_slug(self, slug: str) -> League | None:
        stmt = select(League).where(League.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active(self) -> list[League]:
        stmt = select(League).where(League.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class SeasonRepository(BaseRepository[Season]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Season, session)

    async def get_by_year(self, year: int) -> Season | None:
        stmt = select(Season).where(Season.year == year)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, year: int) -> tuple[Season, bool]:
        existing = await self.get_by_year(year)
        if existing:
            return existing, False
        instance = await self.create(year=year, label=f"{year}/{year + 1}")
        return instance, True


class LeagueSeasonRepository(BaseRepository[LeagueSeason]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(LeagueSeason, session)

    async def get_by_league_and_season(
        self, league_id: int, season_id: int
    ) -> LeagueSeason | None:
        stmt = select(LeagueSeason).where(
            LeagueSeason.league_id == league_id,
            LeagueSeason.season_id == season_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self, league_id: int, season_id: int, **kwargs
    ) -> tuple[LeagueSeason, bool]:
        existing = await self.get_by_league_and_season(league_id, season_id)
        if existing:
            return existing, False
        instance = await self.create(
            league_id=league_id, season_id=season_id, **kwargs
        )
        return instance, True
