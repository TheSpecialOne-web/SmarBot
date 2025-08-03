"""add constraint to workflow_thread_flow_steps table

Revision ID: 1a849649b9a1
Revises: ae40bed28fb3
Create Date: 2025-01-23 07:40:14.212707

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "1a849649b9a1"
down_revision = "ae40bed28fb3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add a partial unique index
    op.create_index(
        "uq_workflow_thread_flow_steps_active",
        "workflow_thread_flow_steps",
        ["workflow_thread_flow_id", "step"],
        unique=True,
        postgresql_where=sa.text("is_active = TRUE"),
    )


def downgrade() -> None:
    # Drop the unique index
    op.drop_index("uq_workflow_thread_flow_steps_active", table_name="workflow_thread_flow_steps")
