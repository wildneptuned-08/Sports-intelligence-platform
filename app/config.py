from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    environment: str = "development"
    secret_key: str = "change-me-in-production-generate-with-secrets-token-hex-32"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://sip:sip_password@postgres:5432/sip_db"

    # ── JWT ──────────────────────────────────────────────────────────────────
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ── External APIs ─────────────────────────────────────────────────────────
    api_football_key: str = ""
    api_football_base_url: str = "https://v3.football.api-sports.io"
    football_data_key: str = ""
    the_odds_api_key: str = ""

    # ── ETL Scheduler (Sprint 2+) ─────────────────────────────────────────────
    etl_sync_fixtures_interval_hours: int = 6
    etl_sync_results_interval_hours: int = 1
    etl_enabled_leagues: list[str] = ["la-liga", "premier-league"]

    # ── Observability ─────────────────────────────────────────────────────────
    sentry_dsn: str = ""

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Phase 2: add your Netlify domain here
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("etl_enabled_leagues", "allowed_origins", mode="before")
    @classmethod
    def parse_comma_separated(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
