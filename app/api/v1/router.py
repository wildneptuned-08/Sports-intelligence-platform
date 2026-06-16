from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()

# ── Routes registered here per sprint ────────────────────────────────────────
# Sprint 4+: uncomment and implement each module
#
# from app.api.v1 import auth, matches, teams, players, leagues, predictions, users, admin
#
# api_router.include_router(auth.router,        prefix="/auth",        tags=["Auth"])
# api_router.include_router(matches.router,     prefix="/matches",     tags=["Matches"])
# api_router.include_router(teams.router,       prefix="/teams",       tags=["Teams"])
# api_router.include_router(players.router,     prefix="/players",     tags=["Players"])
# api_router.include_router(leagues.router,     prefix="/leagues",     tags=["Leagues"])
# api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
# api_router.include_router(users.router,       prefix="/users",       tags=["Users"])
# api_router.include_router(admin.router,       prefix="/admin",       tags=["Admin"])
