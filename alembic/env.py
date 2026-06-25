from __future__ import annotations

import asyncio
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Import all models so Base.metadata is fully populated ────────────────────
from app.models.base import Base
import app.models  # noqa: F401 — triggers all model imports via __init__.py

# ── Alembic config object ─────────────────────────────────────────────────────
config = context.config

# Configure Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# Target metadata for --autogenerate
target_metadata = Base.metadata


def get_url() -> str:
    """Read DATABASE_URL from app settings (overrides alembic.ini placeholder)."""
    from app.config import get_settings
    return get_settings().database_url


# ── Offline mode (generates SQL without connecting) ──────────────────────────
def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Render constraint names from our NAMING_CONVENTION
        render_as_batch=False,
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connects and runs migrations) ────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Include constraint names in generated SQL
        include_schemas=False,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine (required for asyncpg)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entrypoint ────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
