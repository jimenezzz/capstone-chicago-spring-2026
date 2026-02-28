from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import insert
from sqlalchemy.orm import Session

from pipelines.ingestion.utils import (
    complete_run,
    compute_sha256,
    create_run,
    extract_ndc_from_description,
    get_existing_run,
    load_csv_or_excel,
    make_jsonable,
    ndc10_to_ndc11,
)
from shared.db.models import RawNadac


SOURCE_NAME = "nadac"


def _to_float(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).replace("$", "").replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def ingest_nadac(session: Session, path: str, as_of_date: date, force: bool = False) -> dict[str, Any]:
    file_path = Path(path)
    file_hash = compute_sha256(file_path)

    if not force:
        existing = get_existing_run(session, SOURCE_NAME, as_of_date, file_hash)
        if existing:
            return {"status": "skipped", "reason": "already_ingested", "ingestion_run_id": str(existing.id)}

    df = load_csv_or_excel(file_path)
    run = create_run(session, SOURCE_NAME, as_of_date, str(file_path), file_hash)

    ndc_col = next((c for c in ["NDC", "ndc", "NDC Code"] if c in df.columns), None)
    price_col = next((c for c in ["NADAC Per Unit", "nadac_per_unit", "unit_price", "price"] if c in df.columns), None)
    effective_col = next((c for c in ["Effective Date", "effective_date", "As of Date", "date"] if c in df.columns), None)
    desc_col = next((c for c in ["NDC Description", "description", "drug_name"] if c in df.columns), None)

    rows: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        ndc_raw = str(row.get(ndc_col, "")).strip() if ndc_col else None
        ndc11 = ndc10_to_ndc11(ndc_raw)
        if not ndc11 and desc_col:
            extracted = extract_ndc_from_description(row.get(desc_col))
            ndc11 = ndc10_to_ndc11(extracted)

        effective_date = None
        if effective_col and row.get(effective_col):
            effective_date = pd.to_datetime(row.get(effective_col), errors="coerce")
            effective_date = None if pd.isna(effective_date) else effective_date.date()

        rows.append(
            {
                "ingestion_run_id": run.id,
                "as_of_date": as_of_date,
                "source_row": make_jsonable(row),
                "ndc_raw": ndc_raw,
                "ndc11": ndc11,
                "nadac_price": _to_float(row.get(price_col)) if price_col else None,
                "effective_date": effective_date,
                "ndc_description": str(row.get(desc_col, "")).strip() if desc_col else None,
            }
        )

    if rows:
        session.execute(insert(RawNadac), rows)

    complete_run(session, run, row_count=len(rows))
    return {"status": "success", "row_count": len(rows), "ingestion_run_id": str(run.id)}
