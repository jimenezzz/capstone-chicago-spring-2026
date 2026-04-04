"""Add user accounts for authentication and authorization."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_auth_users"
down_revision: Union[str, None] = "0002_cms_units_text"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_account",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_system_account", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("username", name="uq_user_account_username"),
    )
    op.create_index("ix_user_account_username", "user_account", ["username"])
    op.create_index("ix_user_account_role", "user_account", ["role"])


def downgrade() -> None:
    op.drop_index("ix_user_account_role", table_name="user_account")
    op.drop_index("ix_user_account_username", table_name="user_account")
    op.drop_table("user_account")
