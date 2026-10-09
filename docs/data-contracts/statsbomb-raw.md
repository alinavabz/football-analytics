# Data contract: `statsbomb_raw` (MongoDB)

Raw StatsBomb open data, stored as delivered. Downstream loaders read from here; nothing writes to it except `make ingest`.

| | |
|---|---|
| Owner | football-analytics ingestion (`src/football_analytics/ingest.py`) |
| Source | [StatsBomb open data](https://github.com/statsbomb/open-data), `data/` folder |
| Scope | One competition season per load. Default: FIFA World Cup 2022 (competition 43, season 106) |
| Delivery | Batch, on demand. Reloads replace documents by `_id`, so a load can be repeated or resumed without creating duplicates |
| Freshness | Historical data that does not change after a tournament. Reload only when StatsBomb publishes corrections |

## Collections

Every document keeps StatsBomb's fields and nesting unchanged. Two fields are added, and none are removed or renamed.

- `_ingest`: `{source, ingested_at}`, the source file path and load time (UTC).
- `match_id` on `events` and `lineups`: StatsBomb identifies the match only by file name, so it is copied onto each document.

| Collection | One document per | `_id` | Source file | Indexes |
|---|---|---|---|---|
| `competitions` | competition season | `"{competition_id}-{season_id}"` | `competitions.json` | `_id` |
| `matches` | match | `match_id` (int) | `matches/{competition_id}/{season_id}.json` | `_id`, `(competition.competition_id, season.season_id)` |
| `lineups` | team in a match | `"{match_id}-{team_id}"` | `lineups/{match_id}.json` | `_id`, `match_id` |
| `events` | event (pass, shot, carry, ...) | event `id` (UUID string) | `events/{match_id}.json` | `_id`, `match_id`, `type.name` |

## Guarantees

- No duplicates: `_id` is derived from StatsBomb identifiers and every write is an upsert.
- Nested structure preserved: for example `events.shot.freeze_frame` stays an array of player positions.
- A document missing from a reload is not deleted. If StatsBomb removes a record, the stale document must be removed by hand.

## Schema reference

Field-level definitions are StatsBomb's own: [open data specification](https://github.com/statsbomb/open-data/tree/master/doc).
