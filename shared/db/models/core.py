from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.db.base import Base


class Drug(Base):
    __tablename__ = "drug"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    generic_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand_name: Mapped[str | None] = mapped_column(Text, nullable=True)


class Applicant(Base):
    __tablename__ = "applicant"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    applicant_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicant_number: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)


class TeCode(Base):
    __tablename__ = "te_code"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class NdcProduct(Base):
    __tablename__ = "ndc_product"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_ndc: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    drug_id: Mapped[int | None] = mapped_column(ForeignKey("drug.id"), nullable=True, index=True)


class NdcPackage(Base):
    __tablename__ = "ndc_package"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ndc11: Mapped[str] = mapped_column(String(11), nullable=False, unique=True, index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("ndc_product.id"), nullable=True, index=True)
    package_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
