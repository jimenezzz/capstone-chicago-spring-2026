from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import insert
from sqlalchemy.orm import Session

from pipelines.ingestion.utils import (
    complete_run,
    compute_sha256,
    create_run,
    get_existing_run,
    load_purple_book,
    make_jsonable,
    normalize_bla_number,
)
from shared.db.models import RawPurpleBook


SOURCE_NAME = "purple_book"


def ingest_purple_book(session: Session, path: str, as_of_date: date, force: bool = False) -> dict[str, Any]:
    file_path = Path(path)
    file_hash = compute_sha256(file_path)

    if not force:
        existing = get_existing_run(session, SOURCE_NAME, as_of_date, file_hash)
        if existing:
            return {"status": "skipped", "reason": "already_ingested", "ingestion_run_id": str(existing.id)}

    df = load_purple_book(file_path)
    run = create_run(session, SOURCE_NAME, as_of_date, str(file_path), file_hash)

    bla_col = next((c for c in ["BLA Number", "BLA_Number"] if c in df.columns), None)
    prop_col = next((c for c in ["Proprietary Name", "Proprietary_Name"] if c in df.columns), None)
    proper_col = next((c for c in ["Proper Name", "Proper_Name"] if c in df.columns), None)

    rows: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        app_norm, bla_raw = normalize_bla_number(row.get(bla_col) if bla_col else None)
        rows.append(
            {
                "ingestion_run_id": run.id,
                "as_of_date": as_of_date,
                "source_row": make_jsonable(row),
                "application_number_norm": app_norm,
                "bla_number": bla_raw,
                "proprietary_name": row.get(prop_col) if prop_col else None,
                "proper_name": row.get(proper_col) if proper_col else None,
            }
        )

    if rows:
        session.execute(insert(RawPurpleBook), rows)

    complete_run(session, run, row_count=len(rows))
    return {"status": "success", "row_count": len(rows), "ingestion_run_id": str(run.id)}
