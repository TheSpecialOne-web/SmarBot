"""add-enum-to-users-groups-role

Revision ID: 178f9a5b4aca
Revises: f05fe5705315
Create Date: 2024-09-28 07:57:15.823953

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "178f9a5b4aca"
down_revision = "f05fe5705315"
branch_labels = None
depends_on = None


def upgrade():
    group_role = pg.ENUM("group_admin", "group_editor", "group_viewer", name="group_role")
    group_role.create(op.get_bind())

    op.alter_column("users_groups", "role", server_default=sa.text("'group_viewer'::group_role"), nullable=False)
    op.alter_column("users_groups", "role", type_=group_role, postgresql_using="role::text::group_role")


def downgrade():
    op.alter_column("users_groups", "role", server_default=None, nullable=True)
    op.alter_column("users_groups", "role", type_=sa.String(), postgresql_using="role::text")
    op.execute("DROP TYPE group_role")
