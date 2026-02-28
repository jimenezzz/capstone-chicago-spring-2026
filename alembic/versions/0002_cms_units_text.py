"""Alter raw_cms_asp_pricing.units to text."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_cms_units_text"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "raw_cms_asp_pricing",
        "units",
        existing_type=sa.String(length=64),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "raw_cms_asp_pricing",
        "units",
        existing_type=sa.Text(),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
