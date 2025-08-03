"""delete tenant_bot_idx

Revision ID: df3c62488dec
Revises: 9bb370eb4e8d
Create Date: 2024-10-10 11:43:37.043340

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "df3c62488dec"
down_revision = "9bb370eb4e8d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "bots_name_tenant_id_idx",
        "bots",
    )
    op.create_index(
        "bots_name_group_id_idx",
        "bots",
        ["name", "group_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.create_index(
        "bots_name_tenant_id_idx",
        "bots",
        ["name", "tenant_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index(
        "bots_name_group_id_idx",
        "bots",
    )
