"""add model_familiy

Revision ID: a9ff0da1c1a5
Revises: d4b1e78b121d
Create Date: 2024-08-09 09:28:23.559642

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "a9ff0da1c1a5"
down_revision = "d4b1e78b121d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("response_generator_model_family", pg.VARCHAR(255), nullable=True))
    op.drop_column("tenants", "available_models")
    op.add_column(
        "tenants",
        sa.Column(
            "allowed_model_families",
            pg.ARRAY(pg.VARCHAR(255)),
        ),
    )


def downgrade() -> None:
    op.drop_column("bots", "response_generator_model_family")
    op.add_column("tenants", sa.Column("available_models", pg.ARRAY(pg.VARCHAR(255))))
    op.drop_column("tenants", "allowed_model_families")
