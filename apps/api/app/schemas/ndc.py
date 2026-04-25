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
    record_count: int = 1


class NadacMonthlyPoint(BaseModel):
    month: str
    average_price: Decimal
    min_price: Decimal
    max_price: Decimal
    median_price: Decimal
    point_count: int
    mom_change: Decimal | None = None
    mom_change_pct: Decimal | None = None


class NadacStatsSummary(BaseModel):
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    average_price: Decimal | None = None
    median_price: Decimal | None = None
    latest_price: Decimal | None = None
    latest_effective_date: date | None = None
    earliest_effective_date: date | None = None
    point_count: int = 0
    raw_record_count: int = 0
    price_range: Decimal | None = None
    latest_mom_change: Decimal | None = None
    latest_mom_change_pct: Decimal | None = None


class NadacStatsResponse(BaseModel):
    ndc11: str
    summary: NadacStatsSummary
    monthly: list[NadacMonthlyPoint]


class NdcPricePredictionPoint(BaseModel):
    month: int
    predicted_price: Decimal


class NdcPricePredictionResponse(BaseModel):
    ndc11: str
    months: int
    predictions: list[NdcPricePredictionPoint]
