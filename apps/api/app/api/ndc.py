from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.app.db.session import get_db
from apps.api.app.schemas.ndc import NadacHistoryRow, NdcLookupResponse
from apps.api.app.services.ndc import get_nadac_pricing_history, get_ndc_overview

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
