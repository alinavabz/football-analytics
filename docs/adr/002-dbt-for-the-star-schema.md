# ADR-002: dbt for the star schema

- Status: accepted
- Date: 2026-10-09

## Context

Reporting needs a star schema: facts at a stated grain surrounded by dimensions. The `core` schema is shaped for correctness (normalised, constrained), not for reporting. The reporting layer is SQL transformations of `core`, and it needs tests that stop bad data reaching a dashboard, documentation of every column, and a record of which model depends on which.

## Decision

Build the reporting layer with dbt, in `dbt/`:

- `staging` (views): one model per `core` table, renaming and adding simple flags. No joins.
- `marts` (tables): `dim_team`, `dim_player`, `dim_match`, `dim_date`, and two facts at the finest grain available, `fact_shots` (one row per shot) and `fact_events` (one row per event). Totals are aggregated in the reporting tool, never stored, so no detail is lost.
- Tests run with every build: keys unique and not null, every foreign key resolves to its dimension, accepted values, and a reconciliation test that goals counted from events equal every official scoreline. Source freshness reads `core.load_runs`.

## Alternatives considered

- **SQL views in a numbered SQL file.** No new tool, but no tests, no lineage, and dependency order maintained by hand.
- **Python transformations in the loader.** Mixes loading with modelling, and tests become code rather than declarations next to the models.

## Consequences

- One more tool and dependency (`dbt-postgres`).
- `ref()` and `source()` give dbt the dependency graph, so build order and the lineage diagram (`make docs`) come for free.
- Facts at the finest grain are larger (234,637 event rows) than pre-aggregated tables would be; at this volume that costs under two seconds per build.
