"""alter bot output length in chat logs table

Revision ID: 77faa14d3cbf
Revises: 0ebf99a5c7a6
Create Date: 2024-01-06 08:09:36.914482

"""

from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "77faa14d3cbf"
down_revision = "0ebf99a5c7a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        table_name="chat_logs",
        column_name="user_input",
        existing_type=pg.VARCHAR(511),
        type_=pg.VARCHAR(1023),
        existing_nullable=True,
    )
    op.alter_column(
        table_name="chat_logs",
        column_name="bot_output",
        existing_type=pg.VARCHAR(511),
        type_=pg.VARCHAR(1023),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        table_name="chat_logs",
        column_name="user_input",
        existing_type=pg.VARCHAR(1023),
        type_=pg.VARCHAR(511),
        existing_nullable=True,
    )
    op.alter_column(
        table_name="chat_logs",
        column_name="bot_output",
        existing_type=pg.VARCHAR(1023),
        type_=pg.VARCHAR(511),
        existing_nullable=True,
    )
