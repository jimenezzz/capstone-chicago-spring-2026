from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class VolatilityThresholdResponse(BaseModel):
    threshold_pct: Decimal = Field(ge=0)
    moderate_risk_months: int = Field(ge=1)
    high_risk_months: int = Field(ge=1)


class UpdateVolatilityThresholdRequest(BaseModel):
    threshold_pct: Decimal = Field(ge=0, le=1000)
    moderate_risk_months: int = Field(ge=1, le=120)
    high_risk_months: int = Field(ge=1, le=120)

    @model_validator(mode="after")
    def validate_risk_cutoffs(self) -> "UpdateVolatilityThresholdRequest":
        if self.high_risk_months <= self.moderate_risk_months:
            raise ValueError("High Risk months must be greater than Moderate Risk months")
        return self
