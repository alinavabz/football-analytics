# Data contract: `core` schema (PostgreSQL)

Relational model of the StatsBomb raw store. Analytical models and reports read from here.

| | |
|---|---|
| Owner | football-analytics loader (`src/football_analytics/load_core.py`) |
| Source | MongoDB `statsbomb_raw` (see [statsbomb-raw.md](statsbomb-raw.md)) |
| Schema definition | [`sql/001_core_schema.sql`](../../sql/001_core_schema.sql) |
| Delivery | Batch, `make load`, after `make ingest`. One transaction: readers see the previous load or the new one, never a partial one |
| Guarantees | Rows are merged by primary key, so reloads never duplicate. Row counts for matches, squads, events, shots, and passes are reconciled with MongoDB before commit; a mismatch aborts the load |
| Freshness | Same as the raw store: historical data, reloaded on demand |

## Tables

| Table | One row per | Primary key | References |
|---|---|---|---|
| `competitions` | competition season | `(competition_id, season_id)` | |
| `teams` | team | `team_id` | |
| `players` | player | `player_id` | |
| `matches` | match | `match_id` | competitions, teams (home and away) |
| `match_players` | player in a match squad | `(match_id, player_id)` | matches, players, teams |
| `events` | on-ball or off-ball event | `event_id` (uuid) | matches, teams, players |
| `shots` | shot (subset of events) | `event_id` | events, key pass event |
| `passes` | pass (subset of events) | `event_id` | events, recipient player |

## Notes for consumers

- `match_players.started` is true for the starting eleven; `played` is true for anyone who took the field. Unused substitutes have both false.
- `passes.outcome` is `'Complete'` when StatsBomb records no outcome; otherwise StatsBomb's value (`Incomplete`, `Out`, ...).
- Period 5 is the penalty shootout. Exclude it when counting goals from open play.
- Coordinates: x 0 to 120 towards the opponent's goal, y 0 to 80.
- Not modelled here, available in MongoDB: shot freeze frames, tactics and formations, related events, and type-specific detail for events other than shots and passes.
