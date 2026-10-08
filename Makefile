up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

test:
	uv run --env-file .env pytest

reset:
	docker compose down -v
# DELETS THE WHOLE DATABSE VOLUME, USE WITH CAUTION
delete:
	docker compose down

