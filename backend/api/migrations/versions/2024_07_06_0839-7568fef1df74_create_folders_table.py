"""create_folders_table

Revision ID: 7568fef1df74
Revises: a6c0f4b7508d
Create Date: 2024-07-06 08:39:55.174717

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "7568fef1df74"
down_revision = "a6c0f4b7508d"
branch_labels = None
depends_on = None


# table names
DOCUMENT_FOLDERS = "document_folders"
DOCUMENT_FOLDER_PATHS = "document_folder_paths"
DOCUMENTS = "documents"

# columns
ID = "id"
DOCUMENT_FOLDER_ID = "document_folder_id"
CREATED_AT = "created_at"
UPDATED_AT = "updated_at"
DELETED_AT = "deleted_at"


def upgrade() -> None:
    op.create_table(
        DOCUMENT_FOLDERS,
        sa.Column(
            ID,
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "bot_id", pg.INTEGER, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column(CREATED_AT, pg.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column(UPDATED_AT, pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column(DELETED_AT, pg.TIMESTAMP),
    )

    op.create_table(
        DOCUMENT_FOLDER_PATHS,
        sa.Column(
            ID,
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "ancestor_document_folder_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey(f"{DOCUMENT_FOLDERS}.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "descendant_document_folder_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey(f"{DOCUMENT_FOLDERS}.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("path_length", pg.INTEGER, nullable=False),
        sa.Column(CREATED_AT, pg.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column(UPDATED_AT, pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column(DELETED_AT, pg.TIMESTAMP),
    )

    op.add_column(
        DOCUMENTS,
        sa.Column(
            DOCUMENT_FOLDER_ID,
            pg.UUID(as_uuid=True),
            sa.ForeignKey(f"{DOCUMENT_FOLDERS}.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(DOCUMENTS, DOCUMENT_FOLDER_ID)
    op.drop_table(DOCUMENT_FOLDER_PATHS)
    op.drop_table(DOCUMENT_FOLDERS)
