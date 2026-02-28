from datetime import date

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from pipelines.ingestion.utils import ndc10_to_ndc11
from shared.db.models import RawCmsAspPricing, RawCmsCrosswalk


def _normalize_ndc11(value: str) -> str:
    ndc11 = ndc10_to_ndc11(value)
    if not ndc11:
        raise ValueError("Invalid NDC")
    return ndc11


def get_crosswalk_by_ndc(session: Session, ndc11: str, as_of_date: date | None = None) -> list[dict]:
    normalized = _normalize_ndc11(ndc11)
    stmt = select(RawCmsCrosswalk).where(RawCmsCrosswalk.ndc11 == normalized).order_by(desc(RawCmsCrosswalk.as_of_date))
    if as_of_date:
        stmt = stmt.where(RawCmsCrosswalk.as_of_date == as_of_date)
    rows = session.scalars(stmt).all()
    return [
        {
            "ndc11": row.ndc11,
            "hcpcs": row.hcpcs,
            "short_description": row.short_description,
            "long_description": row.long_description,
            "quarter": row.quarter,
            "effective_date": row.effective_date,
            "as_of_date": row.as_of_date,
            "ingestion_run_id": str(row.ingestion_run_id),
        }
        for row in rows
    ]


def get_crosswalk_by_hcpcs(session: Session, hcpcs: str, as_of_date: date | None = None) -> list[dict]:
    stmt = select(RawCmsCrosswalk).where(RawCmsCrosswalk.hcpcs == hcpcs).order_by(desc(RawCmsCrosswalk.as_of_date))
    if as_of_date:
        stmt = stmt.where(RawCmsCrosswalk.as_of_date == as_of_date)
    rows = session.scalars(stmt).all()
    return [
        {
            "ndc11": row.ndc11,
            "hcpcs": row.hcpcs,
            "short_description": row.short_description,
            "long_description": row.long_description,
            "quarter": row.quarter,
            "effective_date": row.effective_date,
            "as_of_date": row.as_of_date,
            "ingestion_run_id": str(row.ingestion_run_id),
        }
        for row in rows
    ]


def get_pricing_by_hcpcs(session: Session, hcpcs: str, as_of_date: date | None = None) -> list[dict]:
    stmt = select(RawCmsAspPricing).where(RawCmsAspPricing.hcpcs == hcpcs).order_by(desc(RawCmsAspPricing.as_of_date), desc(RawCmsAspPricing.effective_date))
    if as_of_date:
        stmt = stmt.where(RawCmsAspPricing.as_of_date == as_of_date)
    rows = session.scalars(stmt).all()
    return [
        {
            "hcpcs": row.hcpcs,
            "short_description": row.short_description,
            "payment_limit": row.payment_limit,
            "units": row.units,
            "quarter": row.quarter,
            "effective_date": row.effective_date,
            "as_of_date": row.as_of_date,
            "ingestion_run_id": str(row.ingestion_run_id),
        }
        for row in rows
    ]


def get_pricing_by_ndc(
    session: Session,
    ndc11: str,
    as_of_date: date | None = None,
    hcpcs_hint: str | None = None,
) -> dict:
    normalized = _normalize_ndc11(ndc11)
    crosswalk = get_crosswalk_by_ndc(session, normalized, as_of_date)

    hcpcs_codes = sorted({r["hcpcs"] for r in crosswalk if r.get("hcpcs")})
    if hcpcs_hint:
        hcpcs_codes = [h for h in hcpcs_codes if h == hcpcs_hint]

    pricing_rows = []
    for hcpcs in hcpcs_codes:
        pricing_rows.extend(get_pricing_by_hcpcs(session, hcpcs, as_of_date))

    return {
        "input_ndc11": normalized,
        "matched_hcpcs": hcpcs_codes,
        "crosswalk_rows": crosswalk,
        "pricing_rows": pricing_rows,
    }
