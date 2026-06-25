from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
_MAX_RETRIES = 3


class APIFootballError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"API-Football error {status_code}: {message}")


class APIFootballClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.api_football_base_url
        self._headers = {
            "x-apisports-key": settings.api_football_key,
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers,
            timeout=_TIMEOUT,
        )

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        stop=stop_after_attempt(_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request(self, endpoint: str, params: dict[str, Any] | None = None) -> list[dict]:
        async with self._client() as client:
            logger.info(
                "API-Football request",
                extra={"endpoint": endpoint, "params": params},
            )
            response = await client.get(endpoint, params=params)

            if response.status_code == 429:
                raise APIFootballError(429, "Rate limit exceeded")
            if response.status_code != 200:
                raise APIFootballError(response.status_code, response.text)

            data = response.json()
            errors = data.get("errors")
            if errors and (isinstance(errors, dict) and errors or isinstance(errors, list) and len(errors) > 0):
                raise APIFootballError(400, str(errors))

            results = data.get("response", [])
            logger.info(
                "API-Football response",
                extra={"endpoint": endpoint, "results_count": len(results)},
            )
            return results

    async def get_leagues(self) -> list[dict]:
        return await self._request("/leagues")

    async def get_teams(self, league_id: int, season: int) -> list[dict]:
        return await self._request("/teams", params={"league": league_id, "season": season})

    async def get_fixtures(self, league_id: int, season: int) -> list[dict]:
        return await self._request("/fixtures", params={"league": league_id, "season": season})
