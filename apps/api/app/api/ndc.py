from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.app.db.session import get_db
from apps.api.app.schemas.ndc import (
    NadacHistoryRow,
    NadacStatsResponse,
    NdcLookupResponse,
    NdcPricePredictionResponse,
)
from apps.api.app.services.ndc import (
    get_nadac_price_statistics,
    get_nadac_pricing_history,
    get_ndc_overview,
    get_ndc_price_prediction,
)

router = APIRouter(prefix="/ndc", tags=["ndc"])


@router.get("/{ndc11}", response_model=NdcLookupResponse)
def ndc_lookup(
    ndc11: str,
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> NdcLookupResponse:
    return NdcLookupResponse(**get_ndc_overview(db, ndc11, as_of_date))


@router.get("/{ndc11}/pricing/nadac", response_model=list[NadacHistoryRow])
def ndc_nadac_pricing(
    ndc11: str,
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[NadacHistoryRow]:
    return [NadacHistoryRow(**row) for row in get_nadac_pricing_history(db, ndc11, as_of_date)]


@router.get("/{ndc11}/pricing/nadac/stats", response_model=NadacStatsResponse)
def ndc_nadac_price_stats(
    ndc11: str,
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> NadacStatsResponse:
    return NadacStatsResponse(**get_nadac_price_statistics(db, ndc11, as_of_date))


@router.get("/{ndc11}/pricing/prediction", response_model=NdcPricePredictionResponse)
def ndc_price_prediction(
    ndc11: str,
    months: int = Query(default=12, ge=1, le=60),
    db: Session = Depends(get_db),
) -> NdcPricePredictionResponse:
    return NdcPricePredictionResponse(**get_ndc_price_prediction(db, ndc11, months))
