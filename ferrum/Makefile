.PHONY: up down migrate seed test logs shell db-shell graph-sync embeddings clean

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m data.scripts.seed_db

test:
	docker compose exec api pytest

logs:
	docker compose logs -f

shell:
	docker compose exec api bash

db-shell:
	docker compose exec postgres psql -U ferrum

graph-sync:
	docker compose exec api python -m data.scripts.sync_graph

embeddings:
	docker compose exec api python -m data.scripts.generate_embeddings

clean:
	docker compose down -v
