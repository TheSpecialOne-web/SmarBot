"""add question_answer id to conversation data points

Revision ID: 19e0c54f8252
Revises: b3ce32b99ab3
Create Date: 2024-06-01 11:39:10.559201

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "19e0c54f8252"
down_revision = "b3ce32b99ab3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversation_data_points",
        sa.Column(
            "question_answer_id",
            pg.UUID,
            sa.ForeignKey("question_answers.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("conversation_data_points", "question_answer_id")
