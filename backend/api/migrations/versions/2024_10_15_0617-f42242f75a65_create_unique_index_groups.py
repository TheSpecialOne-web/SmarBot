"""create unique index groups

Revision ID: f42242f75a65
Revises: af650915a844
Create Date: 2024-10-15 06:17:20.748380

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f42242f75a65"
down_revision = "af650915a844"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "groups_tenant_id_name_idx",
        "groups",
        ["name", "tenant_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "groups_tenant_id_name_idx",
        "groups",
    )
