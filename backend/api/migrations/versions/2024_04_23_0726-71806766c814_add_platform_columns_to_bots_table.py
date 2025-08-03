"""add platform columns to bots table

Revision ID: 71806766c814
Revises: be52b3f7c89e
Create Date: 2024-04-23 07:26:15.669013

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "71806766c814"
down_revision = "be52b3f7c89e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("query_generator_platform", sa.VARCHAR(255), nullable=True))
    op.add_column(
        "bots", sa.Column("response_generator_platform", sa.VARCHAR(255), nullable=False, server_default="azure")
    )


def downgrade() -> None:
    op.drop_column("bots", "query_generator_platform")
    op.drop_column("bots", "response_generator_platform")
