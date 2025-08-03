"""add type and url to datapoints

Revision ID: 0e1d85d6057b
Revises: 8dcc443bd9e7
Create Date: 2024-04-04 01:32:51.167232

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0e1d85d6057b"
down_revision = "8dcc443bd9e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conversation_data_points", sa.Column("url", sa.Text, nullable=True))
    op.add_column(
        "conversation_data_points", sa.Column("type", sa.String(255), nullable=False, server_default="internal")
    )


def downgrade() -> None:
    op.drop_column("conversation_data_points", "url")
    op.drop_column("conversation_data_points", "type")
