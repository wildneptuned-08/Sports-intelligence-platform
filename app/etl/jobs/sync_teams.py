from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone

from app.database import AsyncSessionLocal
from app.etl.fetchers.api_football import APIFootballClient
from app.etl.transformers.team_transformer import transform_team, transform_venue
from app.models.etl import ETLJobLog
from app.repositories.competition import LeagueRepository, LeagueSeasonRepository, SeasonRepository
from app.repositories.team import TeamRepository, VenueRepository

logger = logging.getLogger(__name__)

JOB_NAME = "sync_teams"


async def sync_teams() -> dict:
    started_at = datetime.now(timezone.utc)
    inserted = 0
    updated = 0
    errors = 0

    async with AsyncSessionLocal() as session:
        job_log = ETLJobLog(
            job_name=JOB_NAME,
            source="api-football",
            status="RUNNING",
            started_at=started_at,
        )
        session.add(job_log)
        await session.flush()

        try:
            client = APIFootballClient()
            league_repo = LeagueRepository(session)
            season_repo = SeasonRepository(session)
            team_repo = TeamRepository(session)
            venue_repo = VenueRepository(session)

            active_leagues = await league_repo.get_active()
            if not active_leagues:
                logger.warning("No active leagues found — skipping sync_teams")
                job_log.status = "SUCCESS"
                job_log.records_processed = 0
                await _finalize(job_log, started_at, session)
                return {"inserted": 0, "updated": 0, "errors": 0}

            for league in active_leagues:
                current_season = await _get_current_season(season_repo)
                if not current_season:
                    logger.warning("No current season found — skipping")
                    continue

                league_ext_id = int(league.external_id)
                raw_teams = await client.get_teams(league_ext_id, current_season.year)

                for raw in raw_teams:
                    try:
                        venue_data = transform_venue(raw)
                        venue = None
                        if venue_data:
                            ext_id = venue_data.pop("external_id")
                            venue, _ = await venue_repo.upsert(
                                external_id=ext_id, **venue_data
                            )

                        team_data = transform_team(raw)
                        ext_id = team_data.pop("external_id")
                        if venue:
                            team_data["home_venue_id"] = venue.id

                        if league.country_id:
                            team_data["country_id"] = league.country_id

                        team, created = await team_repo.upsert(
                            external_id=ext_id, **team_data
                        )
                        if created:
                            inserted += 1
                        else:
                            updated += 1

                    except Exception:
                        errors += 1
                        logger.exception("Error processing team entry")

            job_log.status = "SUCCESS"
            job_log.records_processed = inserted + updated
            job_log.records_failed = errors

        except Exception as exc:
            job_log.status = "FAILED"
            job_log.error_message = str(exc)
            job_log.error_traceback = traceback.format_exc()
            logger.exception("sync_teams failed")

        finally:
            await _finalize(job_log, started_at, session)

    metrics = {"inserted": inserted, "updated": updated, "errors": errors}
    logger.info("sync_teams completed", extra=metrics)
    return metrics


async def _get_current_season(season_repo: SeasonRepository):
    from sqlalchemy import select
    from app.models.competition import Season

    stmt = select(Season).where(Season.is_current.is_(True)).limit(1)
    result = await season_repo._session.execute(stmt)
    return result.scalar_one_or_none()


async def _finalize(job_log: ETLJobLog, started_at: datetime, session) -> None:
    job_log.finished_at = datetime.now(timezone.utc)
    job_log.duration_ms = (job_log.finished_at - started_at).total_seconds() * 1000
    await session.commit()
