from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import TIMESTAMP, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.competition import Country, LeagueSeason
    from app.models.match import MatchEvent, MatchPlayerStats, Lineup
    from app.models.team import Team


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    nationality_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("countries.id")
    )
    position: Mapped[str | None] = mapped_column(String(50))
    height_cm: Mapped[int | None] = mapped_column(Integer)
    weight_kg: Mapped[int | None] = mapped_column(Integer)
    photo_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    nationality: Mapped["Country | None"] = relationship(
        "Country", back_populates="players"
    )
    contracts: Mapped[list["PlayerTeamContract"]] = relationship(
        "PlayerTeamContract", back_populates="player"
    )
    season_stats: Mapped[list["PlayerSeasonStats"]] = relationship(
        "PlayerSeasonStats", back_populates="player"
    )
    match_events: Mapped[list["MatchEvent"]] = relationship(
        "MatchEvent", back_populates="player", foreign_keys="MatchEvent.player_id"
    )
    match_stats: Mapped[list["MatchPlayerStats"]] = relationship(
        "MatchPlayerStats", back_populates="player"
    )
    lineups: Mapped[list["Lineup"]] = relationship("Lineup", back_populates="player")


class PlayerTeamContract(Base):
    __tablename__ = "player_team_contracts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.id"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id"), nullable=False
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    jersey_number: Mapped[int | None] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Partial unique index: each player can have at most one current contract
    __table_args__ = (
        Index(
            "uq_player_current_contract",
            "player_id",
            unique=True,
            postgresql_where=text("is_current = TRUE"),
        ),
    )

    player: Mapped["Player"] = relationship("Player", back_populates="contracts")
    team: Mapped["Team"] = relationship("Team", back_populates="player_contracts")


class PlayerSeasonStats(Base):
    __tablename__ = "player_season_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.id"), nullable=False
    )
    league_season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("league_seasons.id"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id"), nullable=False
    )
    appearances: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    minutes_played: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    goals: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    assists: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    yellow_cards: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    red_cards: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    rating_avg: Mapped[float | None] = mapped_column(Numeric(4, 2))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("player_id", "league_season_id", "team_id"),)

    player: Mapped["Player"] = relationship("Player", back_populates="season_stats")
    league_season: Mapped["LeagueSeason"] = relationship(
        "LeagueSeason", back_populates="player_season_stats"
    )
