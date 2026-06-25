from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competition import Country, League, Season
from app.models.match import Match
from app.models.team import Team
from app.repositories.competition import (
    CountryRepository,
    LeagueRepository,
    LeagueSeasonRepository,
    SeasonRepository,
)
from app.repositories.match import MatchRepository
from app.repositories.team import TeamRepository


class TestCountryRepository:
    async def test_upsert_by_code_creates(self, db_session: AsyncSession) -> None:
        repo = CountryRepository(db_session)
        country, created = await repo.upsert_by_code(code="ES", name="Spain")
        assert created is True
        assert country.code == "ES"
        assert country.name == "Spain"

    async def test_upsert_by_code_updates(self, db_session: AsyncSession) -> None:
        repo = CountryRepository(db_session)
        await repo.upsert_by_code(code="ES", name="Spain")
        country, created = await repo.upsert_by_code(
            code="ES", name="España", flag_url="https://flag.es"
        )
        assert created is False
        assert country.name == "España"
        assert country.flag_url == "https://flag.es"

    async def test_get_by_code(self, db_session: AsyncSession) -> None:
        repo = CountryRepository(db_session)
        await repo.upsert_by_code(code="GB", name="England")
        found = await repo.get_by_code("GB")
        assert found is not None
        assert found.name == "England"

    async def test_get_by_code_not_found(self, db_session: AsyncSession) -> None:
        repo = CountryRepository(db_session)
        assert await repo.get_by_code("ZZ") is None


class TestLeagueRepository:
    async def _create_country(self, session: AsyncSession) -> Country:
        repo = CountryRepository(session)
        country, _ = await repo.upsert_by_code(code="ES", name="Spain")
        return country

    async def test_upsert_creates(self, db_session: AsyncSession) -> None:
        country = await self._create_country(db_session)
        repo = LeagueRepository(db_session)
        league, created = await repo.upsert(
            external_id="140",
            name="La Liga",
            slug="la-liga",
            country_id=country.id,
        )
        assert created is True
        assert league.external_id == "140"
        assert league.name == "La Liga"

    async def test_upsert_updates(self, db_session: AsyncSession) -> None:
        country = await self._create_country(db_session)
        repo = LeagueRepository(db_session)
        await repo.upsert(external_id="140", name="La Liga", slug="la-liga", country_id=country.id)
        league, created = await repo.upsert(
            external_id="140", name="LaLiga EA Sports", slug="la-liga", country_id=country.id
        )
        assert created is False
        assert league.name == "LaLiga EA Sports"

    async def test_get_active(self, db_session: AsyncSession) -> None:
        country = await self._create_country(db_session)
        repo = LeagueRepository(db_session)
        await repo.upsert(
            external_id="140", name="La Liga", slug="la-liga",
            country_id=country.id, is_active=True,
        )
        await repo.upsert(
            external_id="39", name="Premier League", slug="premier-league",
            country_id=country.id, is_active=False,
        )
        active = await repo.get_active()
        assert len(active) == 1
        assert active[0].name == "La Liga"


class TestSeasonRepository:
    async def test_get_or_create_creates(self, db_session: AsyncSession) -> None:
        repo = SeasonRepository(db_session)
        season, created = await repo.get_or_create(2024)
        assert created is True
        assert season.year == 2024
        assert season.label == "2024/2025"

    async def test_get_or_create_returns_existing(self, db_session: AsyncSession) -> None:
        repo = SeasonRepository(db_session)
        await repo.get_or_create(2024)
        season, created = await repo.get_or_create(2024)
        assert created is False
        assert season.year == 2024


class TestTeamRepository:
    async def test_upsert_creates(self, db_session: AsyncSession) -> None:
        repo = TeamRepository(db_session)
        team, created = await repo.upsert(
            external_id="541",
            name="Real Madrid",
            slug="real-madrid",
        )
        assert created is True
        assert team.external_id == "541"

    async def test_upsert_updates(self, db_session: AsyncSession) -> None:
        repo = TeamRepository(db_session)
        await repo.upsert(external_id="541", name="Real Madrid", slug="real-madrid")
        team, created = await repo.upsert(
            external_id="541", name="Real Madrid CF", slug="real-madrid",
        )
        assert created is False
        assert team.name == "Real Madrid CF"

    async def test_get_by_slug(self, db_session: AsyncSession) -> None:
        repo = TeamRepository(db_session)
        await repo.upsert(external_id="541", name="Real Madrid", slug="real-madrid")
        found = await repo.get_by_slug("real-madrid")
        assert found is not None
        assert found.name == "Real Madrid"

    async def test_list_all(self, db_session: AsyncSession) -> None:
        repo = TeamRepository(db_session)
        await repo.upsert(external_id="541", name="Real Madrid", slug="real-madrid")
        await repo.upsert(external_id="529", name="Barcelona", slug="barcelona")
        teams = await repo.list_all()
        assert len(teams) == 2

    async def test_count(self, db_session: AsyncSession) -> None:
        repo = TeamRepository(db_session)
        assert await repo.count() == 0
        await repo.upsert(external_id="541", name="Real Madrid", slug="real-madrid")
        assert await repo.count() == 1


class TestMatchRepository:
    async def _setup_match_deps(self, session: AsyncSession):
        country_repo = CountryRepository(session)
        country, _ = await country_repo.upsert_by_code(code="ES", name="Spain")

        league_repo = LeagueRepository(session)
        league, _ = await league_repo.upsert(
            external_id="140", name="La Liga", slug="la-liga", country_id=country.id
        )

        season_repo = SeasonRepository(session)
        season, _ = await season_repo.get_or_create(2024)

        ls_repo = LeagueSeasonRepository(session)
        ls, _ = await ls_repo.get_or_create(league_id=league.id, season_id=season.id)

        team_repo = TeamRepository(session)
        home, _ = await team_repo.upsert(external_id="541", name="Real Madrid", slug="real-madrid")
        away, _ = await team_repo.upsert(external_id="529", name="Barcelona", slug="barcelona")

        return ls, home, away

    async def test_upsert_creates(self, db_session: AsyncSession) -> None:
        ls, home, away = await self._setup_match_deps(db_session)
        repo = MatchRepository(db_session)
        from datetime import datetime, timezone

        match, created = await repo.upsert(
            external_id="867946",
            league_season_id=ls.id,
            home_team_id=home.id,
            away_team_id=away.id,
            kickoff_utc=datetime(2024, 9, 1, 19, 0, tzinfo=timezone.utc),
            slug="real-madrid-vs-barcelona-2024-09-01",
            status="FINISHED",
            home_score=2,
            away_score=1,
        )
        assert created is True
        assert match.external_id == "867946"

    async def test_upsert_updates_score(self, db_session: AsyncSession) -> None:
        ls, home, away = await self._setup_match_deps(db_session)
        repo = MatchRepository(db_session)
        from datetime import datetime, timezone

        await repo.upsert(
            external_id="867946",
            league_season_id=ls.id,
            home_team_id=home.id,
            away_team_id=away.id,
            kickoff_utc=datetime(2024, 9, 1, 19, 0, tzinfo=timezone.utc),
            slug="real-madrid-vs-barcelona-2024-09-01",
            status="SCHEDULED",
        )
        match, created = await repo.upsert(
            external_id="867946",
            status="FINISHED",
            home_score=2,
            away_score=1,
        )
        assert created is False
        assert match.status == "FINISHED"
        assert match.home_score == 2
