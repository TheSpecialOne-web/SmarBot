"""create_api_keys_table

Revision ID: c66fc2456cd8
Revises: f2589876f3cb
Create Date: 2024-06-05 06:01:34.370313

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "c66fc2456cd8"
down_revision = "f2589876f3cb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("encrypted_api_key", sa.String(length=255), nullable=False),
        sa.Column("expires_at", pg.TIMESTAMP, nullable=True),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
