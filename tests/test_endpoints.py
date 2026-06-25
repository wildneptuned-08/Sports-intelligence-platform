from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.competition import CountryRepository, LeagueRepository
from app.repositories.team import TeamRepository


class TestCompetitionsEndpoint:
    async def test_list_competitions_empty(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/competitions/")
        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_list_competitions_with_data(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        country_repo = CountryRepository(db_session)
        country, _ = await country_repo.upsert_by_code(code="ES", name="Spain")

        league_repo = LeagueRepository(db_session)
        await league_repo.upsert(
            external_id="140", name="La Liga", slug="la-liga", country_id=country.id
        )
        await db_session.commit()

        response = await client.get("/api/v1/competitions/")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "La Liga"

    async def test_list_competitions_pagination(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        country_repo = CountryRepository(db_session)
        country, _ = await country_repo.upsert_by_code(code="ES", name="Spain")

        league_repo = LeagueRepository(db_session)
        await league_repo.upsert(
            external_id="140", name="La Liga", slug="la-liga", country_id=country.id
        )
        await league_repo.upsert(
            external_id="39", name="Premier League", slug="premier-league", country_id=country.id
        )
        await db_session.commit()

        response = await client.get("/api/v1/competitions/?limit=1&offset=0")
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 1
        assert body["total"] == 2


class TestTeamsEndpoint:
    async def test_list_teams_empty(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/teams/")
        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_list_teams_with_data(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        team_repo = TeamRepository(db_session)
        await team_repo.upsert(external_id="541", name="Real Madrid", slug="real-madrid")
        await db_session.commit()

        response = await client.get("/api/v1/teams/")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Real Madrid"


class TestMatchesEndpoint:
    async def test_list_matches_empty(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/matches/")
        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["total"] == 0
