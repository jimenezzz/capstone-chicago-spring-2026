from datetime import date

import pandas as pd
from sqlalchemy import text

from shared.db.session import get_engine


def resolve_as_of(source_name: str, as_of_date: date | None = None) -> date | None:
    if as_of_date is not None:
        return as_of_date
    sql = text(
        """
        select max(as_of_date) as as_of_date
        from ingestion_run
        where source_name = :source_name and status = 'success'
        """
    )
    with get_engine().connect() as conn:
        row = conn.execute(sql, {"source_name": source_name}).first()
    return row[0] if row and row[0] is not None else None


def read_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})
