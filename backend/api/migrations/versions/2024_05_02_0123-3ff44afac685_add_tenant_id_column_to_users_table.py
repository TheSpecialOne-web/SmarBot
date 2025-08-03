"""add_tenant_id_column_to_users_table

Revision ID: 3ff44afac685
Revises: d0b3112d377c
Create Date: 2024-05-02 01:23:32.329943

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "3ff44afac685"
down_revision = "d0b3112d377c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", onupdate="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "roles",
            pg.ARRAY(pg.VARCHAR(255)),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "roles")
    op.drop_column("users", "tenant_id")
