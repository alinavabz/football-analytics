# Changelog

All notable changes to this project are recorded here. Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
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
