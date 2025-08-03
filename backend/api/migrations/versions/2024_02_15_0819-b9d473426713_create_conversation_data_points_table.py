"""create conversation data points table

Revision ID: b9d473426713
Revises: 72c6bcead839
Create Date: 2024-02-15 08:19:51.545828

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "b9d473426713"
down_revision = "72c6bcead839"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversation_data_points",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "turn_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("conversation_turns.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("cite_number", pg.INTEGER, nullable=False),
        sa.Column("chunk_name", pg.TEXT, nullable=False),
        sa.Column("content", pg.VARCHAR(1023), nullable=False),
        sa.Column("blob_path", pg.VARCHAR(1023), nullable=False),
        sa.Column("page_number", pg.INTEGER, nullable=False),
        sa.Column("additional_info", pg.JSON, nullable=True),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("conversation_data_points")
