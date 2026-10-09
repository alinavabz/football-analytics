import pytest

from football_analytics.config import MongoSettings, PostgresSettings

# A tiny competition in StatsBomb's file layout: one match, two teams, a pass and a shot.
FIXTURE = {
    "competitions.json": [
        {
            "competition_id": 1,
            "season_id": 2,
            "competition_name": "Test Cup",
            "season_name": "2022",
        },
        {
            "competition_id": 1,
            "season_id": 3,
            "competition_name": "Test Cup",
            "season_name": "2026",
        },
    ],
    "matches/1/2.json": [
        {
            "match_id": 100,
            "match_date": "2022-12-18",
            "kick_off": "17:00:00.000",
            "competition": {"competition_id": 1, "competition_name": "Test Cup"},
            "season": {"season_id": 2, "season_name": "2022"},
            "competition_stage": {"id": 26, "name": "Final"},
            "home_team": {"home_team_id": 10, "home_team_name": "Argentina"},
            "away_team": {"away_team_id": 20, "away_team_name": "France"},
            "home_score": 3,
            "away_score": 3,
        }
    ],
    "lineups/100.json": [
        {
            "team_id": 10,
            "team_name": "Argentina",
            "lineup": [
                {
                    "player_id": 5503,
                    "player_name": "Lionel Messi",
                    "jersey_number": 10,
                    "positions": [{"position": "Right Wing", "start_reason": "Starting XI"}],
                },
                {
                    "player_id": 6000,
                    "player_name": "Unused Sub",
                    "jersey_number": 22,
                    "positions": [],
                },
            ],
        },
        {
            "team_id": 20,
            "team_name": "France",
            "lineup": [
                {
                    "player_id": 3009,
                    "player_name": "Kylian Mbappé",
                    "jersey_number": 10,
                    "positions": [{"position": "Left Wing", "start_reason": "Starting XI"}],
                }
            ],
        },
    ],
    "events/100.json": [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "index": 1,
            "period": 1,
            "minute": 22,
            "second": 10,
            "type": {"id": 30, "name": "Pass"},
            "team": {"id": 10, "name": "Argentina"},
            "player": {"id": 6100, "name": "Not In Lineup"},
            "location": [60.0, 40.0],
            "pass": {"recipient": {"id": 5503, "name": "Lionel Messi"}, "length": 30.5},
        },
        {
            "id": "00000000-0000-0000-0000-000000000002",
            "index": 2,
            "period": 1,
            "minute": 23,
            "second": 0,
            "type": {"id": 16, "name": "Shot"},
            "team": {"id": 10, "name": "Argentina"},
            "player": {"id": 5503, "name": "Lionel Messi"},
            "location": [108.0, 40.0],
            "shot": {
                "statsbomb_xg": 0.78,
                "outcome": {"name": "Goal"},
                "body_part": {"name": "Left Foot"},
                "key_pass_id": "00000000-0000-0000-0000-000000000001",
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


@pytest.fixture
def pg_conn():
    """A connection to a throwaway database, dropped after the test."""
    settings = PostgresSettings.from_env()
    name = "football_test"
    with settings.connect(autocommit=True) as admin:
        admin.execute(f"DROP DATABASE IF EXISTS {name}")
        admin.execute(f"CREATE DATABASE {name}")
    conn = settings.connect(dbname=name)
    yield conn
    conn.close()
    with settings.connect(autocommit=True) as admin:
        admin.execute(f"DROP DATABASE IF EXISTS {name}")
