"""Add app settings for configurable analytics thresholds."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_app_settings"
down_revision: Union[str, None] = "0003_auth_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_setting",
        sa.Column("key", sa.String(length=80), primary_key=True),
        sa.Column("numeric_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.execute(
        """
        INSERT INTO app_setting (key, numeric_value, description)
        VALUES (
            'nadac_volatility_threshold_pct',
            5.0000,
            'Percent change threshold for monthly NADAC volatility risk analytics.'
        )
        """
    )


def downgrade() -> None:
    op.drop_table("app_setting")
