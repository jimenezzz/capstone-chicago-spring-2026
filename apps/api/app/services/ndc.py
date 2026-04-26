from datetime import date
from decimal import Decimal
from statistics import median, pstdev

from sqlalchemy import Select, cast, desc, exists, func, select
from sqlalchemy import String as SqlString
from sqlalchemy.orm import Session

from apps.api.app.services.prediction_models import MODEL_LABELS, forecast_arima, forecast_lightgbm
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


def search_ndcs_by_name(
    session: Session,
    name: str,
    as_of_date: date | None = None,
    limit: int = 100,
) -> list[dict]:
    term = name.strip().lower()
    if not term:
        return []

    pattern = f"%{term}%"
    results: dict[str, dict] = {}
    nadac_exists = exists().where(RawNadac.ndc11 == RawOpenfdaNdc.package_ndc11)
    if as_of_date:
        nadac_exists = nadac_exists.where(RawNadac.as_of_date == as_of_date)

    openfda_stmt: Select = (
        select(
            RawOpenfdaNdc.package_ndc11,
            RawOpenfdaNdc.brand_name,
            RawOpenfdaNdc.generic_name,
            RawOpenfdaNdc.as_of_date,
        )
        .where(RawOpenfdaNdc.package_ndc11.is_not(None))
        .where(
            (
                RawOpenfdaNdc.brand_name.is_not(None)
                & func.lower(RawOpenfdaNdc.brand_name).like(pattern)
            )
            | (
                RawOpenfdaNdc.generic_name.is_not(None)
                & func.lower(RawOpenfdaNdc.generic_name).like(pattern)
            )
        )
        .order_by(desc(nadac_exists), desc(RawOpenfdaNdc.as_of_date), RawOpenfdaNdc.brand_name)
        .limit(limit * 4)
    )
    if as_of_date:
        openfda_stmt = openfda_stmt.where(RawOpenfdaNdc.as_of_date == as_of_date)

    for ndc11, brand_name, generic_name, source_as_of in session.execute(openfda_stmt).all():
        if not ndc11 or ndc11 in results:
            continue
        results[ndc11] = {
            "ndc11": ndc11,
            "brand_name": brand_name,
            "generic_name": generic_name,
            "ndc_description": None,
            "latest_nadac_price": None,
            "latest_effective_date": None,
            "as_of_date": source_as_of,
        }
        if len(results) >= limit:
            break

    nadac_stmt: Select = (
        select(
            RawNadac.ndc11,
            RawNadac.ndc_description,
            RawNadac.nadac_price,
            RawNadac.effective_date,
            RawNadac.as_of_date,
        )
        .where(RawNadac.ndc11.is_not(None))
        .where(RawNadac.ndc_description.is_not(None))
        .where(func.lower(RawNadac.ndc_description).like(pattern))
        .order_by(desc(RawNadac.as_of_date), desc(RawNadac.effective_date))
        .limit(limit * 4)
    )
    if as_of_date:
        nadac_stmt = nadac_stmt.where(RawNadac.as_of_date == as_of_date)

    for ndc11, description, price, effective_date, source_as_of in session.execute(nadac_stmt).all():
        if not ndc11:
            continue
        if ndc11 in results:
            results[ndc11]["ndc_description"] = results[ndc11]["ndc_description"] or description
            results[ndc11]["latest_nadac_price"] = results[ndc11]["latest_nadac_price"] or price
            results[ndc11]["latest_effective_date"] = (
                results[ndc11]["latest_effective_date"] or effective_date
            )
            continue
        results[ndc11] = {
            "ndc11": ndc11,
            "brand_name": None,
            "generic_name": None,
            "ndc_description": description,
            "latest_nadac_price": price,
            "latest_effective_date": effective_date,
            "as_of_date": source_as_of,
        }
        if len(results) >= limit:
            break

    for row in results.values():
        if not row["brand_name"] or not row["generic_name"]:
            openfda_detail_stmt: Select = (
                select(
                    RawOpenfdaNdc.brand_name,
                    RawOpenfdaNdc.generic_name,
                    RawOpenfdaNdc.as_of_date,
                )
                .where(RawOpenfdaNdc.package_ndc11 == row["ndc11"])
                .order_by(desc(RawOpenfdaNdc.as_of_date))
                .limit(1)
            )
            if as_of_date:
                openfda_detail_stmt = openfda_detail_stmt.where(RawOpenfdaNdc.as_of_date == as_of_date)
            openfda_detail = session.execute(openfda_detail_stmt).first()
            if openfda_detail:
                row["brand_name"] = row["brand_name"] or openfda_detail.brand_name
                row["generic_name"] = row["generic_name"] or openfda_detail.generic_name
                row["as_of_date"] = row["as_of_date"] or openfda_detail.as_of_date

        if row["latest_nadac_price"] is None or row["latest_effective_date"] is None:
            nadac_detail_stmt: Select = (
                select(
                    RawNadac.ndc_description,
                    RawNadac.nadac_price,
                    RawNadac.effective_date,
                    RawNadac.as_of_date,
                )
                .where(RawNadac.ndc11 == row["ndc11"])
                .order_by(desc(RawNadac.as_of_date), desc(RawNadac.effective_date))
                .limit(1)
            )
            if as_of_date:
                nadac_detail_stmt = nadac_detail_stmt.where(RawNadac.as_of_date == as_of_date)
            nadac_detail = session.execute(nadac_detail_stmt).first()
            if nadac_detail:
                row["ndc_description"] = row["ndc_description"] or nadac_detail.ndc_description
                row["latest_nadac_price"] = row["latest_nadac_price"] or nadac_detail.nadac_price
                row["latest_effective_date"] = (
                    row["latest_effective_date"] or nadac_detail.effective_date
                )
                row["as_of_date"] = row["as_of_date"] or nadac_detail.as_of_date

    return list(results.values())[:limit]


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


