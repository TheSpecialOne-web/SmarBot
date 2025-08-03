"""add status column to documents table

Revision ID: 85ee71cd37a9
Revises: c43957229095
Create Date: 2024-04-12 05:48:22.695161

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "85ee71cd37a9"
down_revision = "c43957229095"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "status",
            sa.VARCHAR(255),
            nullable=False,
            server_default="pending",
        ),
    )
    op.alter_column("documents", "can_search", nullable=True)


def downgrade() -> None:
    op.alter_column("documents", "can_search", nullable=False)
    op.drop_column("documents", "status")
