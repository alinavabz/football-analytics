"""Load one StatsBomb competition season into MongoDB as raw documents.

Documents are stored as delivered. Two additions only:
- `match_id` on events and lineups, because those files identify their match only by file name.
- `_ingest`, recording the source file and load time.

Every document's `_id` is derived from StatsBomb's own identifiers and written with an upsert,
so reloading the same season replaces documents instead of duplicating them.
"""

import argparse
import logging
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pymongo import ReplaceOne
from pymongo.collection import Collection
from pymongo.database import Database

from football_analytics.config import MongoSettings
from football_analytics.statsbomb import StatsBombClient

Fetch = Callable[[str], Any]

log = logging.getLogger("football_analytics.ingest")


def _ingest_meta(source: str, ingested_at: datetime) -> dict:
    return {"source": f"statsbomb/open-data/data/{source}", "ingested_at": ingested_at}


def competition_doc(competition: dict, source: str, ingested_at: datetime) -> dict:
    key = f"{competition['competition_id']}-{competition['season_id']}"
    return {"_id": key, **competition, "_ingest": _ingest_meta(source, ingested_at)}


def match_doc(match: dict, source: str, ingested_at: datetime) -> dict:
    return {"_id": match["match_id"], **match, "_ingest": _ingest_meta(source, ingested_at)}


def lineup_doc(team_lineup: dict, match_id: int, source: str, ingested_at: datetime) -> dict:
    return {
        "_id": f"{match_id}-{team_lineup['team_id']}",
        "match_id": match_id,
        **team_lineup,
        "_ingest": _ingest_meta(source, ingested_at),
    }


def event_doc(event: dict, match_id: int, source: str, ingested_at: datetime) -> dict:
    return {
        "_id": event["id"],
        "match_id": match_id,
        **event,
        "_ingest": _ingest_meta(source, ingested_at),
    }


def upsert(collection: Collection, docs: Iterable[dict]) -> int:
    """Replace each document by `_id`, inserting it if absent. Returns the number written."""
    ops = [ReplaceOne({"_id": doc["_id"]}, doc, upsert=True) for doc in docs]
    if ops:
        collection.bulk_write(ops, ordered=False)
    return len(ops)


def ensure_indexes(db: Database) -> None:
    db.events.create_index("match_id")
    db.events.create_index("type.name")
    db.lineups.create_index("match_id")
    db.matches.create_index([("competition.competition_id", 1), ("season.season_id", 1)])


def load_season(
    db: Database, competition_id: int, season_id: int, fetch: Fetch, workers: int = 8
) -> dict[str, int]:
    """Load the competition record, matches, lineups, and events for one season."""
    ingested_at = datetime.now(UTC)
    counts = {"competitions": 0, "matches": 0, "lineups": 0, "events": 0}

    competitions = [
        c
        for c in fetch("competitions.json")
        if c["competition_id"] == competition_id and c["season_id"] == season_id
    ]
    if not competitions:
        raise ValueError(f"competition {competition_id} season {season_id} not found")
    counts["competitions"] = upsert(
        db.competitions,
        (competition_doc(c, "competitions.json", ingested_at) for c in competitions),
    )

    matches_path = f"matches/{competition_id}/{season_id}.json"
    matches = fetch(matches_path)
    counts["matches"] = upsert(
        db.matches, (match_doc(m, matches_path, ingested_at) for m in matches)
    )

    def fetch_match_files(match_id: int) -> tuple[int, list, list]:
        return match_id, fetch(f"lineups/{match_id}.json"), fetch(f"events/{match_id}.json")

    match_ids = [m["match_id"] for m in matches]
    # Download in small batches so only a few matches' events are held in memory at once.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for start in range(0, len(match_ids), workers):
            batch = match_ids[start : start + workers]
            for match_id, lineups, events in pool.map(fetch_match_files, batch):
                counts["lineups"] += upsert(
                    db.lineups,
                    (
                        lineup_doc(t, match_id, f"lineups/{match_id}.json", ingested_at)
                        for t in lineups
                    ),
                )
                counts["events"] += upsert(
                    db.events,
                    (
                        event_doc(e, match_id, f"events/{match_id}.json", ingested_at)
                        for e in events
                    ),
                )
            log.info("loaded %s/%s matches", min(start + workers, len(match_ids)), len(match_ids))

    ensure_indexes(db)
    return counts


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--competition-id", type=int, default=43, help="default: FIFA World Cup")
    parser.add_argument("--season-id", type=int, default=106, help="default: 2022")
    parser.add_argument("--cache-dir", type=Path, default=Path("data/raw/statsbomb"))
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = MongoSettings.from_env()
    client = settings.client()
    statsbomb = StatsBombClient(cache_dir=args.cache_dir)

    db = client[settings.database]
    started = time.perf_counter()
    try:
        written = load_season(db, args.competition_id, args.season_id, statsbomb.fetch)
        elapsed = time.perf_counter() - started
        stored = {name: db[name].count_documents({}) for name in written}
    finally:
        client.close()

    log.info("done in %.1fs", elapsed)
    log.info("documents written this run: %s", written)
    log.info("documents now stored:       %s", stored)


if __name__ == "__main__":
    main()
