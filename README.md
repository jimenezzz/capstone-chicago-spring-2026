# Pharmaceutical Economic Data Hub

Monorepo scaffold for ingesting NADAC, Orange Book, Purple Book, OpenFDA, and CMS data into PostgreSQL as the source of truth, with FastAPI query endpoints and modular dataframe transforms.

## Repository Layout
- `apps/api`: FastAPI service
- `apps/web`: Next.js placeholder UI scaffold
- `pipelines/ingestion`: per-source ingestion logic + Typer CLI
- `pipelines/transforms`: dataframe transforms from DB raw layer
- `pipelines/jobs`: Prefect placeholder flow
- `shared`: common config, db session, SQLAlchemy models
- `alembic`: migrations
- `infra/azure`: deployment mapping notes
- `data` and `notebooks`: existing source data + notebook retained

## Prerequisites
- Python 3.12
- Docker + Docker Compose

## Configuration
Copy `.env.example` to `.env` and update values.

Required environment variable:
- `DATABASE_URL`

Example local value:
- `postgresql+psycopg://postgres:postgres@localhost:5432/pharma_hub`

Azure usage:
- Set `DATABASE_URL` to Azure Database for PostgreSQL Flexible Server connection string.

## Local Run
Start core services (db + api):
```bash
docker compose --profile core up
```

Start only specific services:
```bash
docker compose up db
docker compose up api db
```

API health:
- [http://localhost:8000/health](http://localhost:8000/health)

## Fresh Machine: Complete Command Order (Data Already in `data/`)
Use this sequence on a brand-new machine after cloning, assuming all source files are already present under `data/`.

1. Copy env file:
```bash
cp .env.example .env
```

2. Start only Postgres first (background):
```bash
docker compose up -d db
```

3. Run migrations against the DB container:
```bash
docker compose run --rm --build pipelines alembic upgrade head
```

4. Ingest each source in a consistent order (set your snapshot date once):
```bash
AS_OF=2025-12-01

docker compose run --rm --build pipelines python -m pipelines.ingestion.cli nadac --path /app/data/nadac/nadac.csv --as-of ${AS_OF}
docker compose run --rm --build pipelines python -m pipelines.ingestion.cli orange-book --zip /app/data/orange_book/products.txt --as-of ${AS_OF}
docker compose run --rm --build pipelines python -m pipelines.ingestion.cli purple-book --path /app/data/purple_book/purple_book.csv --as-of ${AS_OF}
docker compose run --rm --build pipelines python -m pipelines.ingestion.cli openfda --local-json /app/data/openfda/openfda_drug_ndc.json --as-of ${AS_OF}
docker compose run --rm --build pipelines python -m pipelines.ingestion.cli cms-crosswalk --dir /app/data/ndc_hcpcs_crosswalk --as-of ${AS_OF}
docker compose run --rm --build pipelines python -m pipelines.ingestion.cli cms-asp --dir /app/data/asp_pricing --as-of ${AS_OF}
```

5. Start the API (and keep it running in this terminal):
```bash
docker compose --profile core up --build api
```

6. Verify API:
```bash
curl -sS http://localhost:8000/health
curl -sS http://localhost:8000/meta/as-of-dates
```

7. Optional cleanup when done:
```bash
docker compose down
```

### psql connection
```bash
docker compose exec db psql -U postgres -d pharma_hub
```

## Migrations
```bash
alembic upgrade head
```

## Ingestion CLI (historic loads via `--as-of`)
Examples:
```bash
python -m pipelines.ingestion.cli nadac --path data/nadac/nadac.csv --as-of 2025-12-01
python -m pipelines.ingestion.cli orange-book --zip data/orange_book/products.txt --as-of 2025-12-01
python -m pipelines.ingestion.cli purple-book --path data/purple_book/purple_book.csv --as-of 2025-12-01
python -m pipelines.ingestion.cli openfda --local-json data/openfda/openfda_drug_ndc.json --as-of 2025-12-01
python -m pipelines.ingestion.cli cms-crosswalk --dir data/ndc_hcpcs_crosswalk --as-of 2025-12-01
python -m pipelines.ingestion.cli cms-asp --dir data/asp_pricing --as-of 2025-12-01
```

Idempotency:
- ingestion skips when `(source_name, as_of_date, file_hash)` was already loaded with success.
- use `--force` to re-ingest.

## API Endpoints
- `GET /health`
- `GET /meta/as-of-dates`
- `GET /ndc/{ndc11}`
- `GET /ndc/{ndc11}/pricing/nadac`
- `GET /cms/crosswalk/ndc/{ndc11}`
- `GET /cms/crosswalk/hcpcs/{hcpcs}`
- `GET /cms/pricing/hcpcs/{hcpcs}`
- `GET /cms/pricing/ndc/{ndc11}`
- `GET /cms/pricing?ndc11=...&hcpcs=...&as_of_date=YYYY-MM-DD`

## Transforms
`pipelines/transforms/*.py` read from DB raw tables and recreate notebook-like intermediate dataframes:
- `get_nadac_norm`, `get_nadac_latest`
- `get_openfda_xwalk`
- `get_orange_book_agg`
- `get_purple_book_agg`
- `get_cms_crosswalk_agg`, `get_asp_pricing`
- `build_master_dataframe`

## Makefile helpers
```bash
make up-core
make down
make api-logs
make ingest-nadac AS_OF=2025-12-01 INGEST_PATH=data/nadac/nadac.csv
```
