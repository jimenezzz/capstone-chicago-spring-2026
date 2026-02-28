from datetime import date

import pandas as pd

from pipelines.transforms._common import read_df, resolve_as_of


SOURCE_NAME = "nadac"


def get_nadac_norm(as_of_date: date | None = None) -> pd.DataFrame:
    resolved = resolve_as_of(SOURCE_NAME, as_of_date)
    if resolved is None:
        return pd.DataFrame()
    df = read_df(
        """
        select ndc_raw, ndc11, nadac_price, effective_date as nadac_date, ndc_description
        from raw_nadac
        where as_of_date = :as_of_date
        """,
        {"as_of_date": resolved},
    )
    return df


def get_nadac_latest(as_of_date: date | None = None) -> pd.DataFrame:
    df = get_nadac_norm(as_of_date)
    if df.empty:
        return df
    if "nadac_date" in df.columns:
        df["nadac_date"] = pd.to_datetime(df["nadac_date"], errors="coerce")
        df = df.sort_values(["ndc11", "nadac_date"], ascending=[True, False])
        return df.drop_duplicates(subset=["ndc11"], keep="first")
    return df.drop_duplicates(subset=["ndc11"], keep="first")
