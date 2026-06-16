from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import get_db
from app.main import app
from app.models.base import Base

# Import all models so Base.metadata is fully populated before create_all
import app.models  # noqa: F401

# ── Test database URL ─────────────────────────────────────────────────────────
# Uses a dedicated test database to avoid corrupting development data.
# The CI workflow (see .github/workflows/ci.yml) sets TEST_DATABASE_URL via env.
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://sip:sip_password@localhost:5432/sip_test",
)


# ── Session-scoped engine and schema ─────────────────────────────────────────
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create the test engine and schema once per test session."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)

    # Enable pg_trgm before creating tables (required by trigram indexes)
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ── Per-test DB session with automatic rollback ───────────────────────────────
@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncSession:
    """Each test gets a rolled-back session — no data bleeds between tests."""
    TestSession = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with TestSession() as session:
        yield session
        await session.rollback()


# ── HTTP test client ──────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """
    FastAPI test client that:
      - Uses the rolled-back test DB session (via dependency override)
      - Runs the full lifespan (APScheduler starts/stops)
    """

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
