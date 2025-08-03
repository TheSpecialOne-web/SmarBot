"""add check constraint to administrators table

Revision ID: d5887fc816cc
Revises: bf8bd6fdc2af
Create Date: 2024-08-16 10:04:40.933631

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d5887fc816cc"
down_revision = "bf8bd6fdc2af"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # create the function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_administrator_tenant() RETURNS TRIGGER AS $$
        DECLARE
            user_tenant_id INTEGER;
        BEGIN
            SELECT tenant_id INTO user_tenant_id
            FROM users
            WHERE id = NEW.user_id;
            IF user_tenant_id != 1 THEN
                RAISE EXCEPTION 'Only users from neoAI can be added as administrators.';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # create the trigger
    op.execute(
        """
        CREATE TRIGGER enforce_administrator_tenant
        BEFORE INSERT OR UPDATE ON administrators
        FOR EACH ROW EXECUTE FUNCTION check_administrator_tenant();
        """
    )


def downgrade() -> None:
    # drop the trigger
    op.execute("DROP TRIGGER IF EXISTS enforce_administrator_tenant ON administrators;")

    # drop the function
    op.execute("DROP FUNCTION IF EXISTS check_administrator_tenant();")
