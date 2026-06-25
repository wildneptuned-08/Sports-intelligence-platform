from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.slug import slugify


def transform_match(raw: dict[str, Any]) -> dict[str, Any]:
    fixture = raw["fixture"]
    teams = raw["teams"]
    goals = raw["goals"]
    score = raw.get("score", {})

    status_map = {
        "TBD": "SCHEDULED",
        "NS": "SCHEDULED",
        "1H": "LIVE",
        "HT": "LIVE",
        "2H": "LIVE",
        "ET": "LIVE",
        "P": "LIVE",
        "FT": "FINISHED",
        "AET": "FINISHED",
        "PEN": "FINISHED",
        "BT": "LIVE",
        "SUSP": "SUSPENDED",
        "INT": "INTERRUPTED",
        "PST": "POSTPONED",
        "CANC": "CANCELLED",
        "ABD": "ABANDONED",
        "AWD": "FINISHED",
        "WO": "FINISHED",
        "LIVE": "LIVE",
    }
    api_status = fixture.get("status", {}).get("short", "NS")

    kickoff = fixture.get("date")
    if isinstance(kickoff, str):
        kickoff = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))

    home_name = teams["home"]["name"]
    away_name = teams["away"]["name"]
    date_str = kickoff.strftime("%Y-%m-%d") if isinstance(kickoff, datetime) else "unknown"
    match_slug = slugify(f"{home_name}-vs-{away_name}-{date_str}")

    halftime = score.get("halftime", {})

    return {
        "external_id": str(fixture["id"]),
        "home_team_external_id": str(teams["home"]["id"]),
        "away_team_external_id": str(teams["away"]["id"]),
        "kickoff_utc": kickoff,
        "round": raw.get("league", {}).get("round"),
        "referee_name": fixture.get("referee"),
        "venue_external_id": str(fixture["venue"]["id"]) if fixture.get("venue", {}).get("id") else None,
        "status": status_map.get(api_status, "SCHEDULED"),
        "home_score": goals.get("home"),
        "away_score": goals.get("away"),
        "home_score_ht": halftime.get("home"),
        "away_score_ht": halftime.get("away"),
        "minutes_played": fixture.get("status", {}).get("elapsed"),
        "slug": match_slug,
    }
