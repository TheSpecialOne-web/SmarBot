"""create status column to question answers table

Revision ID: 00eafde39dbe
Revises: 26008f8704fa
Create Date: 2024-08-01 02:04:28.045193

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "00eafde39dbe"
down_revision = "26008f8704fa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    question_answer_status = pg.ENUM("pending", "indexed", name="question_answer_status", create_type=False)
    question_answer_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "question_answers",
        sa.Column("status", question_answer_status, server_default="pending"),
    )


def downgrade() -> None:
    op.drop_column("question_answers", "status")
    op.execute("DROP TYPE question_answer_status")
