"""add tenant_id column to bots table

Revision ID: b06acbe52663
Revises: 1c610eb5666d
Create Date: 2023-08-24 08:01:17.915470

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "b06acbe52663"
down_revision = "1c610eb5666d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("tenant_id", pg.INTEGER, nullable=False))
    op.create_foreign_key("fk_bots_tenant_id_tenants_id", "bots", "tenants", ["tenant_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_bots_tenant_id_tenants_id", "bots", type_="foreignkey")
    op.drop_column("bots", "tenant_id")
