"""
Import all models here so SQLAlchemy's Base.metadata is populated
when any code imports `app.models`.

This is required by:
  - Alembic autogenerate (reads Base.metadata)
  - Tests that call Base.metadata.create_all()
  - Relationship resolution (SQLAlchemy mapper configuration)
"""
from app.models.competition import Country, League, LeagueSeason, Season  # noqa: F401
from app.models.etl import ETLJobLog  # noqa: F401
from app.models.match import Lineup, Match, MatchEvent, MatchPlayerStats, MatchTeamStats  # noqa: F401
from app.models.player import Player, PlayerSeasonStats, PlayerTeamContract  # noqa: F401
from app.models.prediction import Odds, Prediction  # noqa: F401
from app.models.team import Standing, Team, TeamAlias, TeamLeagueSeason, Venue  # noqa: F401
from app.models.user import RefreshToken, User, UserFavoriteLeague, UserFavoriteTeam  # noqa: F401

__all__ = [
    # competition
    "Country", "League", "Season", "LeagueSeason",
    # team
    "Venue", "Team", "TeamAlias", "TeamLeagueSeason", "Standing",
    # player
    "Player", "PlayerTeamContract", "PlayerSeasonStats",
    # match
    "Match", "MatchTeamStats", "MatchEvent", "MatchPlayerStats", "Lineup",
    # prediction
    "Prediction", "Odds",
    # user
    "User", "RefreshToken", "UserFavoriteTeam", "UserFavoriteLeague",
    # etl
    "ETLJobLog",
]
