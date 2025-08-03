"""add image generator model to bots and conversation turns

Revision ID: 0b275ec1d9b8
Revises: 7306308d967b
Create Date: 2024-06-15 00:08:11.972155

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "0b275ec1d9b8"
down_revision = "7306308d967b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bots",
        sa.Column("image_generator_model", pg.VARCHAR(511), nullable=True),
    )
    op.add_column(
        "conversation_turns",
        sa.Column("image_generator_model", pg.VARCHAR(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bots", "image_generator_model")
    op.drop_column("conversation_turns", "image_generator_model")
