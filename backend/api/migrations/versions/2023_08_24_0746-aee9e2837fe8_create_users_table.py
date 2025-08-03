"""create users table

Revision ID: aee9e2837fe8
Revises: d70feddb9367
Create Date: 2023-08-24 07:46:22.570890

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "aee9e2837fe8"
down_revision = "d70feddb9367"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column("name", pg.VARCHAR(255), nullable=False),
        sa.Column("email", pg.VARCHAR(255), nullable=False),
        sa.Column("auth0_id", pg.VARCHAR(255), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("users")
