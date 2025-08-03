"""create users_policies table

Revision ID: 4b8216f16a35
Revises: b06acbe52663
Create Date: 2023-08-24 08:07:00.594676

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "4b8216f16a35"
down_revision = "b06acbe52663"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users_policies",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column("user_id", pg.INTEGER, nullable=False),
        sa.Column("bot_id", pg.INTEGER, nullable=False),
        sa.Column("action", pg.ENUM("read", "write", name="users_policies_action"), nullable=False),
    )
    op.create_foreign_key("fk_users_policies_user_id_users_id", "users_policies", "users", ["user_id"], ["id"])
    op.create_foreign_key("fk_users_policies_bot_id_bots_id", "users_policies", "bots", ["bot_id"], ["id"])


def downgrade() -> None:
    op.drop_table("users_policies")
