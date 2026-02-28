"""Initial schema for Pharmaceutical Economic Data Hub."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingestion_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("dataset_version", sa.String(length=120), nullable=True),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_ingestion_run_source_name", "ingestion_run", ["source_name"])
    op.create_index("ix_ingestion_run_as_of_date", "ingestion_run", ["as_of_date"])
    op.create_index("ix_ingestion_run_ingested_at", "ingestion_run", ["ingested_at"])
    op.create_index("ix_ingestion_run_status", "ingestion_run", ["status"])
    op.create_index("ix_ingestion_run_file_hash", "ingestion_run", ["file_hash"])

    op.create_table(
        "raw_nadac",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("source_row", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ndc_raw", sa.String(length=32), nullable=True),
        sa.Column("ndc11", sa.String(length=11), nullable=True),
        sa.Column("nadac_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("ndc_description", sa.Text(), nullable=True),
    )
    op.create_index("ix_raw_nadac_ingestion_run_id", "raw_nadac", ["ingestion_run_id"])
    op.create_index("ix_raw_nadac_as_of_date", "raw_nadac", ["as_of_date"])
    op.create_index("ix_raw_nadac_ndc11", "raw_nadac", ["ndc11"])
    op.create_index("ix_raw_nadac_effective_date", "raw_nadac", ["effective_date"])
    op.create_index("ix_raw_nadac_ndc11_as_of", "raw_nadac", ["ndc11", "as_of_date"])

    op.create_table(
        "raw_orange_book_products",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("source_row", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("application_number", sa.String(length=32), nullable=True),
        sa.Column("application_number_norm", sa.String(length=32), nullable=True),
        sa.Column("te_code", sa.String(length=16), nullable=True),
        sa.Column("ingredient", sa.Text(), nullable=True),
        sa.Column("trade_name", sa.Text(), nullable=True),
    )
    op.create_index("ix_raw_ob_ingestion_run_id", "raw_orange_book_products", ["ingestion_run_id"])
    op.create_index("ix_raw_ob_as_of_date", "raw_orange_book_products", ["as_of_date"])
    op.create_index("ix_raw_ob_application_number", "raw_orange_book_products", ["application_number"])
    op.create_index("ix_raw_ob_application_number_norm", "raw_orange_book_products", ["application_number_norm"])
    op.create_index("ix_raw_ob_te_code", "raw_orange_book_products", ["te_code"])

    op.create_table(
        "raw_purple_book",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("source_row", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("application_number_norm", sa.String(length=32), nullable=True),
        sa.Column("bla_number", sa.String(length=32), nullable=True),
        sa.Column("proprietary_name", sa.Text(), nullable=True),
        sa.Column("proper_name", sa.Text(), nullable=True),
    )
    op.create_index("ix_raw_pb_ingestion_run_id", "raw_purple_book", ["ingestion_run_id"])
    op.create_index("ix_raw_pb_as_of_date", "raw_purple_book", ["as_of_date"])
    op.create_index("ix_raw_pb_application_number_norm", "raw_purple_book", ["application_number_norm"])

    op.create_table(
        "raw_openfda_ndc",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("source_row", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("package_ndc", sa.String(length=32), nullable=True),
        sa.Column("package_ndc11", sa.String(length=11), nullable=True),
        sa.Column("product_ndc", sa.String(length=16), nullable=True),
        sa.Column("application_number", sa.String(length=32), nullable=True),
        sa.Column("application_number_norm", sa.String(length=32), nullable=True),
        sa.Column("generic_name", sa.Text(), nullable=True),
        sa.Column("brand_name", sa.Text(), nullable=True),
    )
    op.create_index("ix_raw_openfda_ingestion_run_id", "raw_openfda_ndc", ["ingestion_run_id"])
    op.create_index("ix_raw_openfda_as_of_date", "raw_openfda_ndc", ["as_of_date"])
    op.create_index("ix_raw_openfda_package_ndc11", "raw_openfda_ndc", ["package_ndc11"])
    op.create_index("ix_raw_openfda_product_ndc", "raw_openfda_ndc", ["product_ndc"])
    op.create_index("ix_raw_openfda_application_number_norm", "raw_openfda_ndc", ["application_number_norm"])
    op.create_index("ix_raw_openfda_pkg_ndc11_as_of", "raw_openfda_ndc", ["package_ndc11", "as_of_date"])

    op.create_table(
        "raw_cms_crosswalk",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("source_row", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ndc11", sa.String(length=11), nullable=True),
        sa.Column("hcpcs", sa.String(length=16), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("long_description", sa.Text(), nullable=True),
        sa.Column("quarter", sa.String(length=32), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
    )
    op.create_index("ix_raw_cms_crosswalk_ingestion_run_id", "raw_cms_crosswalk", ["ingestion_run_id"])
    op.create_index("ix_raw_cms_crosswalk_as_of_date", "raw_cms_crosswalk", ["as_of_date"])
    op.create_index("ix_raw_cms_crosswalk_ndc11", "raw_cms_crosswalk", ["ndc11"])
    op.create_index("ix_raw_cms_crosswalk_hcpcs", "raw_cms_crosswalk", ["hcpcs"])
    op.create_index("ix_raw_cms_crosswalk_quarter", "raw_cms_crosswalk", ["quarter"])
    op.create_index("ix_raw_cms_crosswalk_effective_date", "raw_cms_crosswalk", ["effective_date"])
    op.create_index("ix_raw_cms_crosswalk_ndc11_hcpcs_as_of", "raw_cms_crosswalk", ["ndc11", "hcpcs", "as_of_date"])

    op.create_table(
        "raw_cms_asp_pricing",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("source_row", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("hcpcs", sa.String(length=16), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("payment_limit", sa.Numeric(18, 6), nullable=True),
        sa.Column("units", sa.String(length=64), nullable=True),
        sa.Column("quarter", sa.String(length=32), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
    )
    op.create_index("ix_raw_cms_pricing_ingestion_run_id", "raw_cms_asp_pricing", ["ingestion_run_id"])
    op.create_index("ix_raw_cms_pricing_as_of_date", "raw_cms_asp_pricing", ["as_of_date"])
    op.create_index("ix_raw_cms_pricing_hcpcs", "raw_cms_asp_pricing", ["hcpcs"])
    op.create_index("ix_raw_cms_pricing_payment_limit", "raw_cms_asp_pricing", ["payment_limit"])
    op.create_index("ix_raw_cms_pricing_quarter", "raw_cms_asp_pricing", ["quarter"])
    op.create_index("ix_raw_cms_pricing_effective_date", "raw_cms_asp_pricing", ["effective_date"])
    op.create_index("ix_raw_cms_pricing_hcpcs_as_of", "raw_cms_asp_pricing", ["hcpcs", "as_of_date"])

    op.create_table(
        "drug",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("generic_name", sa.Text(), nullable=True),
        sa.Column("brand_name", sa.Text(), nullable=True),
    )

    op.create_table(
        "applicant",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("applicant_name", sa.Text(), nullable=True),
        sa.Column("applicant_number", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_applicant_applicant_number", "applicant", ["applicant_number"])

    op.create_table(
        "te_code",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_te_code_code"),
    )
    op.create_index("ix_te_code_code", "te_code", ["code"])

    op.create_table(
        "ndc_product",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_ndc", sa.String(length=16), nullable=False),
        sa.Column("drug_id", sa.Integer(), sa.ForeignKey("drug.id"), nullable=True),
        sa.UniqueConstraint("product_ndc", name="uq_ndc_product_product_ndc"),
    )
    op.create_index("ix_ndc_product_product_ndc", "ndc_product", ["product_ndc"])
    op.create_index("ix_ndc_product_drug_id", "ndc_product", ["drug_id"])

    op.create_table(
        "ndc_package",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ndc11", sa.String(length=11), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("ndc_product.id"), nullable=True),
        sa.Column("package_desc", sa.Text(), nullable=True),
        sa.UniqueConstraint("ndc11", name="uq_ndc_package_ndc11"),
    )
    op.create_index("ix_ndc_package_ndc11", "ndc_package", ["ndc11"])
    op.create_index("ix_ndc_package_product_id", "ndc_package", ["product_id"])

    op.create_table(
        "pricing_nadac",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ndc11", sa.String(length=11), nullable=False),
        sa.Column("price", sa.Numeric(18, 6), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_run.id"), nullable=True),
    )
    op.create_index("ix_pricing_nadac_ndc11", "pricing_nadac", ["ndc11"])
    op.create_index("ix_pricing_nadac_effective_date", "pricing_nadac", ["effective_date"])
    op.create_index("ix_pricing_nadac_ingestion_run_id", "pricing_nadac", ["ingestion_run_id"])


def downgrade() -> None:
    op.drop_index("ix_pricing_nadac_ingestion_run_id", table_name="pricing_nadac")
    op.drop_index("ix_pricing_nadac_effective_date", table_name="pricing_nadac")
    op.drop_index("ix_pricing_nadac_ndc11", table_name="pricing_nadac")
    op.drop_table("pricing_nadac")

    op.drop_index("ix_ndc_package_product_id", table_name="ndc_package")
    op.drop_index("ix_ndc_package_ndc11", table_name="ndc_package")
    op.drop_table("ndc_package")

    op.drop_index("ix_ndc_product_drug_id", table_name="ndc_product")
    op.drop_index("ix_ndc_product_product_ndc", table_name="ndc_product")
    op.drop_table("ndc_product")

    op.drop_index("ix_te_code_code", table_name="te_code")
    op.drop_table("te_code")

    op.drop_index("ix_applicant_applicant_number", table_name="applicant")
    op.drop_table("applicant")

    op.drop_table("drug")

    op.drop_index("ix_raw_cms_pricing_hcpcs_as_of", table_name="raw_cms_asp_pricing")
    op.drop_index("ix_raw_cms_pricing_effective_date", table_name="raw_cms_asp_pricing")
    op.drop_index("ix_raw_cms_pricing_quarter", table_name="raw_cms_asp_pricing")
    op.drop_index("ix_raw_cms_pricing_payment_limit", table_name="raw_cms_asp_pricing")
    op.drop_index("ix_raw_cms_pricing_hcpcs", table_name="raw_cms_asp_pricing")
    op.drop_index("ix_raw_cms_pricing_as_of_date", table_name="raw_cms_asp_pricing")
    op.drop_index("ix_raw_cms_pricing_ingestion_run_id", table_name="raw_cms_asp_pricing")
    op.drop_table("raw_cms_asp_pricing")

    op.drop_index("ix_raw_cms_crosswalk_ndc11_hcpcs_as_of", table_name="raw_cms_crosswalk")
    op.drop_index("ix_raw_cms_crosswalk_effective_date", table_name="raw_cms_crosswalk")
    op.drop_index("ix_raw_cms_crosswalk_quarter", table_name="raw_cms_crosswalk")
    op.drop_index("ix_raw_cms_crosswalk_hcpcs", table_name="raw_cms_crosswalk")
    op.drop_index("ix_raw_cms_crosswalk_ndc11", table_name="raw_cms_crosswalk")
    op.drop_index("ix_raw_cms_crosswalk_as_of_date", table_name="raw_cms_crosswalk")
    op.drop_index("ix_raw_cms_crosswalk_ingestion_run_id", table_name="raw_cms_crosswalk")
    op.drop_table("raw_cms_crosswalk")

    op.drop_index("ix_raw_openfda_pkg_ndc11_as_of", table_name="raw_openfda_ndc")
    op.drop_index("ix_raw_openfda_application_number_norm", table_name="raw_openfda_ndc")
    op.drop_index("ix_raw_openfda_product_ndc", table_name="raw_openfda_ndc")
    op.drop_index("ix_raw_openfda_package_ndc11", table_name="raw_openfda_ndc")
    op.drop_index("ix_raw_openfda_as_of_date", table_name="raw_openfda_ndc")
    op.drop_index("ix_raw_openfda_ingestion_run_id", table_name="raw_openfda_ndc")
    op.drop_table("raw_openfda_ndc")

    op.drop_index("ix_raw_pb_application_number_norm", table_name="raw_purple_book")
    op.drop_index("ix_raw_pb_as_of_date", table_name="raw_purple_book")
    op.drop_index("ix_raw_pb_ingestion_run_id", table_name="raw_purple_book")
    op.drop_table("raw_purple_book")

    op.drop_index("ix_raw_ob_te_code", table_name="raw_orange_book_products")
    op.drop_index("ix_raw_ob_application_number_norm", table_name="raw_orange_book_products")
    op.drop_index("ix_raw_ob_application_number", table_name="raw_orange_book_products")
    op.drop_index("ix_raw_ob_as_of_date", table_name="raw_orange_book_products")
    op.drop_index("ix_raw_ob_ingestion_run_id", table_name="raw_orange_book_products")
    op.drop_table("raw_orange_book_products")

    op.drop_index("ix_raw_nadac_ndc11_as_of", table_name="raw_nadac")
    op.drop_index("ix_raw_nadac_effective_date", table_name="raw_nadac")
    op.drop_index("ix_raw_nadac_ndc11", table_name="raw_nadac")
    op.drop_index("ix_raw_nadac_as_of_date", table_name="raw_nadac")
    op.drop_index("ix_raw_nadac_ingestion_run_id", table_name="raw_nadac")
    op.drop_table("raw_nadac")

    op.drop_index("ix_ingestion_run_file_hash", table_name="ingestion_run")
    op.drop_index("ix_ingestion_run_status", table_name="ingestion_run")
    op.drop_index("ix_ingestion_run_ingested_at", table_name="ingestion_run")
    op.drop_index("ix_ingestion_run_as_of_date", table_name="ingestion_run")
    op.drop_index("ix_ingestion_run_source_name", table_name="ingestion_run")
    op.drop_table("ingestion_run")
