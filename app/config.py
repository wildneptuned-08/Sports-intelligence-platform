from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    environment: Environment = Environment.DEVELOPMENT
    secret_key: str = ""
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = ""

    # ── JWT ──────────────────────────────────────────────────────────────────
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ── External APIs ─────────────────────────────────────────────────────────
    api_football_key: str = ""
    api_football_base_url: str = "https://v3.football.api-sports.io"
    football_data_key: str = ""
    the_odds_api_key: str = ""

    # ── ETL Scheduler ─────────────────────────────────────────────────────────
    etl_sync_fixtures_interval_hours: int = 6
    etl_sync_results_interval_hours: int = 1
    etl_enabled_leagues: list[str] = ["la-liga", "premier-league"]

    # ── Observability ─────────────────────────────────────────────────────────
    sentry_dsn: str = ""

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ── Server ────────────────────────────────────────────────────────────────
    port: int = 8000

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("etl_enabled_leagues", "allowed_origins", mode="before")
    @classmethod
    def parse_comma_separated(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> Settings:
        if self.environment == Environment.PRODUCTION:
            if not self.secret_key or self.secret_key == "change-me-in-production":
                raise ValueError(
                    "SECRET_KEY must be set to a secure random value in production"
                )
            if len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
            if not self.database_url:
                raise ValueError("DATABASE_URL must be set in production")
            if "localhost" in self.database_url or "postgres:5432" in self.database_url:
                raise ValueError(
                    "DATABASE_URL appears to use a local/Docker address in production"
                )
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def show_docs(self) -> bool:
        return self.environment != Environment.PRODUCTION

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
