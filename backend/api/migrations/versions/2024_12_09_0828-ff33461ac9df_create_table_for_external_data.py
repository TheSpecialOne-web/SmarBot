"""create_table_for_external_data

Revision ID: ff33461ac9df
Revises: adcff164682d
Create Date: 2024-12-09 08:28:42.872925

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "ff33461ac9df"
down_revision = "adcff164682d"
branch_labels = None
depends_on = None

# table names
TENANTS = "tenants"
DOCUMENTS = "documents"
DOCUMENT_FOLDERS = "document_folders"
EXTERNAL_DATA_CONNECTIONS = "external_data_connections"

# column names
TENANT_ID = "tenant_id"
ENABLE_EXTERNAL_DATA_INTEGRATIONS = "enable_external_data_integrations"
EXTERNAL_ID = "external_id"
EXTERNAL_TYPE = "external_type"
EXTERNAL_UPDATED_AT = "external_updated_at"
LAST_SYNCED_AT = "last_synced_at"


def upgrade() -> None:
    external_type_enum = pg.ENUM("sharepoint", "box", "google_drive", name="external_type_enum")

    # external_data_connections
    op.create_table(
        EXTERNAL_DATA_CONNECTIONS,
        sa.Column(
            "id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            TENANT_ID,
            sa.Integer,
            sa.ForeignKey("tenants.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            EXTERNAL_TYPE,
            external_type_enum,
            nullable=False,
        ),
        sa.Column("encrypted_credentials", sa.Text, nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_index(
        f"{EXTERNAL_DATA_CONNECTIONS}_{TENANT_ID}_{EXTERNAL_TYPE}_idx",
        EXTERNAL_DATA_CONNECTIONS,
        [TENANT_ID, EXTERNAL_TYPE],
        unique=True,
    )

    # tenants
    op.add_column(
        TENANTS, sa.Column(ENABLE_EXTERNAL_DATA_INTEGRATIONS, sa.Boolean(), nullable=False, server_default="false")
    )

    # documents
    op.add_column(
        DOCUMENTS,
        sa.Column(EXTERNAL_ID, sa.Text, nullable=True),
    )
    op.add_column(
        DOCUMENTS,
        sa.Column(EXTERNAL_UPDATED_AT, pg.TIMESTAMP, nullable=True),
    )

    # document_folders
    op.add_column(
        DOCUMENT_FOLDERS,
        sa.Column(EXTERNAL_ID, sa.Text, nullable=True),
    )
    op.add_column(
        DOCUMENT_FOLDERS,
        sa.Column(
            EXTERNAL_TYPE,
            external_type_enum,
            nullable=True,
        ),
    )
    op.add_column(
        DOCUMENT_FOLDERS,
        sa.Column(EXTERNAL_UPDATED_AT, pg.TIMESTAMP, nullable=True),
    )
    op.add_column(
        DOCUMENT_FOLDERS,
        sa.Column(LAST_SYNCED_AT, pg.TIMESTAMP, nullable=True),
    )


def downgrade() -> None:
    op.drop_column(TENANTS, ENABLE_EXTERNAL_DATA_INTEGRATIONS)

    op.drop_column(DOCUMENTS, EXTERNAL_ID)
    op.drop_column(DOCUMENTS, EXTERNAL_TYPE)
    op.drop_column(DOCUMENTS, EXTERNAL_UPDATED_AT)

    op.drop_column(DOCUMENT_FOLDERS, EXTERNAL_ID)
    op.drop_column(DOCUMENT_FOLDERS, EXTERNAL_UPDATED_AT)
    op.drop_column(DOCUMENT_FOLDERS, EXTERNAL_TYPE)
    op.drop_column(DOCUMENT_FOLDERS, LAST_SYNCED_AT)

    op.drop_index(f"{EXTERNAL_DATA_CONNECTIONS}_{TENANT_ID}_{EXTERNAL_TYPE}_idx", EXTERNAL_DATA_CONNECTIONS)

    op.drop_table(EXTERNAL_DATA_CONNECTIONS)

    op.execute("DROP TYPE external_type_enum")
