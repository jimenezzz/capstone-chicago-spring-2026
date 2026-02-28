from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db.base import Base


class RawBaseMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingestion_run.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source_row: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RawNadac(RawBaseMixin, Base):
    __tablename__ = "raw_nadac"

    ndc_raw: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ndc11: Mapped[str | None] = mapped_column(String(11), nullable=True, index=True)
    nadac_price: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    ndc_description: Mapped[str | None] = mapped_column(Text, nullable=True)


class RawOrangeBookProducts(RawBaseMixin, Base):
    __tablename__ = "raw_orange_book_products"

    application_number: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    application_number_norm: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    te_code: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    ingredient: Mapped[str | None] = mapped_column(Text, nullable=True)
    trade_name: Mapped[str | None] = mapped_column(Text, nullable=True)


class RawPurpleBook(RawBaseMixin, Base):
    __tablename__ = "raw_purple_book"

    application_number_norm: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    bla_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    proprietary_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    proper_name: Mapped[str | None] = mapped_column(Text, nullable=True)


class RawOpenfdaNdc(RawBaseMixin, Base):
    __tablename__ = "raw_openfda_ndc"

    package_ndc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    package_ndc11: Mapped[str | None] = mapped_column(String(11), nullable=True, index=True)
    product_ndc: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    application_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    application_number_norm: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    generic_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand_name: Mapped[str | None] = mapped_column(Text, nullable=True)


class RawCmsCrosswalk(RawBaseMixin, Base):
    __tablename__ = "raw_cms_crosswalk"

    ndc11: Mapped[str | None] = mapped_column(String(11), nullable=True, index=True)
    hcpcs: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quarter: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)


class RawCmsAspPricing(RawBaseMixin, Base):
    __tablename__ = "raw_cms_asp_pricing"

    hcpcs: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_limit: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True, index=True)
    units: Mapped[str | None] = mapped_column(Text, nullable=True)
    quarter: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)


Index("ix_raw_nadac_ndc11_as_of", RawNadac.ndc11, RawNadac.as_of_date)
Index("ix_raw_openfda_pkg_ndc11_as_of", RawOpenfdaNdc.package_ndc11, RawOpenfdaNdc.as_of_date)
Index("ix_raw_cms_crosswalk_ndc11_hcpcs_as_of", RawCmsCrosswalk.ndc11, RawCmsCrosswalk.hcpcs, RawCmsCrosswalk.as_of_date)
Index("ix_raw_cms_pricing_hcpcs_as_of", RawCmsAspPricing.hcpcs, RawCmsAspPricing.as_of_date)
