"""create_users_documents_table

Revision ID: d4b1e78b121d
Revises: 5916773b932b
Create Date: 2024-08-06 09:36:10.246925

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "d4b1e78b121d"
down_revision = "5916773b932b"
branch_labels = None
depends_on = None


USERS_DOCUMENTS = "users_documents"


user_document_evaluation = pg.ENUM("good", "bad", name="user_document_evaluation")


def upgrade() -> None:
    op.create_table(
        USERS_DOCUMENTS,
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", pg.INTEGER, sa.ForeignKey("users.id", onupdate="CASCADE"), nullable=False),
        sa.Column("document_id", pg.INTEGER, sa.ForeignKey("documents.id", onupdate="CASCADE"), nullable=False),
        sa.Column("evaluation", user_document_evaluation, nullable=True),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", pg.TIMESTAMP, nullable=True),
        sa.UniqueConstraint("user_id", "document_id", name="unique_user_id_document_id"),
    )

    # Create the function
    # This function checks if the user and the document have the same tenant_id
    op.execute(
        """
    CREATE OR REPLACE FUNCTION check_has_common_tenant_id() RETURNS TRIGGER AS $$
    BEGIN
        IF (SELECT tenant_id FROM users WHERE id = NEW.user_id) !=
            (SELECT tenant_id FROM bots WHERE id = (SELECT bot_id FROM document_folders WHERE id = (SELECT document_folder_id FROM documents WHERE id = NEW.document_id ))) THEN
            RAISE EXCEPTION 'tenant_id does not match';
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """
    )

    # Create the trigger
    op.execute(
        """
    CREATE TRIGGER trigger_check_has_common_tenant_id
    BEFORE INSERT OR UPDATE ON users_documents
    FOR EACH ROW EXECUTE FUNCTION check_has_common_tenant_id();
    """
    )


def downgrade() -> None:
    # Drop the trigger
    op.execute("DROP TRIGGER IF EXISTS trigger_check_has_common_tenant_id ON users_documents")

    # Drop the function
    op.execute("DROP FUNCTION IF EXISTS check_has_common_tenant_id")
    op.drop_table(USERS_DOCUMENTS)
    user_document_evaluation.drop(op.get_bind())
