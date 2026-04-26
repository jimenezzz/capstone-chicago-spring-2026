import json
import warnings
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd


MODEL_LABELS = {
    "lightgbm": "LightGBM",
    "arima": "ARIMA(1,1,1) NADAC time-series model",
}

MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "nadac_forecast"
LIGHTGBM_MODEL_PATH = MODEL_DIR / "lightgbm_model.pkl"
LIGHTGBM_META_PATH = MODEL_DIR / "feature_metadata.json"


def _month_end(value: date | str | pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(value).to_period("M").to_timestamp("M")


def prepare_monthly_history(monthly_rows: list[dict]) -> pd.DataFrame:
    history_df = pd.DataFrame(
        [
            {"month": row["month"], "NADAC Per Unit": float(row["average_price"])}
            for row in monthly_rows
            if row.get("month") and row.get("average_price") is not None
        ]
    )
    if history_df.empty:
        return pd.DataFrame(columns=["month", "NADAC Per Unit"])

    history_df["month"] = pd.to_datetime(history_df["month"]).map(_month_end)
    history_df["NADAC Per Unit"] = pd.to_numeric(history_df["NADAC Per Unit"], errors="coerce")
    history_df = history_df.dropna(subset=["month", "NADAC Per Unit"])
    history_df = history_df.groupby("month", as_index=False).last()
    history_df = history_df.sort_values("month").reset_index(drop=True)

    full_idx = pd.date_range(
        start=history_df["month"].min(),
        end=history_df["month"].max(),
        freq="ME",
    )
    history_df = (
        history_df.set_index("month")
        .reindex(full_idx)
        .ffill()
        .reset_index()
        .rename(columns={"index": "month"})
    )
    return history_df


def _decimal_price(value: float) -> Decimal:
    return Decimal(str(round(max(0.0, float(value)), 6)))


def _format_forecast(results: list[dict]) -> tuple[dict, ...]:
    return tuple(
        {
            "month": int(row["month"]),
            "target_month": _month_end(row["target_month"]).date()
            if row.get("target_month") is not None
            else None,
            "predicted_price": _decimal_price(row["predicted_price"]),
        }
        for row in results
    )


@lru_cache(maxsize=1)
def _load_lightgbm_assets():
    try:
        import joblib
    except ImportError as exc:
        raise RuntimeError("LightGBM model dependency joblib is not installed") from exc

    if not LIGHTGBM_MODEL_PATH.exists() or not LIGHTGBM_META_PATH.exists():
        raise RuntimeError("LightGBM model artifacts are missing")

    try:
        model = joblib.load(LIGHTGBM_MODEL_PATH)
    except Exception as exc:
        raise RuntimeError("LightGBM model could not be loaded") from exc

    with open(LIGHTGBM_META_PATH) as metadata_file:
        meta = json.load(metadata_file)
    return model, meta["features"], meta["lags"]


def _forecast_lightgbm_uncached(history_df: pd.DataFrame, steps: int) -> tuple[dict, ...]:
    if len(history_df) < 12:
        raise ValueError("LightGBM model needs at least 12 months of NADAC history")

    model, feature_columns, lags = _load_lightgbm_assets()
    known = {
        row["month"]: float(row["NADAC Per Unit"])
        for _, row in history_df.iterrows()
    }
    last_month = max(known.keys())
    future_months = pd.date_range(
        start=last_month + pd.offsets.MonthEnd(1),
        periods=steps,
        freq="ME",
    )

    results = []
    for index, target_month in enumerate(future_months, start=1):
        feature_dict = {}

        for lag in lags:
            lag_month = target_month - pd.offsets.MonthEnd(lag)
            if lag_month not in known:
                raise ValueError(
                    f"Missing lag month {lag_month.strftime('%Y-%m')} "
                    f"for forecast month {target_month.strftime('%Y-%m')}"
                )
            feature_dict[f"lag_{lag}"] = known[lag_month]

        vals_3 = [known[target_month - pd.offsets.MonthEnd(lag)] for lag in range(1, 4)]
        vals_6 = [known[target_month - pd.offsets.MonthEnd(lag)] for lag in range(1, 7)]
        feature_dict["roll_mean_3"] = float(np.mean(vals_3))
        feature_dict["roll_mean_6"] = float(np.mean(vals_6))
        feature_dict["roll_std_6"] = float(np.std(vals_6, ddof=1))
        feature_dict["month_num"] = int(target_month.month)

        x_pred = pd.DataFrame([feature_dict], columns=feature_columns)
        try:
            delta = float(model.predict(x_pred)[0])
        except Exception as exc:
            raise RuntimeError("LightGBM model could not generate a forecast") from exc
        previous_month = target_month - pd.offsets.MonthEnd(1)
        pred_price = known[previous_month] + delta

        results.append(
            {
                "month": index,
                "target_month": target_month,
                "predicted_price": pred_price,
            }
        )
        known[target_month] = pred_price

    return _format_forecast(results)


def forecast_lightgbm(monthly_rows: list[dict], steps: int) -> tuple[dict, ...]:
    history_df = prepare_monthly_history(monthly_rows)
    return _forecast_lightgbm_uncached(history_df, steps)


def forecast_arima(monthly_rows: list[dict], steps: int) -> tuple[dict, ...]:
    history_df = prepare_monthly_history(monthly_rows)
    if len(history_df) < 3:
        raise ValueError("ARIMA model needs at least 3 months of NADAC history")

    try:
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError as exc:
        raise RuntimeError("ARIMA model dependency statsmodels is not installed") from exc

    series = pd.Series(
        history_df["NADAC Per Unit"].astype(float).to_numpy(),
        index=pd.DatetimeIndex(history_df["month"]),
    ).asfreq("ME")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            fit = ARIMA(series, order=(1, 1, 1)).fit()
            forecast = fit.forecast(steps=steps)
        except Exception as exc:
            raise RuntimeError("ARIMA model could not generate a forecast") from exc

    last_month = history_df["month"].max()
    future_months = pd.date_range(
        start=last_month + pd.offsets.MonthEnd(1),
        periods=steps,
        freq="ME",
    )
    return _format_forecast(
        [
            {
                "month": index,
                "target_month": target_month,
                "predicted_price": forecast_value,
            }
            for index, (target_month, forecast_value) in enumerate(
                zip(future_months, forecast, strict=True),
                start=1,
            )
        ]
    )
