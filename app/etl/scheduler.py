from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    """
    Create and configure the APScheduler instance.

    Jobs are registered here. In the bootstrap (Sprint 1) no jobs are active yet.
    Sprint 2+ will uncomment and implement each job below.
    """
    scheduler = AsyncIOScheduler(timezone="UTC")

    # ── ETL Jobs (Sprint 2+) ──────────────────────────────────────────────────
    # Uncomment when the job modules are implemented:
    #
    # from app.etl.jobs.sync_fixtures import sync_fixtures
    # from app.etl.jobs.sync_results import sync_results
    # from app.etl.jobs.sync_standings import sync_standings
    # from app.etl.jobs.generate_predictions import generate_predictions
    # from app.etl.jobs.cleanup import cleanup_old_tokens
    # from app.config import get_settings
    #
    # settings = get_settings()
    #
    # scheduler.add_job(
    #     sync_fixtures,
    #     trigger="interval",
    #     hours=settings.etl_sync_fixtures_interval_hours,
    #     id="sync_fixtures",
    #     replace_existing=True,
    #     max_instances=1,
    # )
    # scheduler.add_job(
    #     sync_results,
    #     trigger="interval",
    #     hours=settings.etl_sync_results_interval_hours,
    #     id="sync_results",
    #     replace_existing=True,
    #     max_instances=1,
    # )
    # scheduler.add_job(
    #     sync_standings,
    #     trigger="cron",
    #     hour=4,
    #     minute=0,
    #     id="sync_standings",
    #     replace_existing=True,
    # )
    # scheduler.add_job(
    #     generate_predictions,
    #     trigger="cron",
    #     hour=8,
    #     minute=0,
    #     id="generate_predictions",
    #     replace_existing=True,
    # )
    # scheduler.add_job(
    #     cleanup_old_tokens,
    #     trigger="cron",
    #     hour=3,
    #     minute=0,
    #     id="cleanup_tokens",
    #     replace_existing=True,
    # )

    logger.info("Scheduler configured — 0 jobs registered (ETL Sprint 2+)")
    return scheduler
