from conftest import FIXTURE, fake_fetch

from football_analytics.ingest import load_season
from football_analytics.load_core import load_core, match_player_rows, pass_row


def _counts(conn):
    tables = ["competitions", "teams", "players", "matches", "match_players", "events", "shots",
              "passes"]  # fmt: skip
    return {t: conn.execute(f"SELECT count(*) FROM core.{t}").fetchone()[0] for t in tables}


def test_completed_pass_gets_explicit_outcome():
    event = {**FIXTURE["events/100.json"][0], "match_id": 100}
    assert pass_row(event)[-1] == "Complete"


def test_started_and_played_flags():
    lineup = {**FIXTURE["lineups/100.json"][0], "match_id": 100}
    rows = {row[1]: row for row in match_player_rows(lineup)}

    assert rows[5503][4:] == (True, True)  # started, played
    assert rows[6000][4:] == (False, False)  # unused substitute


def test_load_is_idempotent_and_reconciles(raw_db, pg_conn):
    load_season(raw_db, 1, 2, fake_fetch)

    with pg_conn.transaction():
        load_core(pg_conn, raw_db)
    first = _counts(pg_conn)

    with pg_conn.transaction():
        load_core(pg_conn, raw_db)

    assert first == {
        "competitions": 1,
        "teams": 2,
        "players": 4,  # three from lineups, one seen only in events
        "matches": 1,
        "match_players": 3,
        "events": 2,
        "shots": 1,
        "passes": 1,
    }
    assert _counts(pg_conn) == first


def test_shot_keeps_its_link_to_the_key_pass(raw_db, pg_conn):
    load_season(raw_db, 1, 2, fake_fetch)
    with pg_conn.transaction():
        load_core(pg_conn, raw_db)

    row = pg_conn.execute(
        "SELECT p.player_name, s.xg, kp.event_type FROM core.shots s "
        "JOIN core.events e USING (event_id) JOIN core.players p USING (player_id) "
        "JOIN core.events kp ON kp.event_id = s.key_pass_id"
    ).fetchone()
    assert row == ("Lionel Messi", 0.78, "Pass")
