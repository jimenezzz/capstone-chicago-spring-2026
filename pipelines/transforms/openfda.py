from datetime import date

import pandas as pd

from pipelines.transforms._common import read_df, resolve_as_of


SOURCE_NAME = "openfda"


def get_openfda_xwalk(as_of_date: date | None = None) -> pd.DataFrame:
    resolved = resolve_as_of(SOURCE_NAME, as_of_date)
    if resolved is None:
        return pd.DataFrame()
    return read_df(
        """
        select package_ndc11, package_ndc, product_ndc, application_number, application_number_norm,
               generic_name, brand_name
        from raw_openfda_ndc
        where as_of_date = :as_of_date
        """,
        {"as_of_date": resolved},
    )
