from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.etl.fetchers.api_football import APIFootballClient
from app.etl.transformers.match_transformer import transform_match
from app.models.competition import Season
from app.models.etl import ETLJobLog
from app.repositories.competition import LeagueRepository, LeagueSeasonRepository
from app.repositories.match import MatchRepository
from app.repositories.team import TeamRepository

logger = logging.getLogger(__name__)

JOB_NAME = "sync_matches"


async def sync_matches() -> dict:
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
            ls_repo = LeagueSeasonRepository(session)
            team_repo = TeamRepository(session)
            match_repo = MatchRepository(session)

            active_leagues = await league_repo.get_active()
            if not active_leagues:
                logger.warning("No active leagues — skipping sync_matches")
                job_log.status = "SUCCESS"
                await _finalize(job_log, started_at, session)
                return {"inserted": 0, "updated": 0, "errors": 0}

            current_season = await _get_current_season(session)
            if not current_season:
                logger.warning("No current season — skipping sync_matches")
                job_log.status = "SUCCESS"
                await _finalize(job_log, started_at, session)
                return {"inserted": 0, "updated": 0, "errors": 0}

            for league in active_leagues:
                league_ext_id = int(league.external_id)
                raw_fixtures = await client.get_fixtures(league_ext_id, current_season.year)

                league_season = await ls_repo.get_by_league_and_season(
                    league.id, current_season.id
                )
                if not league_season:
                    league_season, _ = await ls_repo.get_or_create(
                        league_id=league.id, season_id=current_season.id
                    )

                for raw in raw_fixtures:
                    try:
                        match_data = transform_match(raw)

                        home_ext = match_data.pop("home_team_external_id")
                        away_ext = match_data.pop("away_team_external_id")
                        venue_ext = match_data.pop("venue_external_id", None)

                        home_team = await team_repo.get_by_external_id(home_ext)
                        away_team = await team_repo.get_by_external_id(away_ext)

                        if not home_team or not away_team:
                            errors += 1
                            logger.warning(
                                "Team not found for match",
                                extra={"home_ext": home_ext, "away_ext": away_ext},
                            )
                            continue

                        match_data["league_season_id"] = league_season.id
                        match_data["home_team_id"] = home_team.id
                        match_data["away_team_id"] = away_team.id

                        if venue_ext:
                            from app.repositories.team import VenueRepository
                            venue_repo = VenueRepository(session)
                            venue = await venue_repo.get_by_external_id(venue_ext)
                            if venue:
                                match_data["venue_id"] = venue.id

                        ext_id = match_data.pop("external_id")
                        match, created = await match_repo.upsert(
                            external_id=ext_id, **match_data
                        )
                        if created:
                            inserted += 1
                        else:
                            updated += 1

                    except Exception:
                        errors += 1
                        logger.exception("Error processing fixture")

            job_log.status = "SUCCESS"
            job_log.records_processed = inserted + updated
            job_log.records_failed = errors

        except Exception as exc:
            job_log.status = "FAILED"
            job_log.error_message = str(exc)
            job_log.error_traceback = traceback.format_exc()
            logger.exception("sync_matches failed")

        finally:
            await _finalize(job_log, started_at, session)

    metrics = {"inserted": inserted, "updated": updated, "errors": errors}
    logger.info("sync_matches completed", extra=metrics)
    return metrics


async def _get_current_season(session):
    stmt = select(Season).where(Season.is_current.is_(True)).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _finalize(job_log: ETLJobLog, started_at: datetime, session) -> None:
    job_log.finished_at = datetime.now(timezone.utc)
    job_log.duration_ms = (job_log.finished_at - started_at).total_seconds() * 1000
    await session.commit()
