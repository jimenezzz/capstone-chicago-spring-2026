from datetime import date

import pandas as pd

from pipelines.transforms._common import read_df, resolve_as_of


SOURCE_NAME = "purple_book"


def get_purple_book_agg(as_of_date: date | None = None) -> pd.DataFrame:
    resolved = resolve_as_of(SOURCE_NAME, as_of_date)
    if resolved is None:
        return pd.DataFrame()
    return read_df(
        """
        select application_number_norm,
               max(proprietary_name) as proprietary_name,
               max(proper_name) as proper_name,
               count(*) as row_count
        from raw_purple_book
        where as_of_date = :as_of_date
        group by application_number_norm
        """,
        {"as_of_date": resolved},
    )
