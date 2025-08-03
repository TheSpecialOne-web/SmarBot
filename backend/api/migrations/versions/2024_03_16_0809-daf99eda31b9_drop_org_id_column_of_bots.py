"""drop_org_id_column_of bots

Revision ID: daf99eda31b9
Revises: ec51b578c350
Create Date: 2024-03-16 08:09:22.796179

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "daf99eda31b9"
down_revision = "ec51b578c350"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("bots", "org_id")


def downgrade() -> None:
    op.add_column("bots", sa.Column("org_id", pg.VARCHAR(255), nullable=False))
