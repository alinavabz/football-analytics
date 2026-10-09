# Query performance

Analyst queries live in [`sql/queries/`](../sql/queries/). `make bench` runs each one with `EXPLAIN (ANALYZE)` 25 times after a warm-up and reports the median execution time and how each table was read.

Data: FIFA World Cup 2022, 234,637 rows in `core.events`. Measured on a laptop (Apple Silicon, Docker Desktop), PostgreSQL 16.

## Results

| Query | Before (ms) | After (ms) | What changed |
|---|---|---|---|
| Team shots and xG by match | 16.68 | 0.28 | Composite index `(team_id, event_type)` plus an explicit `event_type = 'Shot'` filter |
| Player pass recipients | 10.16 | 1.06 | Covering index `(player_id, event_type) INCLUDE (event_id)` plus SSD planner cost |
| Top scorers | 0.90 | 0.66 | Nothing: already driven from the 1,494-row shots table |
| One match's events in order | 2.54 | 3.09 | Nothing: already served by the `UNIQUE (match_id, event_index)` index |

Differences under about 1 ms between runs are noise at this data size.

Write cost: a full load into an empty schema took 8.9 s without the two indexes and 9.9 s with them, measured back to back.

## What the plans showed

### Team shots and xG by match

**Before:** `Seq Scan on events`. To find Argentina's shots, PostgreSQL read all 234,637 events, kept Argentina's, and joined them to shots.

An index on `(team_id, event_type)` alone was not enough. The query filters on team only, so the planner could use just the first column of the index, which still matched about 15,600 Argentina events of every type (passes, carries, pressures) before the join narrowed them to about 100 shots.

**Fix:** the query now also states `e.event_type = 'Shot'`. The join to `shots` already implied it, but the planner cannot infer that. With both columns of the composite index usable, the scan reads about 110 index entries.

### Player pass recipients

**Before:** `Seq Scan on events` to find Lionel Messi's passes.

With a `(player_id, event_type)` index, the planner found his 371 passes quickly but then joined them to `passes` by reading the whole 68,515-row table into a hash (`Seq Scan on passes`). Looking up 371 passes one at a time by primary key is cheaper, but the planner estimated otherwise.

The cause is the planner setting `random_page_cost`, the assumed cost of reading a page at a random position relative to reading the next page in sequence. Its default, 4.0, models spinning disks, where random reads are slow. On SSD storage the usual setting is 1.1. With it, the planner chose the index lookups.

**Fix:** `random_page_cost=1.1` in `compose.yaml`, and the index made covering with `INCLUDE (event_id)`, so the join key comes from the index without visiting the table (`Index Only Scan`).

### Top scorers, match events in order

Already efficient. Top scorers starts from the small `shots` table and looks events up by primary key. Match replay uses the index created by the `UNIQUE (match_id, event_index)` constraint, whose leading column is `match_id`. That is also why `match_id` needs no separate index.

## Composite index column order

PostgreSQL can use a composite index for any leftmost prefix of its columns. `(team_id, event_type)` serves "team = X" and "team = X and type = Y", but not "type = Y" alone. Both columns here are equality filters, and the team or player column comes first because it is the one every query in this set filters on.
