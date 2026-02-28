from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class NdcLookupResponse(BaseModel):
    ndc11: str
    nadac_price: Decimal | None = None
    nadac_effective_date: date | None = None
    application_number: str | None = None
    application_number_norm: str | None = None
    brand_name: str | None = None
    generic_name: str | None = None
    hcpcs_codes: list[str] = Field(default_factory=list)


class NadacHistoryRow(BaseModel):
    as_of_date: date
    effective_date: date | None = None
    nadac_price: Decimal | None = None
    ingestion_run_id: str
