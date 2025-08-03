"""create metering table

Revision ID: b0da9a64d4dc
Revises: fa739468b21e
Create Date: 2024-04-02 10:18:26.476947

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "b0da9a64d4dc"
down_revision = "fa739468b21e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "metering",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "tenant_id",
            pg.INTEGER,
            sa.ForeignKey("tenants.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime),
    )


def downgrade() -> None:
    op.drop_table("metering")
