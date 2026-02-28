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
    ndc10_to_ndc11,
    read_csv_with_detected_header,
)
from shared.db.models import RawCmsCrosswalk


SOURCE_NAME = "cms_crosswalk"


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    col_map: dict[str, str] = {}
    for c in df.columns:
        upper = str(c).strip().upper()
        if upper in {"HCPCS CODE", "HCPCS", "CODE", "_2026_CODE"}:
            col_map[c] = "hcpcs"
        elif upper in {"NDC", "NDC2", "11-DIGIT NATIONAL DRUG CODE (NDC) OR ALTERNATE ID"}:
            col_map[c] = "ndc_raw"
        elif upper in {"SHORT DESCRIPTOR", "SHORT DESCRIPTION"}:
            col_map[c] = "short_description"
        elif upper in {"LONG DESCRIPTION", "LONG DESCRIPTOR"}:
            col_map[c] = "long_description"
        elif "QUARTER" in upper:
            col_map[c] = "quarter"
        elif "EFFECTIVE" in upper:
            col_map[c] = "effective_date"
    return df.rename(columns=col_map)


def ingest_cms_crosswalk(session: Session, directory: str, as_of_date: date, force: bool = False) -> dict[str, Any]:
    source_dir = Path(directory)
    files = sorted(source_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {source_dir}")

    hash_input = "".join(compute_sha256(f) for f in files)
    file_hash = compute_sha256(Path(files[0])) if len(files) == 1 else __import__("hashlib").sha256(hash_input.encode()).hexdigest()

    if not force:
        existing = get_existing_run(session, SOURCE_NAME, as_of_date, file_hash)
        if existing:
            return {"status": "skipped", "reason": "already_ingested", "ingestion_run_id": str(existing.id)}

    run = create_run(session, SOURCE_NAME, as_of_date, str(source_dir), file_hash)

    rows: list[dict[str, Any]] = []
    for file in files:
        df = read_csv_with_detected_header(file, ["CODE", "NDC"], max_rows=220)
        df = df.loc[:, ~df.columns.duplicated()]
        df = _normalize_columns(df)
        for row in df.to_dict(orient="records"):
            hcpcs = str(row.get("hcpcs", "")).strip() or None
            ndc_raw = row.get("ndc_raw")
            ndc11 = ndc10_to_ndc11(str(ndc_raw)) if ndc_raw else None
            eff = pd.to_datetime(row.get("effective_date"), errors="coerce") if row.get("effective_date") else None
            rows.append(
                {
                    "ingestion_run_id": run.id,
                    "as_of_date": as_of_date,
                    "source_row": make_jsonable({**row, "source_file": file.name}),
                    "ndc11": ndc11,
                    "hcpcs": hcpcs,
                    "short_description": row.get("short_description"),
                    "long_description": row.get("long_description"),
                    "quarter": row.get("quarter"),
                    "effective_date": eff.date() if eff is not None and not pd.isna(eff) else None,
                }
            )

    if rows:
        session.execute(insert(RawCmsCrosswalk), rows)

    complete_run(session, run, row_count=len(rows))
    return {"status": "success", "row_count": len(rows), "ingestion_run_id": str(run.id)}
