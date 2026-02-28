from datetime import date

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class AsOfDateItem(BaseModel):
    source_name: str
    as_of_date: date
