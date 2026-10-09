.PHONY: up down ps psql mongosh ingest load bench test lint format reset

# Start Postgres and MongoDB, and wait until both pass their health checks
up:
	docker compose up -d --wait

down:
	docker compose down

ps:
	docker compose ps

# Open a database shell, logging in with the credentials from .env
psql:
	docker compose exec postgres sh -c 'psql -U "$$POSTGRES_USER"'

mongosh:
	docker compose exec mongo sh -c 'mongosh -u "$$MONGO_INITDB_ROOT_USERNAME" -p "$$MONGO_INITDB_ROOT_PASSWORD"'

# Load FIFA World Cup 2022 from StatsBomb open data into MongoDB. Safe to rerun.
ingest:
	PYTHONPATH=src uv run --env-file .env python -m football_analytics.ingest

# Build the relational model in PostgreSQL (schema core) from the MongoDB raw store. Safe to rerun.
load:
	PYTHONPATH=src uv run --env-file .env python -m football_analytics.load_core

# Time the analyst queries in sql/queries/ with EXPLAIN ANALYZE
bench:
	PYTHONPATH=src uv run --env-file .env python -m football_analytics.bench

test:
	uv run --env-file .env pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

# WARNING: deletes all database volumes. Every row in Postgres and MongoDB is lost.
reset:
	docker compose down -v
