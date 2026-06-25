from __future__ import annotations

from app.etl.transformers.competition_transformer import (
    transform_country,
    transform_league,
    transform_seasons,
)
from app.etl.transformers.match_transformer import transform_match
from app.etl.transformers.team_transformer import transform_team, transform_venue


class TestCompetitionTransformer:
    def test_transform_country(self) -> None:
        raw = {"name": "Spain", "code": "ES", "flag": "https://example.com/es.png"}
        result = transform_country(raw)
        assert result["name"] == "Spain"
        assert result["code"] == "ES"
        assert result["flag_url"] == "https://example.com/es.png"

    def test_transform_country_missing_code(self) -> None:
        raw = {"name": "Unknown", "code": None}
        result = transform_country(raw)
        assert result["code"] == "XX"

    def test_transform_league(self) -> None:
        raw = {
            "league": {
                "id": 140,
                "name": "La Liga",
                "type": "league",
                "logo": "https://example.com/laliga.png",
            }
        }
        result = transform_league(raw)
        assert result["external_id"] == "140"
        assert result["name"] == "La Liga"
        assert result["slug"] == "la-liga"
        assert result["league_type"] == "league"
        assert result["logo_url"] == "https://example.com/laliga.png"

    def test_transform_seasons(self) -> None:
        raw = {
            "seasons": [
                {"year": 2024, "current": True, "start": "2024-08-15", "end": "2025-05-25"},
                {"year": 2023, "current": False, "start": "2023-08-12", "end": "2024-05-26"},
            ]
        }
        result = transform_seasons(raw)
        assert len(result) == 2
        assert result[0]["year"] == 2024
        assert result[0]["label"] == "2024/2025"
        assert result[0]["is_current"] is True
        assert result[1]["is_current"] is False

    def test_transform_seasons_empty(self) -> None:
        result = transform_seasons({})
        assert result == []


class TestTeamTransformer:
    def test_transform_team(self) -> None:
        raw = {
            "team": {
                "id": 541,
                "name": "Real Madrid",
                "code": "RMA",
                "logo": "https://example.com/rma.png",
                "founded": 1902,
            }
        }
        result = transform_team(raw)
        assert result["external_id"] == "541"
        assert result["name"] == "Real Madrid"
        assert result["short_name"] == "RMA"
        assert result["slug"] == "real-madrid"
        assert result["founded_year"] == 1902

    def test_transform_venue(self) -> None:
        raw = {
            "venue": {
                "id": 1456,
                "name": "Santiago Bernabéu",
                "city": "Madrid",
                "capacity": 81044,
                "surface": "grass",
                "image": "https://example.com/bernabeu.png",
            }
        }
        result = transform_venue(raw)
        assert result is not None
        assert result["external_id"] == "1456"
        assert result["name"] == "Santiago Bernabéu"
        assert result["city"] == "Madrid"
        assert result["capacity"] == 81044

    def test_transform_venue_missing(self) -> None:
        raw = {"venue": None}
        assert transform_venue(raw) is None

    def test_transform_venue_no_id(self) -> None:
        raw = {"venue": {"id": None, "name": "Some Place"}}
        assert transform_venue(raw) is None


class TestMatchTransformer:
    def _fixture(self) -> dict:
        return {
            "fixture": {
                "id": 867946,
                "date": "2024-09-01T19:00:00+00:00",
                "referee": "Carlos del Cerro Grande",
                "status": {"short": "FT", "elapsed": 90},
                "venue": {"id": 1456},
            },
            "league": {"round": "Regular Season - 3"},
            "teams": {
                "home": {"id": 541, "name": "Real Madrid"},
                "away": {"id": 529, "name": "Barcelona"},
            },
            "goals": {"home": 2, "away": 1},
            "score": {
                "halftime": {"home": 1, "away": 0},
            },
        }

    def test_transform_match_basic(self) -> None:
        result = transform_match(self._fixture())
        assert result["external_id"] == "867946"
        assert result["home_team_external_id"] == "541"
        assert result["away_team_external_id"] == "529"
        assert result["status"] == "FINISHED"
        assert result["home_score"] == 2
        assert result["away_score"] == 1
        assert result["home_score_ht"] == 1
        assert result["away_score_ht"] == 0
        assert result["referee_name"] == "Carlos del Cerro Grande"
        assert result["round"] == "Regular Season - 3"
        assert result["venue_external_id"] == "1456"
        assert "real-madrid-vs-barcelona" in result["slug"]

    def test_transform_match_scheduled(self) -> None:
        fixture = self._fixture()
        fixture["fixture"]["status"]["short"] = "NS"
        fixture["goals"] = {"home": None, "away": None}
        result = transform_match(fixture)
        assert result["status"] == "SCHEDULED"
        assert result["home_score"] is None

    def test_transform_match_live(self) -> None:
        fixture = self._fixture()
        fixture["fixture"]["status"]["short"] = "2H"
        result = transform_match(fixture)
        assert result["status"] == "LIVE"

    def test_transform_match_no_venue(self) -> None:
        fixture = self._fixture()
        fixture["fixture"]["venue"] = {}
        result = transform_match(fixture)
        assert result["venue_external_id"] is None
