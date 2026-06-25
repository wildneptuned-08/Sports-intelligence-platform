from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy import TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.match import Match


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id"), nullable=False
    )
    model_version: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="poisson_v1"
    )
    generated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # 1X2 probabilities
    prob_home_win: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)
    prob_draw: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)
    prob_away_win: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)

    # Over/Under 2.5
    prob_over_2_5: Mapped[float | None] = mapped_column(Numeric(8, 6))
    prob_under_2_5: Mapped[float | None] = mapped_column(Numeric(8, 6))

    # BTTS
    prob_btts_yes: Mapped[float | None] = mapped_column(Numeric(8, 6))
    prob_btts_no: Mapped[float | None] = mapped_column(Numeric(8, 6))

    # Poisson model outputs
    expected_goals_home: Mapped[float | None] = mapped_column(Numeric(5, 2))
    expected_goals_away: Mapped[float | None] = mapped_column(Numeric(5, 2))
    most_likely_score: Mapped[str | None] = mapped_column(String(10))

    # Features snapshot for explainability and auditing
    features_snapshot: Mapped[dict | None] = mapped_column(JSONB)

    # Resolution (set after match finishes)
    actual_outcome: Mapped[str | None] = mapped_column(String(10))
    brier_score: Mapped[float | None] = mapped_column(Numeric(8, 6))

    __table_args__ = (
        # Only one prediction per model per match
        UniqueConstraint("match_id", "model_version"),
        # 1X2 calibration: probabilities must sum to 1.0 ± 0.0001
        CheckConstraint(
            "ABS(prob_home_win + prob_draw + prob_away_win - 1.0) < 0.0001",
            name="probs_1x2_sum_check",
        ),
    )

    match: Mapped["Match"] = relationship("Match", back_populates="predictions")


class Odds(Base):
    __tablename__ = "odds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id"), nullable=False
    )
    bookmaker: Mapped[str] = mapped_column(String(100), nullable=False)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    odd_value: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("match_id", "bookmaker", "market", "outcome", "captured_at"),
    )

    match: Mapped["Match"] = relationship("Match", back_populates="odds")
