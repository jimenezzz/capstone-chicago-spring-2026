from datetime import date

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from pipelines.ingestion.utils import ndc10_to_ndc11
from shared.db.models import RawCmsCrosswalk, RawNadac, RawOpenfdaNdc


def _normalized_ndc11(ndc: str) -> str:
    ndc11 = ndc10_to_ndc11(ndc)
    if not ndc11:
        raise ValueError("Invalid NDC format")
    return ndc11


def get_ndc_overview(session: Session, ndc11: str, as_of_date: date | None = None) -> dict:
    normalized = _normalized_ndc11(ndc11)

    nadac_stmt: Select = (
        select(RawNadac)
        .where(RawNadac.ndc11 == normalized)
        .order_by(desc(RawNadac.as_of_date), desc(RawNadac.effective_date))
        .limit(1)
    )
    if as_of_date:
        nadac_stmt = nadac_stmt.where(RawNadac.as_of_date == as_of_date)
    nadac = session.scalar(nadac_stmt)

    openfda_stmt: Select = (
        select(RawOpenfdaNdc)
        .where(RawOpenfdaNdc.package_ndc11 == normalized)
        .order_by(desc(RawOpenfdaNdc.as_of_date))
        .limit(1)
    )
    if as_of_date:
        openfda_stmt = openfda_stmt.where(RawOpenfdaNdc.as_of_date == as_of_date)
    openfda = session.scalar(openfda_stmt)

    hcpcs_stmt = select(RawCmsCrosswalk.hcpcs).where(RawCmsCrosswalk.ndc11 == normalized)
    if as_of_date:
        hcpcs_stmt = hcpcs_stmt.where(RawCmsCrosswalk.as_of_date == as_of_date)
    hcpcs = [r[0] for r in session.execute(hcpcs_stmt).all() if r[0]]

    return {
        "ndc11": normalized,
        "nadac_price": nadac.nadac_price if nadac else None,
        "nadac_effective_date": nadac.effective_date if nadac else None,
        "application_number": openfda.application_number if openfda else None,
        "application_number_norm": openfda.application_number_norm if openfda else None,
        "brand_name": openfda.brand_name if openfda else None,
        "generic_name": openfda.generic_name if openfda else None,
        "hcpcs_codes": sorted(set(hcpcs)),
    }


def get_nadac_pricing_history(session: Session, ndc11: str, as_of_date: date | None = None) -> list[dict]:
    normalized = _normalized_ndc11(ndc11)
    stmt: Select = (
        select(RawNadac)
        .where(RawNadac.ndc11 == normalized)
        .order_by(desc(RawNadac.as_of_date), desc(RawNadac.effective_date))
    )
    if as_of_date:
        stmt = stmt.where(RawNadac.as_of_date == as_of_date)

    rows = session.scalars(stmt).all()
    return [
        {
            "as_of_date": row.as_of_date,
            "effective_date": row.effective_date,
            "nadac_price": row.nadac_price,
            "ingestion_run_id": str(row.ingestion_run_id),
        }
        for row in rows
    ]
