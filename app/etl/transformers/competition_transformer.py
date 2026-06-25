from __future__ import annotations

from typing import Any

from app.core.slug import slugify


def transform_country(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": raw["name"],
        "code": raw.get("code") or "XX",
        "flag_url": raw.get("flag"),
    }


def transform_league(raw: dict[str, Any]) -> dict[str, Any]:
    league = raw["league"]
    return {
        "external_id": str(league["id"]),
        "name": league["name"],
        "slug": slugify(league["name"]),
        "league_type": league.get("type", "league"),
        "logo_url": league.get("logo"),
    }


def transform_seasons(raw: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for s in raw.get("seasons", []):
        results.append({
            "year": s["year"],
            "label": f"{s['year']}/{s['year'] + 1}",
            "is_current": s.get("current", False),
            "start_date": s.get("start"),
            "end_date": s.get("end"),
        })
    return results
