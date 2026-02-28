from datetime import date

import pandas as pd

from pipelines.transforms._common import read_df, resolve_as_of


SOURCE_CROSSWALK = "cms_crosswalk"
SOURCE_ASP = "cms_asp_pricing"


def get_cms_crosswalk_agg(as_of_date: date | None = None) -> pd.DataFrame:
    resolved = resolve_as_of(SOURCE_CROSSWALK, as_of_date)
    if resolved is None:
        return pd.DataFrame()
    return read_df(
        """
        select ndc11, hcpcs, short_description, long_description, quarter, effective_date
        from raw_cms_crosswalk
        where as_of_date = :as_of_date
        """,
        {"as_of_date": resolved},
    )


def get_asp_pricing(as_of_date: date | None = None) -> pd.DataFrame:
    resolved = resolve_as_of(SOURCE_ASP, as_of_date)
    if resolved is None:
        return pd.DataFrame()
    return read_df(
        """
        select hcpcs, short_description, payment_limit, units, quarter, effective_date
        from raw_cms_asp_pricing
        where as_of_date = :as_of_date
        """,
        {"as_of_date": resolved},
    )
