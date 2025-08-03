"""create guidelines table

Revision ID: adcff164682d
Revises: 73e2eee503b3
Create Date: 2024-11-28 20:16:10.227778

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "adcff164682d"
down_revision = "73e2eee503b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guidelines",
        sa.Column(
            "id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )

    op.create_index(
        "guidelines_tenant_id_filename_unique_idx",
        "guidelines",
        ["tenant_id", "filename"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("guidelines_tenant_id_filename_unique_idx", table_name="guidelines")
    op.drop_table("guidelines")
