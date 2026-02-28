SHELL := /bin/bash

AS_OF ?= 2025-12-01
INGEST_PATH ?= data/nadac/nadac.csv

.PHONY: up-core down api-logs ingest-nadac migrate

up-core:
	docker compose --profile core up --build

down:
	docker compose down -v

api-logs:
	docker compose logs -f api

migrate:
	alembic upgrade head

ingest-nadac:
	python -m pipelines.ingestion.cli nadac --path $(INGEST_PATH) --as-of $(AS_OF)
