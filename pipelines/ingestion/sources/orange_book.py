from datetime import date
from pathlib import Path
from typing import Any
import tempfile
import zipfile

import pandas as pd
from sqlalchemy import insert
from sqlalchemy.orm import Session

from pipelines.ingestion.utils import (
    complete_run,
    compute_sha256,
    create_run,
    get_existing_run,
    load_pipe_delimited,
    make_jsonable,
    normalize_application_number,
)
from shared.db.models import RawOrangeBookProducts


SOURCE_NAME = "orange_book"


def ingest_orange_book(session: Session, zip_or_dir: str, as_of_date: date, force: bool = False) -> dict[str, Any]:
    path = Path(zip_or_dir)
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if path.is_dir():
        products_path = path / "products.txt"
    else:
        products_path = path

    if products_path.suffix.lower() == ".zip":
        temp_dir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(products_path, "r") as zf:
            zf.extractall(temp_dir.name)
        extracted_root = Path(temp_dir.name)
        matches = list(extracted_root.rglob("products.txt"))
        if not matches:
            raise FileNotFoundError("products.txt not found in Orange Book zip")
        products_path = matches[0]

    file_hash = compute_sha256(products_path)
    if not force:
        existing = get_existing_run(session, SOURCE_NAME, as_of_date, file_hash)
        if existing:
            return {"status": "skipped", "reason": "already_ingested", "ingestion_run_id": str(existing.id)}

    df = load_pipe_delimited(products_path, sep="~")
    run = create_run(session, SOURCE_NAME, as_of_date, str(products_path), file_hash)

    rows: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        appl_no = row.get("Appl_No")
        appl_type = row.get("Appl_Type")
        app_number_norm = normalize_application_number(appl_type, appl_no)
        app_number = None
        if app_number_norm:
            app_number = f"{str(appl_type).strip().upper() if appl_type else 'N'}{str(appl_no).strip()}"

        rows.append(
            {
                "ingestion_run_id": run.id,
                "as_of_date": as_of_date,
                "source_row": make_jsonable(row),
                "application_number": app_number,
                "application_number_norm": app_number_norm,
                "te_code": row.get("TE_Code"),
                "ingredient": row.get("Ingredient"),
                "trade_name": row.get("Trade_Name"),
            }
        )

    if rows:
        session.execute(insert(RawOrangeBookProducts), rows)

    complete_run(session, run, row_count=len(rows))
    if temp_dir is not None:
        temp_dir.cleanup()
    return {"status": "success", "row_count": len(rows), "ingestion_run_id": str(run.id)}
