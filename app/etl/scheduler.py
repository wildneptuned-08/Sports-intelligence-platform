from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings

logger = logging.getLogger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    settings = get_settings()

    # ── ETL Jobs — registered but paused ─────────────────────────────────────
    # Set API_FOOTBALL_KEY and flip is_active on leagues to enable.
    # To activate: scheduler.resume_job("sync_competitions") etc.

    from app.etl.jobs.sync_competitions import sync_competitions
    from app.etl.jobs.sync_teams import sync_teams
    from app.etl.jobs.sync_matches import sync_matches

    scheduler.add_job(
        sync_competitions,
        trigger="cron",
        hour=2,
        minute=0,
        id="sync_competitions",
        replace_existing=True,
        max_instances=1,
        next_run_time=None,
    )

    scheduler.add_job(
        sync_teams,
        trigger="cron",
        hour=3,
        minute=0,
        id="sync_teams",
        replace_existing=True,
        max_instances=1,
        next_run_time=None,
    )

    scheduler.add_job(
        sync_matches,
        trigger="interval",
        hours=settings.etl_sync_fixtures_interval_hours,
        id="sync_matches",
        replace_existing=True,
        max_instances=1,
        next_run_time=None,
    )

    logger.info(
        "Scheduler configured — 3 ETL jobs registered (paused)",
        extra={"jobs": ["sync_competitions", "sync_teams", "sync_matches"]},
    )
    return scheduler
