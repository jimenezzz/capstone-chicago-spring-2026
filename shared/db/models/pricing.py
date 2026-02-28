from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db.base import Base


class PricingNadac(Base):
    __tablename__ = "pricing_nadac"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ndc11: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    ingestion_run_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingestion_run.id"), nullable=True, index=True
    )
