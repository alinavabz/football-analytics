from datetime import UTC, datetime

import pytest
from conftest import FIXTURE, fake_fetch

from football_analytics.ingest import event_doc, lineup_doc, load_season

NOW = datetime(2022, 12, 18, tzinfo=UTC)


def test_event_doc_adds_match_id_and_keeps_nested_fields():
    event = FIXTURE["events/100.json"][1]
    doc = event_doc(event, 100, "events/100.json", NOW)

    assert doc["_id"] == event["id"]
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
