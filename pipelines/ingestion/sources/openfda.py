import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import insert
from sqlalchemy.orm import Session

from pipelines.ingestion.utils import (
    clean_ndc,
    complete_run,
    create_run,
    get_existing_run,
    make_jsonable,
    ndc10_to_ndc11,
    normalize_openfda_application_number,
    openfda_get,
)
from shared.config import get_settings
from shared.db.models import RawOpenfdaNdc


SOURCE_NAME = "openfda"
OPENFDA_NDC_URL = "https://api.fda.gov/drug/ndc.json"


def _read_local_openfda(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    return data.get("results", [])


def _fetch_from_api(ndcs: list[str]) -> list[dict[str, Any]]:
    settings = get_settings()
    cache_dir = settings.data_dir / "openfda_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for ndc in ndcs:
        cleaned = clean_ndc(ndc)
        search_ndc = ndc10_to_ndc11(cleaned) or cleaned.replace("-", "")
        if len(search_ndc) == 11:
            search_ndc = f"{search_ndc[:5]}-{search_ndc[5:9]}-{search_ndc[9:]}"
        params = {"search": f'package_ndc:"{search_ndc}"', "limit": 100}
        cache_key = hashlib.sha256((OPENFDA_NDC_URL + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:20]
        cache_file = cache_dir / f"ndc_q_{cache_key}.json"
        payload = openfda_get(OPENFDA_NDC_URL, params, cache_file, api_key=settings.openfda_api_key)
        for rec in payload.get("results", []):
            results.append(rec)
    return results


def ingest_openfda(
    session: Session,
    as_of_date: date,
    ndc_file: str | None = None,
    ndc_list: str | None = None,
    local_json: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    source_descriptor = local_json or ndc_file or "openfda_api"
    source_hash = None

    records: list[dict[str, Any]] = []
    if local_json:
        file_path = Path(local_json)
        source_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if not force:
            existing = get_existing_run(session, SOURCE_NAME, as_of_date, source_hash)
            if existing:
                return {"status": "skipped", "reason": "already_ingested", "ingestion_run_id": str(existing.id)}
        records = _read_local_openfda(file_path)
    else:
        ndcs: list[str] = []
        if ndc_file:
            p = Path(ndc_file)
            ndcs.extend([line.strip() for line in p.read_text().splitlines() if line.strip()])
        if ndc_list:
            ndcs.extend([x.strip() for x in ndc_list.split(",") if x.strip()])
        ndcs = list(dict.fromkeys(ndcs))
        source_hash = hashlib.sha256("|".join(sorted(ndcs)).encode()).hexdigest()
        if not force:
            existing = get_existing_run(session, SOURCE_NAME, as_of_date, source_hash)
            if existing:
                return {"status": "skipped", "reason": "already_ingested", "ingestion_run_id": str(existing.id)}
        if not ndcs:
            raise ValueError("Provide --ndc-file, --ndc-list, or --local-json")
        records = _fetch_from_api(ndcs)

    run = create_run(session, SOURCE_NAME, as_of_date, source_descriptor, source_hash)

    rows: list[dict[str, Any]] = []
    for rec in records:
        packaging = rec.get("packaging") or []
        for package in packaging:
            package_ndc = package.get("package_ndc")
            package_ndc11 = ndc10_to_ndc11(package_ndc)
            rows.append(
                {
                    "ingestion_run_id": run.id,
                    "as_of_date": as_of_date,
                    "source_row": make_jsonable({"record": rec, "package": package}),
                    "package_ndc": package_ndc,
                    "package_ndc11": package_ndc11,
                    "product_ndc": rec.get("product_ndc"),
                    "application_number": rec.get("application_number"),
                    "application_number_norm": normalize_openfda_application_number(rec.get("application_number")),
                    "generic_name": rec.get("generic_name"),
                    "brand_name": rec.get("brand_name"),
                }
            )

    if rows:
        session.execute(insert(RawOpenfdaNdc), rows)

    complete_run(session, run, row_count=len(rows))
    return {"status": "success", "row_count": len(rows), "ingestion_run_id": str(run.id)}
