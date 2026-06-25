from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.competition import League, Season


class ETLJobLog(Base):
    """Audit log for every ETL job execution — success or failure."""

    __tablename__ = "etl_job_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str | None] = mapped_column(String(50))
    league_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("leagues.id"))
    season_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("seasons.id"))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="RUNNING"
    )
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    # NUMERIC(12,3) — EXTRACT returns DOUBLE PRECISION, can be NULL while job runs
    duration_ms: Mapped[float | None] = mapped_column(Numeric(12, 3))
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    records_failed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text)
    error_traceback: Mapped[str | None] = mapped_column(Text)

    league: Mapped["League | None"] = relationship("League", back_populates="etl_job_logs")
    season: Mapped["Season | None"] = relationship("Season", back_populates="etl_job_logs")
