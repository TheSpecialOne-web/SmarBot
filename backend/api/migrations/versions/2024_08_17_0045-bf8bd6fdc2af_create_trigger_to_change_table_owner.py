"""create_trigger_to_change_table_owner

Revision ID: bf8bd6fdc2af
Revises: b96561506589
Create Date: 2024-08-17 00:45:40.399659

"""

import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "bf8bd6fdc2af"
down_revision = "b96561506589"
branch_labels = None
depends_on = None
app_env = os.environ.get("APP_ENV", "localhost")


def upgrade() -> None:
    if app_env == "localhost":
        return

    op.execute(
        """
CREATE OR REPLACE FUNCTION change_table_owner()
RETURNS event_trigger AS $$
DECLARE
    obj record;
BEGIN
    FOR obj IN
        SELECT * FROM pg_event_trigger_ddl_commands()
        WHERE command_tag = 'CREATE TABLE'
    LOOP
        EXECUTE format('ALTER TABLE %s OWNER TO azure_pg_admin',  obj.object_identity);
    END LOOP;
END;
$$ LANGUAGE plpgsql;
"""
    )

    op.execute(
        """
CREATE EVENT TRIGGER change_table_owner_trigger
ON ddl_command_end
WHEN TAG IN ('CREATE TABLE')
EXECUTE PROCEDURE change_table_owner();
"""
    )


def downgrade() -> None:
    if app_env == "localhost":
        return

    op.execute("DROP EVENT TRIGGER IF EXISTS change_table_owner_trigger;")
    op.execute("DROP FUNCTION IF EXISTS change_table_owner();")
