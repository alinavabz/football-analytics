from datetime import UTC, datetime

import pytest

from football_analytics.config import MongoSettings
from football_analytics.ingest import event_doc, lineup_doc, load_season

NOW = datetime(2022, 12, 18, tzinfo=UTC)

# A tiny competition in StatsBomb's file layout: one match, two teams, two events.
FIXTURE = {
    "competitions.json": [
        {"competition_id": 1, "season_id": 2, "competition_name": "Test Cup"},
        {"competition_id": 1, "season_id": 3, "competition_name": "Test Cup"},
    ],
    "matches/1/2.json": [
        {
            "match_id": 100,
            "home_team": {"home_team_id": 10, "home_team_name": "Argentina"},
            "away_team": {"away_team_id": 20, "away_team_name": "France"},
            "home_score": 3,
            "away_score": 3,
        }
    ],
    "lineups/100.json": [
        {"team_id": 10, "team_name": "Argentina", "lineup": [{"player_id": 5503}]},
        {"team_id": 20, "team_name": "France", "lineup": [{"player_id": 3009}]},
    ],
    "events/100.json": [
        {"id": "e-1", "type": {"id": 30, "name": "Pass"}, "minute": 22},
        {
            "id": "e-2",
            "type": {"id": 16, "name": "Shot"},
            "minute": 23,
            "player": {"id": 5503, "name": "Lionel Messi"},
            "shot": {
                "outcome": {"name": "Goal"},
                "freeze_frame": [{"location": [118.0, 40.0], "teammate": False}],
            },
        },
    ],
}


def fake_fetch(path: str):
    return FIXTURE[path]


@pytest.fixture
def raw_db():
    settings = MongoSettings.from_env()
    client = settings.client()
    db = client["statsbomb_raw_test"]
    client.drop_database(db.name)
    yield db
    client.drop_database(db.name)
    client.close()


def test_event_doc_adds_match_id_and_keeps_nested_fields():
    event = FIXTURE["events/100.json"][1]
    doc = event_doc(event, 100, "events/100.json", NOW)

    assert doc["_id"] == "e-2"
    assert doc["match_id"] == 100
    assert doc["shot"] == event["shot"]
    assert doc["_ingest"]["source"].endswith("events/100.json")


def test_lineup_id_combines_match_and_team():
    doc = lineup_doc(FIXTURE["lineups/100.json"][0], 100, "lineups/100.json", NOW)
    assert doc["_id"] == "100-10"


def test_reload_does_not_duplicate(raw_db):
    load_season(raw_db, 1, 2, fake_fetch)
    first = {name: raw_db[name].count_documents({}) for name in raw_db.list_collection_names()}

    load_season(raw_db, 1, 2, fake_fetch)
    second = {name: raw_db[name].count_documents({}) for name in raw_db.list_collection_names()}

    assert first == {"competitions": 1, "matches": 1, "lineups": 2, "events": 2}
    assert second == first


def test_nested_structure_survives_the_round_trip(raw_db):
    load_season(raw_db, 1, 2, fake_fetch)

    shot = raw_db.events.find_one({"shot.outcome.name": "Goal"})
    assert shot["player"]["name"] == "Lionel Messi"
    assert shot["shot"]["freeze_frame"] == [{"location": [118.0, 40.0], "teammate": False}]


def test_unknown_season_fails_loudly(raw_db):
    with pytest.raises(ValueError, match="not found"):
        load_season(raw_db, 1, 999, fake_fetch)
