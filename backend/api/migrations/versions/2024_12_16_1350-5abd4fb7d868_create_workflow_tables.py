"""create workflow tables

Revision ID: 5abd4fb7d868
Revises: 52753c85e63f
Create Date: 2024-12-16 13:50:38.481249

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "5abd4fb7d868"
down_revision = "52753c85e63f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflows",
        sa.Column(
            "id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id", onupdate="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("config", pg.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("workflows")
