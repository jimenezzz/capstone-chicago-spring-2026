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
    get_existing_run,
    make_jsonable,
    read_csv_with_detected_header,
)
from shared.db.models import RawCmsAspPricing


SOURCE_NAME = "cms_asp_pricing"


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    s = str(v).replace("$", "").replace(",", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "HCPCS Code": "hcpcs",
        "HCPCS": "hcpcs",
        "Short Description": "short_description",
        "SHORT DESCRIPTOR": "short_description",
        "HCPCS Code Dosage": "units",
        "Payment Limit": "payment_limit",
        "PAYMENT": "payment_limit",
    }
    renamed = {}
    for c in df.columns:
        key = str(c).strip()
        upper = key.upper()
        if key in mapping:
            renamed[c] = mapping[key]
        elif upper in mapping:
            renamed[c] = mapping[upper]
        elif "QUARTER" in upper:
            renamed[c] = "quarter"
        elif "EFFECTIVE" in upper:
            renamed[c] = "effective_date"
    return df.rename(columns=renamed)


def ingest_cms_asp_pricing(session: Session, directory_or_file: str, as_of_date: date, force: bool = False) -> dict[str, Any]:
    base = Path(directory_or_file)
    if base.is_dir():
        files = sorted(base.glob("*.csv"))
    else:
        files = [base]

    if not files:
        raise FileNotFoundError(f"No pricing CSV files found at {base}")

    hash_input = "".join(compute_sha256(f) for f in files)
    file_hash = compute_sha256(files[0]) if len(files) == 1 else __import__("hashlib").sha256(hash_input.encode()).hexdigest()

    if not force:
        existing = get_existing_run(session, SOURCE_NAME, as_of_date, file_hash)
        if existing:
            return {"status": "skipped", "reason": "already_ingested", "ingestion_run_id": str(existing.id)}

    run = create_run(session, SOURCE_NAME, as_of_date, str(base), file_hash)

    rows: list[dict[str, Any]] = []
    for file in files:
        df = read_csv_with_detected_header(file, ["HCPCS", "PAYMENT"], max_rows=220)
        df = _normalize_columns(df)
        for row in df.to_dict(orient="records"):
            eff = pd.to_datetime(row.get("effective_date"), errors="coerce") if row.get("effective_date") else None
            rows.append(
                {
                    "ingestion_run_id": run.id,
                    "as_of_date": as_of_date,
                    "source_row": make_jsonable({**row, "source_file": file.name}),
                    "hcpcs": str(row.get("hcpcs", "")).strip() or None,
                    "short_description": row.get("short_description"),
                    "payment_limit": _to_float(row.get("payment_limit")),
                    "units": row.get("units"),
                    "quarter": row.get("quarter"),
                    "effective_date": eff.date() if eff is not None and not pd.isna(eff) else None,
                }
            )

    if rows:
        session.execute(insert(RawCmsAspPricing), rows)

    complete_run(session, run, row_count=len(rows))
    return {"status": "success", "row_count": len(rows), "ingestion_run_id": str(run.id)}
