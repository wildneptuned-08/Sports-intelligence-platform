"""Add unique constraints to external_id fields and season.year

Revision ID: 002
Revises: 001
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op

revision: str = "002"
down_revision: str = "001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_unique_constraint("uq_leagues_external_id", "leagues", ["external_id"])
    op.create_unique_constraint("uq_teams_external_id", "teams", ["external_id"])
    op.create_unique_constraint("uq_venues_external_id", "venues", ["external_id"])
    op.create_unique_constraint("uq_players_external_id", "players", ["external_id"])
    op.create_unique_constraint("uq_seasons_year", "seasons", ["year"])


def downgrade() -> None:
    op.drop_constraint("uq_seasons_year", "seasons", type_="unique")
    op.drop_constraint("uq_players_external_id", "players", type_="unique")
    op.drop_constraint("uq_venues_external_id", "venues", type_="unique")
    op.drop_constraint("uq_teams_external_id", "teams", type_="unique")
    op.drop_constraint("uq_leagues_external_id", "leagues", type_="unique")
