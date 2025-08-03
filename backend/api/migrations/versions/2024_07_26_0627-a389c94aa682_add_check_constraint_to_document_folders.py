"""add check constraint to document_folders

Revision ID: a389c94aa682
Revises: 4500b846ba70
Create Date: 2024-07-26 06:27:41.031295

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a389c94aa682"
down_revision = "4500b846ba70"
branch_labels = None
depends_on = None


def upgrade():
    # Create the function
    op.execute(
        """
    CREATE OR REPLACE FUNCTION check_root_folder_uniqueness() RETURNS TRIGGER AS $$
    DECLARE
        root_folder_count INTEGER;
    BEGIN
        SELECT COUNT(*) INTO root_folder_count
        FROM (
        SELECT df.id
        FROM document_folders df
        JOIN document_folder_paths dfp ON dfp.descendant_document_folder_id = df.id
        WHERE df.bot_id = NEW.bot_id
        GROUP BY df.id
        HAVING COUNT(dfp.id) = 1
        ) AS root_folders;

        IF root_folder_count > 1 THEN
            RAISE EXCEPTION 'Multiple root folders exist for bot_id: %. Only one root folder is allowed.', NEW.bot_id;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """
    )

    # Create the trigger
    op.execute(
        """
    CREATE CONSTRAINT TRIGGER enforce_single_root_folder
    AFTER INSERT OR UPDATE ON document_folders
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION check_root_folder_uniqueness();
    """
    )


def downgrade():
    # Drop the trigger
    op.execute("DROP TRIGGER IF EXISTS enforce_single_root_folder ON document_folders;")

    # Drop the function
    op.execute("DROP FUNCTION IF EXISTS check_root_folder_uniqueness();")
