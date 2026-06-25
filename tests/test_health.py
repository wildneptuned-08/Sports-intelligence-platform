from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for GET /health"""

    async def test_health_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_response_schema(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        body = response.json()

        assert "status" in body
        assert "db" in body
        assert "scheduler" in body
        assert "version" in body
        assert "environment" in body

    async def test_health_db_ok(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        body = response.json()
        assert body["db"] == "ok", f"Database health check failed: {body}"

    async def test_health_scheduler_running(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        body = response.json()
        assert body["scheduler"] == "running", f"Scheduler is not running: {body}"

    async def test_health_overall_status_ok(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        body = response.json()
        assert body["status"] == "ok"

    async def test_health_version_present(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        body = response.json()
        assert body["version"] == "0.1.0"


class TestReadinessEndpoint:
    """Tests for GET /health/ready"""

    async def test_ready_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/health/ready")
        assert response.status_code == 200

    async def test_ready_body(self, client: AsyncClient) -> None:
        response = await client.get("/health/ready")
        assert response.json() == {"ready": True}


class TestOpenAPI:
    """Tests for Swagger/OpenAPI availability"""

    async def test_docs_accessible(self, client: AsyncClient) -> None:
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    async def test_openapi_json_accessible(self, client: AsyncClient) -> None:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert spec["info"]["title"] == "Sports Intelligence Platform"
        assert spec["info"]["version"] == "0.1.0"

    async def test_openapi_has_health_path(self, client: AsyncClient) -> None:
        response = await client.get("/openapi.json")
        spec = response.json()
        assert "/health" in spec["paths"]
        assert "/health/ready" in spec["paths"]