def _monthly_history_for_prediction(session: Session, ndc11: str) -> list[dict]:
    history = get_nadac_pricing_history(session, ndc11)
    monthly_groups: dict[str, list[Decimal]] = {}
    for row in history:
        if row["effective_date"] is None or row["nadac_price"] is None:
            continue
        month_key = row["effective_date"].strftime("%Y-%m")
        monthly_groups.setdefault(month_key, []).append(Decimal(row["nadac_price"]))

    return [
        {
            "month": f"{month_key}-01",
            "average_price": sum(prices) / Decimal(len(prices)),
        }
        for month_key, prices in sorted(monthly_groups.items())
    ]


def _prediction_summary(predictions: tuple[dict, ...]) -> dict:
    if not predictions:
        return {}

    predicted_prices = [Decimal(row["predicted_price"]) for row in predictions]
    first_price = predicted_prices[0]
    last_price = predicted_prices[-1]
    total_change = last_price - first_price
    total_change_pct = (total_change / first_price) * Decimal("100") if first_price != 0 else None

    return {
        "min_price": min(predicted_prices),
        "max_price": max(predicted_prices),
        "average_price": sum(predicted_prices) / Decimal(len(predicted_prices)),
        "median_price": Decimal(str(median(predicted_prices))),
        "price_range": max(predicted_prices) - min(predicted_prices),
        "first_price": first_price,
        "last_price": last_price,
        "total_change": total_change,
        "total_change_pct": total_change_pct,
    }


def get_ndc_price_prediction(
    session: Session,
    ndc11: str,
    months: int = 12,
    model: str = "lightgbm",
) -> dict:
    normalized = _normalized_ndc11(ndc11)
    model_key = model.lower()
    monthly_history = _monthly_history_for_prediction(session, normalized)
    if model_key == "lightgbm":
        predictions = forecast_lightgbm(monthly_history, months)
    elif model_key == "arima":
        predictions = forecast_arima(monthly_history, months)
    else:
        raise ValueError(f"Unsupported prediction model: {model}")

    return {
        "ndc11": normalized,
        "months": months,
        "model": model_key,
        "model_name": MODEL_LABELS[model_key],
        "summary": _prediction_summary(predictions),
        "predictions": list(predictions),
    }
