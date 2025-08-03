"""add document_id column to conversation_data_points table

Revision ID: 2db004f0349e
Revises: 1aa03930b8bc
Create Date: 2024-04-17 11:39:40.567858

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2db004f0349e"
down_revision = "1aa03930b8bc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversation_data_points",
        sa.Column(
            "document_id",
            sa.Integer,
            sa.ForeignKey("documents.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("conversation_data_points", "document_id")
