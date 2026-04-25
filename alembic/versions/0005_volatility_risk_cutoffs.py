"""Add configurable NADAC volatility risk month cutoffs."""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_volatility_risk_cutoffs"
down_revision: Union[str, None] = "0004_app_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO app_setting (key, numeric_value, description)
        VALUES
            (
                'nadac_moderate_risk_months',
                1,
                'Volatile month count where NADAC stability becomes Moderate Risk.'
            ),
            (
                'nadac_high_risk_months',
                3,
                'Volatile month count where NADAC stability becomes High Risk.'
            )
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM app_setting
        WHERE key IN ('nadac_moderate_risk_months', 'nadac_high_risk_months')
        """
    )
