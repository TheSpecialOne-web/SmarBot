"""delete sender_id from notifications table

Revision ID: 51e9cdbfc26f
Revises: b25140d27f13
Create Date: 2024-05-16 09:16:43.783204

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "51e9cdbfc26f"
down_revision = "b25140d27f13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("notifications", "sender_id")


def downgrade() -> None:
    op.add_column("notifications", sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False))
