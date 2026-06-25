from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import competitions, matches, teams

api_router = APIRouter()

# ── ETL validation endpoints (read-only) ─────────────────────────────────────
api_router.include_router(competitions.router, prefix="/competitions", tags=["Competitions"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(matches.router, prefix="/matches", tags=["Matches"])

# ── Future routes ────────────────────────────────────────────────────────────
# api_router.include_router(auth.router,        prefix="/auth",        tags=["Auth"])
# api_router.include_router(players.router,     prefix="/players",     tags=["Players"])
# api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
# api_router.include_router(users.router,       prefix="/users",       tags=["Users"])
# api_router.include_router(admin.router,       prefix="/admin",       tags=["Admin"])
