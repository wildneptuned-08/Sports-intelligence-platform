# Sports Intelligence Platform — Makefile
.PHONY: help up down restart logs shell psql test test-cov lint format \
        migrate migration rollback migrate-history create-test-db \
        sync-fixtures sync-results build clean

# ── Default ──────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Sports Intelligence Platform — available commands:"
	@echo ""
	@echo "  Docker:"
	@echo "    make up           — Start all containers (detached)"
	@echo "    make down         — Stop and remove containers"
	@echo "    make restart      — Restart the API container"
	@echo "    make logs         — Tail API logs"
	@echo "    make build        — Rebuild Docker images"
	@echo "    make clean        — Remove containers, volumes and images"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate      — Run pending Alembic migrations"
	@echo "    make migration name=<desc> — Create new migration (autogenerate)"
	@echo "    make rollback     — Roll back one migration"
	@echo "    make migrate-history — Show migration history"
	@echo "    make psql         — Open PostgreSQL interactive shell"
	@echo "    make create-test-db — Create sip_test database for tests"
	@echo ""
	@echo "  Development:"
	@echo "    make shell        — Open Python shell inside api container"
	@echo "    make test         — Run tests"
	@echo "    make test-cov     — Run tests with coverage report"
	@echo "    make lint         — Run ruff linter"
	@echo "    make format       — Auto-format code with ruff"
	@echo ""
	@echo "  ETL (Sprint 2+):"
	@echo "    make sync-fixtures — Run fixture sync job manually"
	@echo "    make sync-results  — Run results sync job manually"
	@echo ""

# ── Docker ───────────────────────────────────────────────────────────────────
up:
	docker compose up -d
	@echo "API:  http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

down:
	docker compose down

restart:
	docker compose restart api

logs:
	docker compose logs -f api

build:
	docker compose build

clean:
	docker compose down -v --rmi local

# ── Database ─────────────────────────────────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

# Usage: make migration name="add_user_avatar"
migration:
	docker compose exec api alembic revision --autogenerate -m "$(name)"

rollback:
	docker compose exec api alembic downgrade -1

migrate-history:
	docker compose exec api alembic history --verbose

psql:
	docker compose exec postgres psql -U sip -d sip_db

create-test-db:
	docker compose exec postgres psql -U sip -d sip_db -c "CREATE DATABASE sip_test;" || true

# ── Development ──────────────────────────────────────────────────────────────
shell:
	docker compose exec api python

test:
	docker compose exec api pytest -v

test-cov:
	docker compose exec api pytest --cov=app --cov-report=term-missing -v

lint:
	docker compose exec api ruff check app tests
	docker compose exec api ruff format --check app tests

format:
	docker compose exec api ruff format app tests
	docker compose exec api ruff check --fix app tests

# ── ETL Manual Triggers (Sprint 2+) ─────────────────────────────────────────
sync-fixtures:
	docker compose exec api python -c "\
import asyncio; \
from app.etl.jobs.sync_fixtures import sync_fixtures; \
asyncio.run(sync_fixtures())"

sync-results:
	docker compose exec api python -c "\
import asyncio; \
from app.etl.jobs.sync_results import sync_results; \
asyncio.run(sync_results())"
