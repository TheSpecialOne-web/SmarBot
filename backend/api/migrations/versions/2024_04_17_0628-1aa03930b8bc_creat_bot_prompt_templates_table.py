"""creat bot_prompt_templates table

Revision ID: 1aa03930b8bc
Revises: 1cc2c17335e5
Create Date: 2024-04-17 06:28:05.102903

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "1aa03930b8bc"
down_revision = "1cc2c17335e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bot_prompt_templates",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "bot_id",
            sa.Integer,
            sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("bot_prompt_templates")
