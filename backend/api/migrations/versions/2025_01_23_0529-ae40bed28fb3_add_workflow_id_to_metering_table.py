"""add workflow_id to metering table

Revision ID: ae40bed28fb3
Revises: 0886b7029823
Create Date: 2025-01-23 05:29:54.959956

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ae40bed28fb3"
down_revision = "0886b7029823"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "metering",
        sa.Column("workflow_id", sa.UUID(as_uuid=True), sa.ForeignKey("workflows.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("metering", "workflow_id")
