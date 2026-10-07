.PHONY: up down seed test

up:
	docker compose up -d minio chromadb api ui

down:
	docker compose down -v

seed:
	docker compose --profile pipeline run --rm ingestion python fetch_arxiv.py
	docker compose --profile pipeline run --rm dbt dbt run
	docker compose --profile pipeline run --rm embedding python embed_and_index.py

test:
	cd ingestion && pytest tests/ -v
	cd embedding && pytest tests/ -v
	cd api && pytest tests/ -v
