import csv
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.db.models import IngestionRun


def parse_as_of(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_ndc(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return "".join(c for c in str(value).strip() if c in "0123456789-")


def ndc10_to_ndc11(ndc10: str | None) -> str | None:
    if not ndc10:
        return None
    raw = clean_ndc(ndc10)
    digits = raw.replace("-", "")
    if len(digits) == 11:
        return digits
    if len(digits) != 10:
        return None

    if "-" in raw:
        parts = [p for p in raw.split("-") if p]
        if len(parts) == 3:
            a, b, c = parts
            if len(a) <= 5 and len(b) <= 4 and len(c) <= 2:
                return a.zfill(5) + b.zfill(4) + c.zfill(2)
            return None
    return digits[:5].zfill(5) + digits[5:9].zfill(4) + digits[9:].zfill(2)


def extract_ndc_from_description(text: Any) -> str | None:
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    m = re.search(r"\b(\d{5}-?\d{4}-?\d{2}|\d{11}|\d{10})\b", str(text))
    return clean_ndc(m.group(1)) if m else None


def normalize_application_number(appl_type: Any, appl_no: Any) -> str | None:
    if pd.isna(appl_type) and pd.isna(appl_no):
        return None
    app_type = str(appl_type).strip().upper() if appl_type is not None and not pd.isna(appl_type) else "N"
    digits = "".join(c for c in str(appl_no) if c.isdigit()) if appl_no is not None else ""
    if not digits:
        return None
    prefix = "NDA" if app_type == "N" else "ANDA"
    return prefix + digits.zfill(6)


def normalize_bla_number(bla: Any) -> tuple[str | None, str | None]:
    if bla is None or (isinstance(bla, float) and pd.isna(bla)):
        return None, None
    raw = str(bla).strip()
    digits = "".join(c for c in raw if c.isdigit())
    if not digits:
        return None, raw
    return "BLA" + digits.zfill(6), raw


def normalize_openfda_application_number(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip().upper()
    if not s:
        return None
    digits = "".join(c for c in s if c.isdigit())
    if not digits:
        return None
    if "BLA" in s:
        return "BLA" + digits.zfill(6)
    if "ANDA" in s or s.startswith("A"):
        return "ANDA" + digits.zfill(6)
    return "NDA" + digits.zfill(6)


def ensure_file(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    return p


def load_csv_or_excel(path: Path, **kwargs: Any) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, **kwargs)
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(path, **kwargs)
    return pd.read_csv(path, **kwargs)


def load_pipe_delimited(path: Path, sep: str = "|", **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(path, sep=sep, encoding="utf-8", on_bad_lines="skip", **kwargs)


def load_purple_book(path: Path) -> pd.DataFrame:
    if path.suffix.lower() != ".csv":
        return load_csv_or_excel(path)
    df = pd.read_csv(path, header=3)
    if len(df.columns) > 0:
        first_col = df.columns[0]
        df = df.loc[df.iloc[:, 0].astype(str).str.strip() != "N/R/U"]
        df = df.dropna(how="all")
        if first_col == "N/R/U":
            df[first_col] = df[first_col].fillna("R").astype(str).str.strip()
            df.loc[df[first_col] == "", first_col] = "R"
    return df.reset_index(drop=True)


def openfda_get(url: str, params: dict[str, Any], cache_file: Path, api_key: str | None = None) -> dict[str, Any]:
    payload = dict(params)
    if api_key:
        payload["api_key"] = api_key
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, params=payload, timeout=45)
    response.raise_for_status()
    data = response.json()
    cache_file.write_text(json.dumps(data))
    return data


def make_jsonable(value: Any) -> Any:
    """Convert pandas/numpy values into JSON-safe values for JSONB inserts."""
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): make_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_jsonable(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if pd.isna(value):
        return None
    if isinstance(value, Path):
        return str(value)
    return value


def find_header_row(path: Path, required_fields: list[str], max_rows: int = 200) -> int:
    required = [x.upper() for x in required_fields]
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        reader = csv.reader(fh)
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            vals = [str(c).strip() for c in row if str(c).strip()]
            if len(vals) < 3:
                continue
            upper = [c.upper() for c in vals]
            if all(any(req == c or req in c for c in upper) for req in required):
                return i
    return 0


def read_csv_with_detected_header(path: Path, required_fields: list[str], max_rows: int = 200) -> pd.DataFrame:
    header_row = find_header_row(path, required_fields, max_rows=max_rows)
    try:
        return pd.read_csv(path, header=header_row, dtype=str, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(
            path,
            header=header_row,
            dtype=str,
            encoding="latin-1",
            on_bad_lines="skip",
        )


def get_existing_run(
    session: Session,
    source_name: str,
    as_of_date: date,
    file_hash: str | None,
) -> IngestionRun | None:
    if not file_hash:
        return None
    stmt = (
        select(IngestionRun)
        .where(IngestionRun.source_name == source_name)
        .where(IngestionRun.as_of_date == as_of_date)
        .where(IngestionRun.file_hash == file_hash)
        .where(IngestionRun.status == "success")
        .order_by(IngestionRun.ingested_at.desc())
        .limit(1)
    )
    return session.scalar(stmt)


def create_run(
    session: Session,
    source_name: str,
    as_of_date: date,
    source_path: str,
    file_hash: str | None,
    dataset_version: str | None = None,
    notes: str | None = None,
) -> IngestionRun:
    run = IngestionRun(
        source_name=source_name,
        as_of_date=as_of_date,
        source_path=source_path,
        file_hash=file_hash,
        dataset_version=dataset_version,
        notes=notes,
        status="started",
    )
    session.add(run)
    session.flush()
    return run


def complete_run(session: Session, run: IngestionRun, row_count: int, notes: str | None = None) -> None:
    run.status = "success"
    run.row_count = row_count
    if notes:
        run.notes = notes
    session.add(run)


def fail_run(session: Session, run: IngestionRun, message: str) -> None:
    run.status = "failed"
    run.notes = message
    session.add(run)
