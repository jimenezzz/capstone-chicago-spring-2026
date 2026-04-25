import random
from datetime import date
from decimal import Decimal
from functools import lru_cache
from statistics import median, pstdev

from sqlalchemy import Select, cast, desc, func, select
from sqlalchemy import String as SqlString
from sqlalchemy.orm import Session

from apps.api.app.services.settings import get_volatility_risk_settings
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
        select(
            RawNadac.as_of_date,
            RawNadac.effective_date,
            RawNadac.nadac_price,
            func.min(cast(RawNadac.ingestion_run_id, SqlString)).label("ingestion_run_id"),
            func.count(RawNadac.id).label("record_count"),
        )
        .where(RawNadac.ndc11 == normalized)
        .group_by(RawNadac.as_of_date, RawNadac.effective_date, RawNadac.nadac_price)
        .order_by(desc(RawNadac.as_of_date), desc(RawNadac.effective_date))
    )
    if as_of_date:
        stmt = stmt.where(RawNadac.as_of_date == as_of_date)

    rows = session.execute(stmt).all()
    return [
        {
            "as_of_date": as_of,
            "effective_date": effective,
            "nadac_price": price,
            "ingestion_run_id": str(ingestion_run_id),
            "record_count": record_count,
        }
        for as_of, effective, price, ingestion_run_id, record_count in rows
    ]


def get_nadac_price_statistics(session: Session, ndc11: str, as_of_date: date | None = None) -> dict:
    normalized = _normalized_ndc11(ndc11)
    risk_settings = get_volatility_risk_settings(session)
    volatility_threshold_pct = risk_settings["threshold_pct"]
    moderate_risk_months = risk_settings["moderate_risk_months"]
    high_risk_months = risk_settings["high_risk_months"]
    history = get_nadac_pricing_history(session, normalized, as_of_date)
    points = [
        row
        for row in history
        if row["effective_date"] is not None and row["nadac_price"] is not None
    ]
    points.sort(key=lambda row: row["effective_date"])

    raw_total = sum(int(row["record_count"]) for row in history)
    prices = [Decimal(row["nadac_price"]) for row in points]

    if not prices:
        return {
            "ndc11": normalized,
            "summary": {
                "point_count": 0,
                "raw_record_count": raw_total,
                "volatility_threshold_pct": volatility_threshold_pct,
                "moderate_risk_months": moderate_risk_months,
                "high_risk_months": high_risk_months,
                "volatile_month_count": 0,
                "stability_label": "Stable",
            },
            "monthly": [],
        }

    monthly_groups: dict[str, list[Decimal]] = {}
    for row in points:
        month_key = row["effective_date"].strftime("%Y-%m")
        monthly_groups.setdefault(month_key, []).append(Decimal(row["nadac_price"]))

    monthly = []
    previous_average: Decimal | None = None
    for month_key in sorted(monthly_groups):
        month_prices = monthly_groups[month_key]
        average = sum(month_prices) / Decimal(len(month_prices))
        change = average - previous_average if previous_average is not None else None
        change_pct = (
            (change / previous_average) * Decimal("100")
            if change is not None and previous_average and previous_average != 0
            else None
        )
        monthly.append(
            {
                "month": month_key,
                "average_price": average,
                "min_price": min(month_prices),
                "max_price": max(month_prices),
                "median_price": Decimal(str(median(month_prices))),
                "point_count": len(month_prices),
                "mom_change": change,
                "mom_change_pct": change_pct,
            }
        )
        previous_average = average

    latest = points[-1]
    first_price = Decimal(points[0]["nadac_price"])
    latest_price = Decimal(latest["nadac_price"])
    total_change_pct = (
        ((latest_price - first_price) / first_price) * Decimal("100")
        if first_price != 0
        else None
    )
    monthly_change_pcts = [
        Decimal(row["mom_change_pct"])
        for row in monthly
        if row["mom_change_pct"] is not None
    ]
    volatile_month_count = sum(
        1 for change_pct in monthly_change_pcts if abs(change_pct) > volatility_threshold_pct
    )
    if volatile_month_count >= high_risk_months:
        stability_label = "High Risk"
    elif volatile_month_count >= moderate_risk_months:
        stability_label = "Moderate Risk"
    else:
        stability_label = "Stable"

    summary = {
        "min_price": min(prices),
        "max_price": max(prices),
        "average_price": sum(prices) / Decimal(len(prices)),
        "median_price": Decimal(str(median(prices))),
        "price_std_dev": (
            Decimal(str(pstdev([float(price) for price in prices])))
            if len(prices) > 1
            else Decimal("0")
        ),
        "latest_price": latest_price,
        "latest_effective_date": latest["effective_date"],
        "earliest_effective_date": points[0]["effective_date"],
        "point_count": len(points),
        "raw_record_count": raw_total,
        "price_range": max(prices) - min(prices),
        "total_change_pct": total_change_pct,
        "latest_mom_change": monthly[-1]["mom_change"] if monthly else None,
        "latest_mom_change_pct": monthly[-1]["mom_change_pct"] if monthly else None,
        "volatility_threshold_pct": volatility_threshold_pct,
        "moderate_risk_months": moderate_risk_months,
        "high_risk_months": high_risk_months,
        "volatile_month_count": volatile_month_count,
        "max_positive_spike_pct": max(monthly_change_pcts) if monthly_change_pcts else None,
        "max_negative_drop_pct": min(monthly_change_pcts) if monthly_change_pcts else None,
        "stability_label": stability_label,
    }

    return {"ndc11": normalized, "summary": summary, "monthly": monthly}


@lru_cache(maxsize=512)
def _cached_prediction(ndc11: str, months: int, latest_price: str | None) -> tuple[Decimal, ...]:
    seed = f"{ndc11}:{months}:{latest_price or 'none'}"
    rng = random.Random(seed)
    return tuple(Decimal(str(round(rng.random(), 6))) for _ in range(months))


def _prediction_summary(predictions: tuple[Decimal, ...]) -> dict:
    if not predictions:
        return {}

    first_price = predictions[0]
    last_price = predictions[-1]
    total_change = last_price - first_price
    total_change_pct = (total_change / first_price) * Decimal("100") if first_price != 0 else None

    return {
        "min_price": min(predictions),
        "max_price": max(predictions),
        "average_price": sum(predictions) / Decimal(len(predictions)),
        "median_price": Decimal(str(median(predictions))),
        "price_range": max(predictions) - min(predictions),
        "first_price": first_price,
        "last_price": last_price,
        "total_change": total_change,
        "total_change_pct": total_change_pct,
    }


def get_ndc_price_prediction(session: Session, ndc11: str, months: int = 12) -> dict:
    normalized = _normalized_ndc11(ndc11)
    latest_stmt = (
        select(RawNadac)
        .where(RawNadac.ndc11 == normalized)
        .order_by(desc(RawNadac.as_of_date), desc(RawNadac.effective_date))
        .limit(1)
    )
    latest = session.scalar(latest_stmt)

    # features = {
    #     "ndc11": normalized,
    #     "nadac_price": latest.nadac_price if latest else None,
    #     "effective_date": latest.effective_date if latest else None,
    #     "ndc_description": latest.ndc_description if latest else None,
    # }
    # predictions = model.predict(features, months=months)

    latest_price = str(latest.nadac_price) if latest and latest.nadac_price is not None else None
    predictions = _cached_prediction(normalized, months, latest_price)
    return {
        "ndc11": normalized,
        "months": months,
        "summary": _prediction_summary(predictions),
        "predictions": [
            {"month": index + 1, "predicted_price": price}
            for index, price in enumerate(predictions)
        ],
    }
