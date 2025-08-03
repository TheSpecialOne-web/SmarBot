"""create attachments table

Revision ID: 7dd4a0a6d5a9
Revises: 762c075b3d19
Create Date: 2024-02-07 13:27:21.419348

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "7dd4a0a6d5a9"
down_revision = "762c075b3d19"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attachments",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "bot_id", pg.INTEGER, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "user_id", pg.INTEGER, sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("basename", pg.VARCHAR(255), nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
        sa.Column("file_extension", pg.VARCHAR(255), nullable=False, server_default="pdf"),
    )


def downgrade() -> None:
    op.drop_table("attachments")
