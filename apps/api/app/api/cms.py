from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.app.db.session import get_db
from apps.api.app.schemas.cms import CmsCrosswalkRow, CmsPricingByNdcResponse, CmsPricingRow
from apps.api.app.services.cms import (
    get_crosswalk_by_hcpcs,
    get_crosswalk_by_ndc,
    get_pricing_by_hcpcs,
    get_pricing_by_ndc,
)

router = APIRouter(prefix="/cms", tags=["cms"])


@router.get("/crosswalk/ndc/{ndc11}", response_model=list[CmsCrosswalkRow])
def cms_crosswalk_ndc(
    ndc11: str,
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CmsCrosswalkRow]:
    try:
        rows = get_crosswalk_by_ndc(db, ndc11, as_of_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [CmsCrosswalkRow(**row) for row in rows]


@router.get("/crosswalk/hcpcs/{hcpcs}", response_model=list[CmsCrosswalkRow])
def cms_crosswalk_hcpcs(
    hcpcs: str,
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CmsCrosswalkRow]:
    return [CmsCrosswalkRow(**row) for row in get_crosswalk_by_hcpcs(db, hcpcs, as_of_date)]


@router.get("/pricing/hcpcs/{hcpcs}", response_model=list[CmsPricingRow])
def cms_pricing_hcpcs(
    hcpcs: str,
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CmsPricingRow]:
    return [CmsPricingRow(**row) for row in get_pricing_by_hcpcs(db, hcpcs, as_of_date)]


@router.get("/pricing/ndc/{ndc11}", response_model=CmsPricingByNdcResponse)
def cms_pricing_ndc(
    ndc11: str,
    as_of_date: date | None = Query(default=None),
    hcpcs: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CmsPricingByNdcResponse:
    try:
        payload = get_pricing_by_ndc(db, ndc11, as_of_date, hcpcs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CmsPricingByNdcResponse(**payload)


@router.get("/pricing")
def cms_pricing(
    ndc11: str | None = Query(default=None),
    hcpcs: str | None = Query(default=None),
    as_of_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if not ndc11 and not hcpcs:
        raise HTTPException(status_code=400, detail="Provide at least one of ndc11 or hcpcs")
    if ndc11:
        return cms_pricing_ndc(ndc11=ndc11, as_of_date=as_of_date, hcpcs=hcpcs, db=db)
    return [CmsPricingRow(**row) for row in get_pricing_by_hcpcs(db, hcpcs=hcpcs or "", as_of_date=as_of_date)]
