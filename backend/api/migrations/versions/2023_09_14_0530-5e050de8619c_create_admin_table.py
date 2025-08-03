"""create administrator table

Revision ID: 5e050de8619c
Revises: b031d83338f7
Create Date: 2023-09-14 05:30:13.574311

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "5e050de8619c"
down_revision = "b031d83338f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "administrators",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column("user_id", pg.INTEGER, nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, nullable=False, default=sa.func.current_timestamp()),
        sa.Column(
            "updated_at",
            pg.TIMESTAMP,
            nullable=False,
            default=sa.func.current_timestamp(),
            onupdate=sa.func.current_timestamp(),
        ),
        sa.Column("deleted_at", pg.TIMESTAMP, nullable=True),
    )
    op.create_foreign_key("fk_administrators_user_id_users_id", "administrators", "users", ["user_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_administrators_user_id_users_id", "administrators", type_="foreignkey")
    op.drop_table("administrators")
