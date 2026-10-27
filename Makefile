.PHONY: up down restart test lint migrate ps logs

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d

ps:
	docker compose ps

logs:
	docker compose logs -f

test:
	docker compose run --rm backend pytest -v
	docker compose run --rm worker pytest -v
	docker compose run --rm frontend npm test

lint:
	docker compose run --rm backend ruff check .
	docker compose run --rm worker ruff check .
	docker compose run --rm frontend npm run lint

migrate:
	docker compose run --rm backend alembic upgrade head
