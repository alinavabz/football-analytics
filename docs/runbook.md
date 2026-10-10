# Runbook

How to run, check, and recover the football-analytics stack. All commands run from the repository root.

## Start and stop

| Task | Command |
|---|---|
| Start PostgreSQL and MongoDB, wait until healthy | `make up` |
| Stop (data kept in volumes) | `make down` |
| Full pipeline | `make ingest load dbt` |
| Status | `make ps` |

## Health checks

| Check | How | Healthy looks like |
|---|---|---|
| Containers | `make ps` | both services `Up (healthy)` |
| Databases answer with the configured credentials | `make test` | all tests pass |
| Raw store complete | `make ingest` log line `documents now stored` | 64 matches, 128 lineups, 234,637 events for World Cup 2022 |
| Relational model matches raw | `make load` | ends with `rows in core, reconciled with mongodb`; a mismatch aborts the load |
| Reporting layer valid | `make dbt` | `ERROR=0`; freshness `PASS` |

## Failures and what to do

**`make up` times out or a service is unhealthy.** Run `docker compose logs postgres` or `docker compose logs mongo`. A port already in use (5432, 27017) means another database is running locally: stop it, or change the left-hand port in `compose.yaml`.

**`Authentication failed` from MongoDB, or `password authentication failed` from PostgreSQL.** The credentials in `.env` differ from the ones the database was first created with. Both images read credentials only when their volume is empty. Either restore the old values in `.env`, or, if the data can be reloaded, run `make reset`, then `make up` and the full pipeline.

**`make ingest` fails with an HTTP or network error.** Downloads retry three times. Files already downloaded are cached in `data/raw/`, so rerunning continues from the cache. If StatsBomb has moved a file, the error names the path.

**`make load` fails with `reconciliation failed`.** The transaction is rolled back and `core` still holds the previous load. Compare the counts in the message; rerun `make ingest` if MongoDB is incomplete.

**`make load` fails on a constraint (CHECK, foreign key, NOT NULL).** New source data broke a rule in `sql/001_core_schema.sql`. Nothing was written. Inspect the offending record in MongoDB (`make mongosh`) and decide whether the rule or the data is wrong; change the rule only with a reason in the pull request.

**`make dbt` fails a test.** Run `cd dbt && uv run --env-file ../.env dbt test --profiles-dir . --store-failures` and query the failing rows in the `dbt_test__audit` schema. A failing reconciliation test (`assert_goals_match_scoreline`) means goals were lost or duplicated between MongoDB and the marts.

**Freshness warns or errors.** The last successful `make load` is older than 30 (warn) or 90 (error) days. Rerun the pipeline.

## Recovery

The pipeline is rebuildable from the source:

1. `make reset` (deletes both volumes), then `make up`.
2. `make ingest load dbt`. Each step is idempotent and can be rerun after a failure.

MongoDB is the only store that cannot be rebuilt offline; with the `data/raw/` cache present, no network access is needed.
