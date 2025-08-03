"""create prompt_templates table

Revision ID: f01545c22b3d
Revises: 77faa14d3cbf
Create Date: 2024-01-10 13:07:45.856789

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "f01545c22b3d"
down_revision = "77faa14d3cbf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("prompt_templates")
