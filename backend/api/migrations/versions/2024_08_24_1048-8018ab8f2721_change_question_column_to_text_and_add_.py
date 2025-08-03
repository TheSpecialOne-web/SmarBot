"""change question column to text and add failed and overwriting status to question answers table

Revision ID: 8018ab8f2721
Revises: d5887fc816cc
Create Date: 2024-08-24 10:48:04.089226

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "8018ab8f2721"
down_revision = "d5887fc816cc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tmp_question_answer_status = pg.ENUM(
        "pending", "indexed", "failed", "overwriting", name="tmp_question_answer_status"
    )
    tmp_question_answer_status.create(op.get_bind(), checkfirst=True)
    op.execute("ALTER TABLE question_answers ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE question_answers ALTER COLUMN status TYPE tmp_question_answer_status USING status::text::tmp_question_answer_status"
    )
    op.execute("DROP TYPE question_answer_status")
    op.execute("ALTER TYPE tmp_question_answer_status RENAME TO question_answer_status")
    op.execute("ALTER TABLE question_answers ALTER COLUMN status SET DEFAULT 'pending'::question_answer_status")

    op.alter_column(table_name="question_answers", column_name="question", type_=pg.TEXT())


def downgrade() -> None:
    tmp_question_answer_status = pg.ENUM("pending", "indexed", name="tmp_question_answer_status")
    tmp_question_answer_status.create(op.get_bind(), checkfirst=True)
    op.execute("ALTER TABLE question_answers ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE question_answers ALTER COLUMN status TYPE tmp_question_answer_status USING status::text::tmp_question_answer_status"
    )
    op.execute("DROP TYPE question_answer_status")
    op.execute("ALTER TYPE tmp_question_answer_status RENAME TO question_answer_status")

    op.alter_column(table_name="question_answers", column_name="question", type_=sa.VARCHAR(255))
