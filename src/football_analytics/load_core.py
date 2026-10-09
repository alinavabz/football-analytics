"""Load the relational model in PostgreSQL (schema `core`) from the MongoDB raw store.

The whole load runs in one transaction: either every table is updated or none is. Each table is
copied into a temporary staging table and merged with INSERT ... ON CONFLICT DO UPDATE, so a
rerun updates rows in place and never duplicates them. Row counts are reconciled against MongoDB
before the transaction commits.
"""

import argparse
import logging
import time
from collections.abc import Iterable, Iterator
from pathlib import Path

import psycopg
from psycopg import sql
from pymongo.database import Database

from football_analytics.config import MongoSettings, PostgresSettings

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"
EVENT_BATCH_SIZE = 20_000

log = logging.getLogger("football_analytics.load_core")

# Column order for each table, and its primary key. Rows are tuples in this order.
TABLES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "competitions": (
        (
            "competition_id",
            "season_id",
            "competition_name",
            "season_name",
            "country_name",
            "competition_gender",
        ),
        ("competition_id", "season_id"),
    ),
    "teams": (("team_id", "team_name", "country_name"), ("team_id",)),
    "players": (("player_id", "player_name", "player_nickname", "country_name"), ("player_id",)),
    "matches": (
        (
            "match_id",
            "competition_id",
            "season_id",
            "match_date",
            "kick_off",
            "competition_stage",
            "match_week",
            "home_team_id",
            "away_team_id",
            "home_score",
            "away_score",
            "stadium_name",
            "referee_name",
        ),
        ("match_id",),
    ),
    "match_players": (
        ("match_id", "player_id", "team_id", "jersey_number", "started", "played"),
        ("match_id", "player_id"),
    ),
    "events": (
        (
            "event_id",
            "match_id",
            "event_index",
            "period",
            "minute",
            "second",
            "event_type",
            "team_id",
            "player_id",
            "position_name",
            "play_pattern",
            "possession",
            "location_x",
            "location_y",
            "duration",
            "under_pressure",
        ),
        ("event_id",),
    ),
    "shots": (
        (
            "event_id",
            "xg",
            "outcome",
            "body_part",
            "technique",
            "shot_type",
            "end_x",
            "end_y",
            "end_z",
            "first_time",
            "key_pass_id",
        ),
        ("event_id",),
    ),
    "passes": (
        (
            "event_id",
            "recipient_player_id",
            "length",
            "angle",
            "height",
            "body_part",
            "pass_type",
            "end_x",
            "end_y",
            "is_cross",
            "outcome",
        ),
        ("event_id",),
    ),
}


def _name(obj: dict | None) -> str | None:
    """StatsBomb nests labels as {"id": ..., "name": ...}; return the name or None."""
    return obj["name"] if obj else None


def _coord(values: list | None, i: int) -> float | None:
    return values[i] if values and len(values) > i else None


# ---- transforms: one raw document in, one or more rows out -------------------------------------


def competition_row(c: dict) -> tuple:
    return (
        c["competition_id"], c["season_id"], c["competition_name"], c["season_name"],
        c.get("country_name"), c.get("competition_gender"),
    )  # fmt: skip


def team_rows(match: dict) -> list[tuple]:
    home, away = match["home_team"], match["away_team"]
    return [
        (home["home_team_id"], home["home_team_name"], _name(home.get("country"))),
        (away["away_team_id"], away["away_team_name"], _name(away.get("country"))),
    ]


def match_row(m: dict) -> tuple:
    return (
        m["match_id"], m["competition"]["competition_id"], m["season"]["season_id"],
        m["match_date"], m.get("kick_off"), m["competition_stage"]["name"], m.get("match_week"),
        m["home_team"]["home_team_id"], m["away_team"]["away_team_id"], m["home_score"],
        m["away_score"], _name(m.get("stadium")), _name(m.get("referee")),
    )  # fmt: skip


def player_rows(lineup: dict) -> list[tuple]:
    return [
        (p["player_id"], p["player_name"], p.get("player_nickname"), _name(p.get("country")))
        for p in lineup["lineup"]
    ]


def match_player_rows(lineup: dict) -> list[tuple]:
    rows = []
    for p in lineup["lineup"]:
        positions = p.get("positions") or []
        started = any(pos.get("start_reason") == "Starting XI" for pos in positions)
        rows.append(
            (lineup["match_id"], p["player_id"], lineup["team_id"], p.get("jersey_number"),
             started, bool(positions))
        )  # fmt: skip
    return rows


def event_row(e: dict) -> tuple:
    player = e.get("player")
    return (
        e["id"], e["match_id"], e["index"], e["period"], e["minute"], e["second"],
        e["type"]["name"], e["team"]["id"], player["id"] if player else None,
        _name(e.get("position")), _name(e.get("play_pattern")), e.get("possession"),
        _coord(e.get("location"), 0), _coord(e.get("location"), 1), e.get("duration"),
        bool(e.get("under_pressure")),
    )  # fmt: skip


def shot_row(e: dict) -> tuple:
    s = e["shot"]
    end = s.get("end_location")
    return (
        e["id"], s["statsbomb_xg"], s["outcome"]["name"], _name(s.get("body_part")),
        _name(s.get("technique")), _name(s.get("type")), _coord(end, 0), _coord(end, 1),
        _coord(end, 2), bool(s.get("first_time")), s.get("key_pass_id"),
    )  # fmt: skip


