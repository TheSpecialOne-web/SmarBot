"""chat_completions table: delete bot_id column and add api_key_id column

Revision ID: fa823dac3d9d
Revises: 777724564a2b
Create Date: 2024-06-28 12:34:11.534483

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "fa823dac3d9d"
down_revision = "777724564a2b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("chat_completions", "bot_id")
    op.add_column(
        "chat_completions",
        sa.Column(
            "api_key_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey(
                "api_keys.id",
                onupdate="CASCADE",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("chat_completions", "api_key_id")
    op.add_column(
        "chat_completions",
        sa.Column(
            "bot_id",
            pg.INTEGER,
            sa.ForeignKey(
                "bots.id",
                onupdate="CASCADE",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
    )
