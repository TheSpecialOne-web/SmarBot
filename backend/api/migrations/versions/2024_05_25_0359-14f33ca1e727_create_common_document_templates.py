"""create common_document_templates

Revision ID: 14f33ca1e727
Revises: 90fa83a4c1d8
Create Date: 2024-05-25 03:59:59.844742

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "14f33ca1e727"
down_revision = "90fa83a4c1d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "common_document_templates",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("bot_template_id", pg.UUID(as_uuid=True), sa.ForeignKey("bot_templates.id"), nullable=False),
        sa.Column("basename", sa.String(length=255), nullable=False),
        sa.Column("memo", sa.String(length=511), nullable=True),
        sa.Column("file_extension", sa.String(length=511), nullable=True),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("common_document_templates")
