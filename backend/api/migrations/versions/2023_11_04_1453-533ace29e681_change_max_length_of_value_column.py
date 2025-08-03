"""change max length of value column

Revision ID: 533ace29e681
Revises: 5ebc436ea52f
Create Date: 2023-11-04 14:53:52.281064

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "533ace29e681"
down_revision = "5ebc436ea52f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("approach_variables", "value", type_=sa.String(2047))


def downgrade() -> None:
    op.alter_column("approach_variables", "value", type_=sa.String(511))
