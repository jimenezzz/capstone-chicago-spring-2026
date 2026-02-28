from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CmsCrosswalkRow(BaseModel):
    ndc11: str | None = None
    hcpcs: str | None = None
    short_description: str | None = None
    long_description: str | None = None
    quarter: str | None = None
    effective_date: date | None = None
    as_of_date: date
    ingestion_run_id: str


class CmsPricingRow(BaseModel):
    hcpcs: str | None = None
    short_description: str | None = None
    payment_limit: Decimal | None = None
    units: str | None = None
    quarter: str | None = None
    effective_date: date | None = None
    as_of_date: date
    ingestion_run_id: str


class CmsPricingByNdcResponse(BaseModel):
    input_ndc11: str
    matched_hcpcs: list[str]
    crosswalk_rows: list[CmsCrosswalkRow]
    pricing_rows: list[CmsPricingRow]
