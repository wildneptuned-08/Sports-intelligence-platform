from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone

from app.database import AsyncSessionLocal
from app.etl.fetchers.api_football import APIFootballClient
from app.etl.transformers.competition_transformer import (
    transform_country,
    transform_league,
    transform_seasons,
)
from app.models.etl import ETLJobLog
from app.repositories.competition import (
    CountryRepository,
    LeagueRepository,
    LeagueSeasonRepository,
    SeasonRepository,
)

logger = logging.getLogger(__name__)

JOB_NAME = "sync_competitions"


async def sync_competitions() -> dict:
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
            raw_leagues = await client.get_leagues()

            country_repo = CountryRepository(session)
            league_repo = LeagueRepository(session)
            season_repo = SeasonRepository(session)
            ls_repo = LeagueSeasonRepository(session)

            for raw in raw_leagues:
                try:
                    country_data = transform_country(raw.get("country", {}))
                    country, country_created = await country_repo.upsert_by_code(
                        code=country_data.pop("code"), **country_data
                    )
                    if country_created:
                        inserted += 1

                    league_data = transform_league(raw)
                    league_data["country_id"] = country.id
                    ext_id = league_data.pop("external_id")
                    league, league_created = await league_repo.upsert(
                        external_id=ext_id, **league_data
                    )
                    if league_created:
                        inserted += 1
                    else:
                        updated += 1

                    for season_data in transform_seasons(raw):
                        start_date = season_data.pop("start_date", None)
                        end_date = season_data.pop("end_date", None)
                        is_current = season_data.pop("is_current", False)

                        season, _ = await season_repo.get_or_create(season_data["year"])

                        if is_current and not season.is_current:
                            await season_repo.update(season, is_current=True)

                        await ls_repo.get_or_create(
                            league_id=league.id,
                            season_id=season.id,
                            start_date=start_date,
                            end_date=end_date,
                            is_current=is_current,
                        )

                except Exception:
                    errors += 1
                    logger.exception("Error processing league entry")

            job_log.status = "SUCCESS"
            job_log.records_processed = inserted + updated
            job_log.records_failed = errors

        except Exception as exc:
            job_log.status = "FAILED"
            job_log.error_message = str(exc)
            job_log.error_traceback = traceback.format_exc()
            logger.exception("sync_competitions failed")

        finally:
            job_log.finished_at = datetime.now(timezone.utc)
            duration = (job_log.finished_at - started_at).total_seconds() * 1000
            job_log.duration_ms = duration
            await session.commit()

    metrics = {"inserted": inserted, "updated": updated, "errors": errors}
    logger.info("sync_competitions completed", extra=metrics)
    return metrics
