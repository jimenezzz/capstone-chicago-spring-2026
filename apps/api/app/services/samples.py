from collections.abc import Sequence
from decimal import Decimal
from datetime import date, datetime
from typing import Any
from uuid import UUID

import pandas as pd
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pipelines.transforms.master import build_master_dataframe
from shared.db.models import (
    RawCmsAspPricing,
    RawNadac,
    RawOpenfdaNdc,
    RawOrangeBookProducts,
    RawPurpleBook,
)


def _serialize_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for row in rows:
        data = {column.name: getattr(row, column.name) for column in row.__table__.columns}
        serialized.append(jsonable_encoder(data))
    return serialized


def _random_raw_rows(session: Session, model: Any, n: int) -> list[dict[str, Any]]:
    stmt = select(model).order_by(func.random()).limit(n)
    rows = session.scalars(stmt).all()
    return _serialize_rows(rows)


def _coerce_filter_value(column: Any, value: str) -> Any:
    try:
        python_type = column.type.python_type
    except (AttributeError, NotImplementedError):
        return value

    if value == "null":
        return None

    if python_type is str:
        return value
    if python_type is int:
        return int(value)
    if python_type is float:
        return float(value)
    if python_type is Decimal:
        return Decimal(value)
    if python_type is UUID:
        return UUID(value)
    if python_type is bool:
        return value.lower() in {"true", "1", "yes"}
    if python_type is date:
        return date.fromisoformat(value)
    if python_type is datetime:
        return datetime.fromisoformat(value)
    return value


def _filtered_raw_rows(session: Session, model: Any, filters: dict[str, str], n: int) -> list[dict[str, Any]]:
    columns = {column.name: column for column in model.__table__.columns}
    stmt = select(model)

    for key, raw_value in filters.items():
        if key not in columns:
            raise ValueError(f"Invalid filter column '{key}' for table '{model.__tablename__}'")
        column = columns[key]
        value = _coerce_filter_value(column, raw_value)
        if value is None:
            stmt = stmt.where(column.is_(None))
        else:
            stmt = stmt.where(column == value)

    stmt = stmt.order_by(model.id.desc()).limit(n)
    rows = session.scalars(stmt).all()
    return _serialize_rows(rows)


def get_random_cms_pricing_rows(session: Session, n: int) -> list[dict[str, Any]]:
    return _random_raw_rows(session, RawCmsAspPricing, n)


def get_random_nadac_rows(session: Session, n: int) -> list[dict[str, Any]]:
    return _random_raw_rows(session, RawNadac, n)


def get_random_openfda_rows(session: Session, n: int) -> list[dict[str, Any]]:
    return _random_raw_rows(session, RawOpenfdaNdc, n)


def get_random_orange_book_rows(session: Session, n: int) -> list[dict[str, Any]]:
    return _random_raw_rows(session, RawOrangeBookProducts, n)


def get_random_purple_book_rows(session: Session, n: int) -> list[dict[str, Any]]:
    return _random_raw_rows(session, RawPurpleBook, n)


def get_master_dataframe_rows(n: int) -> list[dict[str, Any]]:
    df = build_master_dataframe()
    if df.empty:
        return []

    # Convert NaN/NaT to JSON nulls before dict conversion.
    clean = df.where(pd.notna(df), None)
    if n < len(clean):
        clean = clean.sample(n=n, random_state=None)

    return jsonable_encoder(clean.to_dict(orient="records"))


def get_exact_cms_pricing_rows(session: Session, filters: dict[str, str], n: int) -> list[dict[str, Any]]:
    return _filtered_raw_rows(session, RawCmsAspPricing, filters, n)


def get_exact_nadac_rows(session: Session, filters: dict[str, str], n: int) -> list[dict[str, Any]]:
    return _filtered_raw_rows(session, RawNadac, filters, n)


def get_exact_openfda_rows(session: Session, filters: dict[str, str], n: int) -> list[dict[str, Any]]:
    return _filtered_raw_rows(session, RawOpenfdaNdc, filters, n)


def get_exact_orange_book_rows(session: Session, filters: dict[str, str], n: int) -> list[dict[str, Any]]:
    return _filtered_raw_rows(session, RawOrangeBookProducts, filters, n)


def get_exact_purple_book_rows(session: Session, filters: dict[str, str], n: int) -> list[dict[str, Any]]:
    return _filtered_raw_rows(session, RawPurpleBook, filters, n)


def get_exact_master_dataframe_rows(filters: dict[str, str], n: int) -> list[dict[str, Any]]:
    df = build_master_dataframe()
    if df.empty:
        return []

    for key, value in filters.items():
        if key not in df.columns:
            raise ValueError(f"Invalid filter column '{key}' for master dataframe")
        if value == "null":
            df = df[df[key].isna()]
        else:
            df = df[df[key].astype(str) == value]

    clean = df.where(pd.notna(df), None)
    if n < len(clean):
        clean = clean.head(n)
    return jsonable_encoder(clean.to_dict(orient="records"))
