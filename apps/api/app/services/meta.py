from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.db.models import IngestionRun


def get_as_of_dates(session: Session) -> list[dict]:
    stmt = (
        select(IngestionRun.source_name, func.max(IngestionRun.as_of_date).label("as_of_date"))
        .where(IngestionRun.status == "success")
        .group_by(IngestionRun.source_name)
        .order_by(IngestionRun.source_name)
    )
    rows = session.execute(stmt).all()
    return [{"source_name": row.source_name, "as_of_date": row.as_of_date} for row in rows]
