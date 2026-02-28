from datetime import date

import pandas as pd

from pipelines.transforms.cms import get_asp_pricing, get_cms_crosswalk_agg
from pipelines.transforms.nadac import get_nadac_latest
from pipelines.transforms.openfda import get_openfda_xwalk
from pipelines.transforms.orange_book import get_orange_book_agg
from pipelines.transforms.purple_book import get_purple_book_agg


def build_master_dataframe(as_of_date: date | None = None) -> pd.DataFrame:
    nadac_latest = get_nadac_latest(as_of_date)
    if nadac_latest.empty:
        return pd.DataFrame()

    df = nadac_latest[["ndc11", "nadac_price", "nadac_date", "ndc_description"]].copy()

    openfda = get_openfda_xwalk(as_of_date)
    if not openfda.empty:
        xwalk = openfda[
            ["package_ndc11", "product_ndc", "application_number", "application_number_norm", "brand_name", "generic_name"]
        ].drop_duplicates()
        xwalk = xwalk.rename(columns={"package_ndc11": "ndc11"})
        df = df.merge(xwalk, on="ndc11", how="left")

    if "application_number_norm" not in df.columns:
        df["application_number_norm"] = pd.NA

    orange = get_orange_book_agg(as_of_date)
    if not orange.empty:
        df = df.merge(orange, on="application_number_norm", how="left", suffixes=("", "_orange"))

    purple = get_purple_book_agg(as_of_date)
    if not purple.empty:
        df = df.merge(purple, on="application_number_norm", how="left", suffixes=("", "_purple"))

    cms_crosswalk = get_cms_crosswalk_agg(as_of_date)
    if not cms_crosswalk.empty:
        df = df.merge(cms_crosswalk, on="ndc11", how="left")

    asp = get_asp_pricing(as_of_date)
    if not asp.empty and "hcpcs" in df.columns:
        asp = asp.rename(columns={"short_description": "asp_short_description"})
        df = df.merge(asp, on="hcpcs", how="left", suffixes=("", "_asp"))

    return df
