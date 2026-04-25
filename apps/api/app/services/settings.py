from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.db.models import AppSetting


VOLATILITY_THRESHOLD_KEY = "nadac_volatility_threshold_pct"
MODERATE_RISK_MONTHS_KEY = "nadac_moderate_risk_months"
HIGH_RISK_MONTHS_KEY = "nadac_high_risk_months"
DEFAULT_VOLATILITY_THRESHOLD_PCT = Decimal("5")
DEFAULT_MODERATE_RISK_MONTHS = 1
DEFAULT_HIGH_RISK_MONTHS = 3


def _get_numeric_setting(db: Session, key: str) -> Decimal | None:
    setting = db.scalar(select(AppSetting).where(AppSetting.key == key))
    if setting is None or setting.numeric_value is None:
        return None
    return Decimal(str(setting.numeric_value))


def _set_numeric_setting(db: Session, key: str, value: Decimal | int, description: str) -> None:
    setting = db.get(AppSetting, key)
    if setting is None:
        setting = AppSetting(
            key=key,
            description=description,
        )
    setting.numeric_value = Decimal(str(value))
    db.add(setting)


def get_volatility_threshold_pct(db: Session) -> Decimal:
    return _get_numeric_setting(db, VOLATILITY_THRESHOLD_KEY) or DEFAULT_VOLATILITY_THRESHOLD_PCT


def get_volatility_risk_settings(db: Session) -> dict:
    threshold_pct = get_volatility_threshold_pct(db)
    moderate_risk_months = _get_numeric_setting(db, MODERATE_RISK_MONTHS_KEY)
    high_risk_months = _get_numeric_setting(db, HIGH_RISK_MONTHS_KEY)
    return {
        "threshold_pct": threshold_pct,
        "moderate_risk_months": (
            int(moderate_risk_months)
            if moderate_risk_months is not None
            else DEFAULT_MODERATE_RISK_MONTHS
        ),
        "high_risk_months": (
            int(high_risk_months) if high_risk_months is not None else DEFAULT_HIGH_RISK_MONTHS
        ),
    }


def set_volatility_risk_settings(
    db: Session,
    *,
    threshold_pct: Decimal,
    moderate_risk_months: int,
    high_risk_months: int,
) -> dict:
    _set_numeric_setting(
        db,
        VOLATILITY_THRESHOLD_KEY,
        threshold_pct,
        "Percent change threshold for monthly NADAC volatility risk analytics.",
    )
    _set_numeric_setting(
        db,
        MODERATE_RISK_MONTHS_KEY,
        moderate_risk_months,
        "Volatile month count where NADAC stability becomes Moderate Risk.",
    )
    _set_numeric_setting(
        db,
        HIGH_RISK_MONTHS_KEY,
        high_risk_months,
        "Volatile month count where NADAC stability becomes High Risk.",
    )
    db.commit()
    return get_volatility_risk_settings(db)
