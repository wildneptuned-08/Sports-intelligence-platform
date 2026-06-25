from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer, String
from sqlalchemy import TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.etl import ETLJobLog
    from app.models.match import Match
    from app.models.player import Player, PlayerSeasonStats
    from app.models.team import Standing, Team, TeamLeagueSeason, Venue
    from app.models.user import UserFavoriteLeague


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    flag_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    leagues: Mapped[list["League"]] = relationship("League", back_populates="country")
    teams: Mapped[list["Team"]] = relationship("Team", back_populates="country")
    venues: Mapped[list["Venue"]] = relationship("Venue", back_populates="country")
    players: Mapped[list["Player"]] = relationship("Player", back_populates="nationality")


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    # Nullable: allows Champions League / UEFA (no single country)
    country_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("countries.id"))
    league_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="league"
    )
    logo_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    country: Mapped["Country | None"] = relationship("Country", back_populates="leagues")
    league_seasons: Mapped[list["LeagueSeason"]] = relationship(
        "LeagueSeason", back_populates="league"
    )
    user_favorites: Mapped[list["UserFavoriteLeague"]] = relationship(
        "UserFavoriteLeague", back_populates="league"
    )
    etl_job_logs: Mapped[list["ETLJobLog"]] = relationship(
        "ETLJobLog", back_populates="league"
    )


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(20), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    league_seasons: Mapped[list["LeagueSeason"]] = relationship(
        "LeagueSeason", back_populates="season"
    )
    etl_job_logs: Mapped[list["ETLJobLog"]] = relationship(
        "ETLJobLog", back_populates="season"
    )


class LeagueSeason(Base):
    __tablename__ = "league_seasons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("leagues.id"), nullable=False
    )
    season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("seasons.id"), nullable=False
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    total_rounds: Mapped[int | None] = mapped_column(Integer)
    current_round: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("league_id", "season_id"),)

    league: Mapped["League"] = relationship("League", back_populates="league_seasons")
    season: Mapped["Season"] = relationship("Season", back_populates="league_seasons")
    team_league_seasons: Mapped[list["TeamLeagueSeason"]] = relationship(
        "TeamLeagueSeason", back_populates="league_season"
    )
    standings: Mapped[list["Standing"]] = relationship(
        "Standing", back_populates="league_season"
    )
    matches: Mapped[list["Match"]] = relationship(
        "Match", back_populates="league_season"
    )
    player_season_stats: Mapped[list["PlayerSeasonStats"]] = relationship(
        "PlayerSeasonStats", back_populates="league_season"
    )
