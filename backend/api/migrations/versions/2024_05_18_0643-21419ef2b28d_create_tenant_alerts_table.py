"""create tenant_alerts table

Revision ID: 21419ef2b28d
Revises: 51e9cdbfc26f
Create Date: 2024-05-18 06:43:37.790391

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "21419ef2b28d"
down_revision = "51e9cdbfc26f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_alerts",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", onupdate="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
        sa.Column("last_token_alerted_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("last_storage_alerted_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("last_ocr_alerted_at", pg.TIMESTAMP, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("tenant_alerts")
