from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy import TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.competition import LeagueSeason
    from app.models.player import Player
    from app.models.prediction import Odds, Prediction
    from app.models.team import Team, Venue


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(50), unique=True)
    league_season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("league_seasons.id"), nullable=False
    )
    home_team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id"), nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id"), nullable=False
    )
    kickoff_utc: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    round: Mapped[str | None] = mapped_column(String(50))
    venue_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("venues.id"))
    referee_name: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="SCHEDULED"
    )
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    home_score_ht: Mapped[int | None] = mapped_column(Integer)
    away_score_ht: Mapped[int | None] = mapped_column(Integer)
    minutes_played: Mapped[int | None] = mapped_column(Integer)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="ck_matches_different_teams"),
    )

    league_season: Mapped["LeagueSeason"] = relationship(
        "LeagueSeason", back_populates="matches"
    )
    home_team: Mapped["Team"] = relationship(
        "Team", back_populates="home_matches", foreign_keys=[home_team_id]
    )
    away_team: Mapped["Team"] = relationship(
        "Team", back_populates="away_matches", foreign_keys=[away_team_id]
    )
    venue: Mapped["Venue | None"] = relationship("Venue", back_populates="matches")
    team_stats: Mapped[list["MatchTeamStats"]] = relationship(
        "MatchTeamStats", back_populates="match", cascade="all, delete-orphan"
    )
    events: Mapped[list["MatchEvent"]] = relationship(
        "MatchEvent", back_populates="match", cascade="all, delete-orphan"
    )
    player_stats: Mapped[list["MatchPlayerStats"]] = relationship(
        "MatchPlayerStats", back_populates="match", cascade="all, delete-orphan"
    )
    lineups: Mapped[list["Lineup"]] = relationship(
        "Lineup", back_populates="match", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="match"
    )
    odds: Mapped[list["Odds"]] = relationship("Odds", back_populates="match")


class MatchTeamStats(Base):
    __tablename__ = "match_team_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id"), nullable=False
    )
    is_home: Mapped[bool] = mapped_column(nullable=False)
    shots_total: Mapped[int | None] = mapped_column(Integer)
    shots_on_goal: Mapped[int | None] = mapped_column(Integer)
    possession_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    passes_total: Mapped[int | None] = mapped_column(Integer)
    passes_accuracy: Mapped[float | None] = mapped_column(Numeric(5, 2))
    fouls: Mapped[int | None] = mapped_column(Integer)
    corners: Mapped[int | None] = mapped_column(Integer)
    offsides: Mapped[int | None] = mapped_column(Integer)
    yellow_cards: Mapped[int | None] = mapped_column(Integer)
    red_cards: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("match_id", "team_id"),)

    match: Mapped["Match"] = relationship("Match", back_populates="team_stats")


class MatchEvent(Base):
    __tablename__ = "match_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id"), nullable=False
    )
    player_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("players.id"))
    assist_player_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("players.id")
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    minute: Mapped[int] = mapped_column(Integer, nullable=False)
    extra_minute: Mapped[int | None] = mapped_column(Integer)
    detail: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    match: Mapped["Match"] = relationship("Match", back_populates="events")
    player: Mapped["Player | None"] = relationship(
        "Player", back_populates="match_events", foreign_keys=[player_id]
    )


class MatchPlayerStats(Base):
    __tablename__ = "match_player_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.id"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id"), nullable=False
    )
    minutes_played: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[float | None] = mapped_column(Numeric(4, 2))
    goals: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    assists: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    shots_total: Mapped[int | None] = mapped_column(Integer)
    shots_on_goal: Mapped[int | None] = mapped_column(Integer)
    passes_total: Mapped[int | None] = mapped_column(Integer)
    key_passes: Mapped[int | None] = mapped_column(Integer)
    yellow_cards: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    red_cards: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    __table_args__ = (UniqueConstraint("match_id", "player_id"),)

    match: Mapped["Match"] = relationship("Match", back_populates="player_stats")
    player: Mapped["Player"] = relationship("Player", back_populates="match_stats")


class Lineup(Base):
    __tablename__ = "lineups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.id"), nullable=False
    )
    lineup_type: Mapped[str] = mapped_column(String(20), nullable=False)
    jersey_number: Mapped[int | None] = mapped_column(Integer)
    position_abbr: Mapped[str | None] = mapped_column(String(10))
    grid_position: Mapped[str | None] = mapped_column(String(10))

    __table_args__ = (UniqueConstraint("match_id", "team_id", "player_id"),)

    match: Mapped["Match"] = relationship("Match", back_populates="lineups")
    player: Mapped["Player"] = relationship("Player", back_populates="lineups")
