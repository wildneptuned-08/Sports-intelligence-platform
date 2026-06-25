from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.etl.fetchers.api_football import APIFootballClient, APIFootballError


class TestAPIFootballClient:
    @pytest.fixture
    def client(self) -> APIFootballClient:
        return APIFootballClient()

    def _mock_response(self, data: list, status_code: int = 200) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            json={"response": data, "errors": []},
            request=httpx.Request("GET", "https://test.com"),
        )

    @patch("app.etl.fetchers.api_football.httpx.AsyncClient")
    async def test_get_leagues(self, mock_client_cls, client) -> None:
        mock_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_instance.get.return_value = self._mock_response([{"league": {"id": 1}}])

        result = await client.get_leagues()

        assert len(result) == 1
        assert result[0]["league"]["id"] == 1
        mock_instance.get.assert_called_once_with("/leagues", params=None)

    @patch("app.etl.fetchers.api_football.httpx.AsyncClient")
    async def test_get_teams(self, mock_client_cls, client) -> None:
        mock_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_instance.get.return_value = self._mock_response([{"team": {"id": 541}}])

        result = await client.get_teams(league_id=140, season=2024)

        assert len(result) == 1
        mock_instance.get.assert_called_once_with(
            "/teams", params={"league": 140, "season": 2024}
        )

    @patch("app.etl.fetchers.api_football.httpx.AsyncClient")
    async def test_get_fixtures(self, mock_client_cls, client) -> None:
        mock_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_instance.get.return_value = self._mock_response([{"fixture": {"id": 1}}])

        result = await client.get_fixtures(league_id=140, season=2024)

        assert len(result) == 1
        mock_instance.get.assert_called_once_with(
            "/fixtures", params={"league": 140, "season": 2024}
        )

    @patch("app.etl.fetchers.api_football.httpx.AsyncClient")
    async def test_rate_limit_raises(self, mock_client_cls, client) -> None:
        mock_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_instance.get.return_value = httpx.Response(
            status_code=429,
            text="Rate limited",
            request=httpx.Request("GET", "https://test.com"),
        )

        with pytest.raises(APIFootballError, match="429"):
            await client.get_leagues()

    @patch("app.etl.fetchers.api_football.httpx.AsyncClient")
    async def test_api_errors_raises(self, mock_client_cls, client) -> None:
        mock_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_instance.get.return_value = httpx.Response(
            status_code=200,
            json={"response": [], "errors": {"token": "Error/Missing application key"}},
            request=httpx.Request("GET", "https://test.com"),
        )

        with pytest.raises(APIFootballError, match="400"):
            await client.get_leagues()

    @patch("app.etl.fetchers.api_football.httpx.AsyncClient")
    async def test_empty_errors_is_ok(self, mock_client_cls, client) -> None:
        mock_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_instance.get.return_value = httpx.Response(
            status_code=200,
            json={"response": [{"id": 1}], "errors": {}},
            request=httpx.Request("GET", "https://test.com"),
        )

        result = await client.get_leagues()
        assert len(result) == 1
