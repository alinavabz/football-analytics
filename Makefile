.PHONY: up down ps test lint format reset

# Start Postgres and MongoDB, and wait until both pass their health checks
up:
	docker compose up -d --wait

down:
	docker compose down

ps:
	docker compose ps

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
