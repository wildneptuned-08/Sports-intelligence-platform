"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2026-06-15 00:00:00.000000

Creates all tables defined in docs/DATABASE_DESIGN.md §4-10.
Uses Base.metadata.create_all() so the migration stays in sync with the models.
Future migrations should use alembic revision --autogenerate.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# Import all models to populate Base.metadata
from app.models.base import Base
import app.models  # noqa: F401

revision: str = "001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # Enable pg_trgm for trigram-based text search (teams, players)
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

    # Create all tables derived from the SQLAlchemy models
    # checkfirst=True skips tables that already exist (idempotent)
    Base.metadata.create_all(bind=conn, checkfirst=True)

    # Trigram indexes for text search (not expressible as standard SQLAlchemy Index)
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_teams_name_trgm "
        "ON teams USING gin (name gin_trgm_ops)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_players_name_trgm "
        "ON players USING gin (name gin_trgm_ops)"
    ))

    # Standard B-tree indexes for common query patterns
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_matches_kickoff_utc ON matches (kickoff_utc)",
        "CREATE INDEX IF NOT EXISTS idx_matches_status ON matches (status)",
        "CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches (home_team_id)",
        "CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches (away_team_id)",
        "CREATE INDEX IF NOT EXISTS idx_matches_league_season ON matches (league_season_id, kickoff_utc)",
        "CREATE INDEX IF NOT EXISTS idx_predictions_match_id ON predictions (match_id)",
        "CREATE INDEX IF NOT EXISTS idx_predictions_generated_at ON predictions (generated_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_standings_league_season ON standings (league_season_id, rank)",
        "CREATE INDEX IF NOT EXISTS idx_etl_job_logs_job_name ON etl_job_logs (job_name, started_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_etl_job_logs_status ON etl_job_logs (status)",
        "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens (user_id)",
    ]
    for ddl in indexes:
        conn.execute(sa.text(ddl))


def downgrade() -> None:
    conn = op.get_bind()

    # Drop all tables in reverse dependency order
    Base.metadata.drop_all(bind=conn)

    conn.execute(sa.text("DROP EXTENSION IF EXISTS pg_trgm"))
