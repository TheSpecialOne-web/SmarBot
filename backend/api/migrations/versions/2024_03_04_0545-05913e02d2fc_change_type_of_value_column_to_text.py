"""change type of value column to text

Revision ID: 05913e02d2fc
Revises: f811705c7dfe
Create Date: 2024-03-04 05:45:35.221497

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "05913e02d2fc"
down_revision = "74f8a4ff9113"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("approach_variables", "value", type_=sa.Text())


def downgrade() -> None:
    op.alter_column("approach_variables", "value", type_=sa.String(2047))
