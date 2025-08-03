"""create unique index to bots name

Revision ID: 0cae8b22acc7
Revises: d784ba1aa29d
Create Date: 2024-09-17 09:25:32.101344

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0cae8b22acc7"
down_revision = "d784ba1aa29d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "bots_name_tenant_id_idx",
        "bots",
        ["name", "tenant_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "bots_name_tenant_id_idx",
        "bots",
    )
