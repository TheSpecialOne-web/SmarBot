"""add model_name columns

Revision ID: b09220947e6c
Revises: f6e0a9d2ac6d
Create Date: 2023-10-12 14:09:20.885428

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "b09220947e6c"
down_revision = "f6e0a9d2ac6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chat_logs", sa.Column("query_generator_model", pg.VARCHAR(511), nullable=True))
    op.add_column("chat_logs", sa.Column("output_generator_model", pg.VARCHAR(511), nullable=True))
    op.add_column(
        "bots", sa.Column("query_generator_model", pg.VARCHAR(511), nullable=True, server_default="gpt-3.5-turbo")
    )
    op.add_column(
        "bots", sa.Column("output_generator_model", pg.VARCHAR(511), nullable=True, server_default="gpt-3.5-turbo")
    )


def downgrade() -> None:
    op.drop_column("chat_logs", "query_generator_model")
    op.drop_column("chat_logs", "output_generator_model")
    op.drop_column("bots", "query_generator_model")
    op.drop_column("bots", "output_generator_model")
