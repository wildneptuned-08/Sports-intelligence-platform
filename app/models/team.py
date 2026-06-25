from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Computed, ForeignKey, Integer, String
from sqlalchemy import TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.competition import Country, LeagueSeason
    from app.models.match import Match
    from app.models.player import Player, PlayerTeamContract
    from app.models.user import UserFavoriteTeam


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100))
    country_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("countries.id"))
    capacity: Mapped[int | None] = mapped_column(Integer)
    surface: Mapped[str | None] = mapped_column(String(50))
    image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    country: Mapped["Country | None"] = relationship("Country", back_populates="venues")
    home_teams: Mapped[list["Team"]] = relationship("Team", back_populates="home_venue")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="venue")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(50))
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    country_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("countries.id"))
    home_venue_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("venues.id")
    )
    logo_url: Mapped[str | None] = mapped_column(String(500))
    founded_year: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    country: Mapped["Country | None"] = relationship("Country", back_populates="teams")
    home_venue: Mapped["Venue | None"] = relationship("Venue", back_populates="home_teams")
    aliases: Mapped[list["TeamAlias"]] = relationship(
        "TeamAlias", back_populates="team", cascade="all, delete-orphan"
    )
    team_league_seasons: Mapped[list["TeamLeagueSeason"]] = relationship(
        "TeamLeagueSeason", back_populates="team"
    )
    standings: Mapped[list["Standing"]] = relationship("Standing", back_populates="team")
    player_contracts: Mapped[list["PlayerTeamContract"]] = relationship(
        "PlayerTeamContract", back_populates="team"
    )
    home_matches: Mapped[list["Match"]] = relationship(
        "Match", back_populates="home_team", foreign_keys="Match.home_team_id"
    )
    away_matches: Mapped[list["Match"]] = relationship(
        "Match", back_populates="away_team", foreign_keys="Match.away_team_id"
    )
    user_favorites: Mapped[list["UserFavoriteTeam"]] = relationship(
        "UserFavoriteTeam", back_populates="team"
    )


class TeamAlias(Base):
    """Alternative names for teams — used by the ETL normalizer to map sources."""

    __tablename__ = "team_aliases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    alias: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (UniqueConstraint("alias", "source"),)

    team: Mapped["Team"] = relationship("Team", back_populates="aliases")


class TeamLeagueSeason(Base):
    __tablename__ = "team_league_seasons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id"), nullable=False
    )
    league_season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("league_seasons.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("team_id", "league_season_id"),)

    team: Mapped["Team"] = relationship("Team", back_populates="team_league_seasons")
    league_season: Mapped["LeagueSeason"] = relationship(
        "LeagueSeason", back_populates="team_league_seasons"
    )


class Standing(Base):
    __tablename__ = "standings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    league_season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("league_seasons.id"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    played: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    won: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    drawn: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    lost: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    goals_for: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    goals_against: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # GENERATED ALWAYS AS (goals_for - goals_against) STORED
    goal_diff: Mapped[int | None] = mapped_column(
        Integer, Computed("goals_for - goals_against", persisted=True)
    )
    form: Mapped[str | None] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("league_season_id", "team_id"),)

    league_season: Mapped["LeagueSeason"] = relationship(
        "LeagueSeason", back_populates="standings"
    )
    team: Mapped["Team"] = relationship("Team", back_populates="standings")
