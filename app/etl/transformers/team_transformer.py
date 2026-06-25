from __future__ import annotations

from typing import Any

from app.core.slug import slugify


def transform_team(raw: dict[str, Any]) -> dict[str, Any]:
    team = raw["team"]
    return {
        "external_id": str(team["id"]),
        "name": team["name"],
        "short_name": team.get("code"),
        "slug": slugify(team["name"]),
        "logo_url": team.get("logo"),
        "founded_year": team.get("founded"),
    }


def transform_venue(raw: dict[str, Any]) -> dict[str, Any] | None:
    venue = raw.get("venue")
    if not venue or not venue.get("id"):
        return None
    return {
        "external_id": str(venue["id"]),
        "name": venue.get("name") or "Unknown",
        "city": venue.get("city"),
        "capacity": venue.get("capacity"),
        "surface": venue.get("surface"),
        "image_url": venue.get("image"),
    }