def pass_row(e: dict) -> tuple:
    p = e["pass"]
    end = p.get("end_location")
    recipient = p.get("recipient")
    return (
        e["id"], recipient["id"] if recipient else None, p.get("length"), p.get("angle"),
        _name(p.get("height")), _name(p.get("body_part")), _name(p.get("type")),
        _coord(end, 0), _coord(end, 1), bool(p.get("cross")),
        _name(p.get("outcome")) or "Complete",
    )  # fmt: skip


def event_player_rows(e: dict) -> list[tuple]:
    """Players referenced by an event, so foreign keys hold even if a lineup omits someone."""
    rows = []
    if e.get("player"):
        rows.append((e["player"]["id"], e["player"]["name"], None, None))
    recipient = e.get("pass", {}).get("recipient")
    if recipient:
        rows.append((recipient["id"], recipient["name"], None, None))
    return rows


# ---- loading ------------------------------------------------------------------------------------


def apply_schema(conn: psycopg.Connection) -> None:
    """Apply the numbered SQL files (001_..., 002_...) in order. Each is safe to re-run."""
    for path in sorted(SQL_DIR.glob("[0-9][0-9][0-9]_*.sql")):
        conn.execute(path.read_text())


def upsert_rows(
    conn: psycopg.Connection, table: str, rows: Iterable[tuple], update: bool = True
) -> int:
    """Copy rows into a staging table, then merge them into core.<table> by primary key.

    With update=False, rows whose key already exists are left untouched (ON CONFLICT DO NOTHING).
    """
    columns, key = TABLES[table]
    stage = sql.Identifier(f"stage_{table}")
    target = sql.Identifier("core", table)
    cols = sql.SQL(", ").join(map(sql.Identifier, columns))
    updates = sql.SQL(", ").join(
        sql.SQL("{c} = EXCLUDED.{c}").format(c=sql.Identifier(c)) for c in columns if c not in key
    )

    conn.execute(sql.SQL("CREATE TEMP TABLE {s} (LIKE {t})").format(s=stage, t=target))
    count = 0
    with conn.cursor().copy(sql.SQL("COPY {s} ({c}) FROM STDIN").format(s=stage, c=cols)) as copy:
        for row in rows:
            copy.write_row(row)
            count += 1
    on_conflict = (
        sql.SQL("DO UPDATE SET {u}").format(u=updates) if update else sql.SQL("DO NOTHING")
    )
    conn.execute(
        sql.SQL(
            "INSERT INTO {t} ({c}) SELECT DISTINCT ON ({k}) {c} FROM {s} ON CONFLICT ({k}) {o}"
        ).format(
            t=target,
            c=cols,
            s=stage,
            k=sql.SQL(", ").join(map(sql.Identifier, key)),
            o=on_conflict,
        )
    )
    conn.execute(sql.SQL("DROP TABLE {s}").format(s=stage))
    return count


def _batched(items: Iterable[dict], size: int) -> Iterator[list[dict]]:
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def load_core(conn: psycopg.Connection, raw: Database) -> dict[str, int]:
    """Load every core table from the raw store. Caller owns the transaction."""
    apply_schema(conn)

    upsert_rows(conn, "competitions", map(competition_row, raw.competitions.find()))

    matches = list(raw.matches.find())
    lineups = list(raw.lineups.find())
    upsert_rows(conn, "teams", (row for m in matches for row in team_rows(m)))
    upsert_rows(conn, "players", (row for lu in lineups for row in player_rows(lu)))
    upsert_rows(conn, "matches", map(match_row, matches))
    upsert_rows(conn, "match_players", (row for lu in lineups for row in match_player_rows(lu)))

    # Events are streamed in batches so the full event set is never held in memory.
    projection = {"_ingest": 0, "related_events": 0, "shot.freeze_frame": 0, "tactics": 0}
    cursor = raw.events.find({}, projection).sort("match_id", 1)
    for batch in _batched(cursor, EVENT_BATCH_SIZE):
        # Lineups are the authoritative player source; events only fill in anyone missing.
        upsert_rows(
            conn, "players", (row for e in batch for row in event_player_rows(e)), update=False
        )
        upsert_rows(conn, "events", map(event_row, batch))
        upsert_rows(conn, "shots", (shot_row(e) for e in batch if e["type"]["name"] == "Shot"))
        upsert_rows(conn, "passes", (pass_row(e) for e in batch if e["type"]["name"] == "Pass"))

    return reconcile(conn, raw)


def reconcile(conn: psycopg.Connection, raw: Database) -> dict[str, int]:
    """Compare row counts with the raw store. Raises if anything is missing or extra."""
    lineup_players = next(
        raw.lineups.aggregate([{"$group": {"_id": None, "n": {"$sum": {"$size": "$lineup"}}}}]),
        {"n": 0},
    )["n"]
    expected = {
        "matches": raw.matches.count_documents({}),
        "match_players": lineup_players,
        "events": raw.events.count_documents({}),
        "shots": raw.events.count_documents({"type.name": "Shot"}),
        "passes": raw.events.count_documents({"type.name": "Pass"}),
    }
    actual = {
        table: conn.execute(
            sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier("core", table))
        ).fetchone()[0]
        for table in expected
    }
    if actual != expected:
        raise RuntimeError(f"reconciliation failed: postgres {actual} != mongodb {expected}")
    return actual


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    mongo = MongoSettings.from_env()
    mongo_client = mongo.client()
    started = time.perf_counter()
    try:
        with PostgresSettings.from_env().connect() as conn, conn.transaction():
            counts = load_core(conn, mongo_client[mongo.database])
    finally:
        mongo_client.close()

    log.info("done in %.1fs", time.perf_counter() - started)
    log.info("rows in core, reconciled with mongodb: %s", counts)


if __name__ == "__main__":
    main()
