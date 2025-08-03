"""alter alias column of tenants table not unique

Revision ID: 48b9cb2d422c
Revises: 74e36de582dd
Create Date: 2024-03-15 12:33:40.242223

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "48b9cb2d422c"
down_revision = "74e36de582dd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("tenants_alias_key", "tenants", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("tenants_alias_key", "tenants", ["alias"])
