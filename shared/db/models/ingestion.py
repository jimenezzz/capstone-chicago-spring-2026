import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db.base import Base


class IngestionRun(Base):
    __tablename__ = "ingestion_run"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dataset_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="started", index=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
