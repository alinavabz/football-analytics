# Changelog

All notable changes to this project are recorded here. Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- dbt project: staging views and a star schema in `marts` (`fact_shots`, `fact_events`, match, team, player, and date dimensions), 37 data tests including goal-to-scoreline reconciliation, and source freshness on `core.load_runs`. `make dbt`, `make docs`. CI loads the full dataset and runs `dbt build`.
- ADR-002 and the `marts` data contract.
- Analyst queries in `sql/queries/` and `make bench`, which times them with EXPLAIN ANALYZE.
- Indexes from measured plans (`sql/002_indexes.sql`): team-level and covering player-level composite indexes on `core.events`. `make load` now applies every numbered SQL file in order.
- PostgreSQL `random_page_cost=1.1` for SSD storage. Query performance write-up in `docs/query-performance.md`.
- Relational model in PostgreSQL (schema `core`): competitions, teams, players, matches, match squads, events, shots, passes, with keys and constraints.
- `make load`: builds `core` from the MongoDB raw store in one transaction, merging by primary key and reconciling row counts with MongoDB.
- ADR-001 on keeping raw data in MongoDB and modelled data in PostgreSQL. Data contract for `core`.
- `make ingest`: loads a StatsBomb competition season (default FIFA World Cup 2022) into MongoDB as raw documents, with idempotent upserts keyed on StatsBomb IDs and a local file cache.
- Data contract for the `statsbomb_raw` collections.
- `make psql` and `make mongosh` open database shells using the credentials in `.env`.
- Docker Compose stack with PostgreSQL 16 and MongoDB 7, credentials read from `.env`, health checks on both services.
- Smoke tests that connect to each database and confirm it answers.
- Makefile targets for the local workflow.
- Pre-commit hooks: whitespace and YAML checks, ruff lint and format, gitleaks secret scan.
- CI on every pull request: lint, full-history secret scan, and tests against the Compose stack.
- Pull request and issue templates, contributing guide.
