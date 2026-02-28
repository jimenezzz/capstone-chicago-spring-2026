from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.db.session import get_db
from apps.api.app.schemas.common import AsOfDateItem
from apps.api.app.services.meta import get_as_of_dates

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/as-of-dates", response_model=list[AsOfDateItem])
def as_of_dates(db: Session = Depends(get_db)) -> list[AsOfDateItem]:
    return [AsOfDateItem(**row) for row in get_as_of_dates(db)]
