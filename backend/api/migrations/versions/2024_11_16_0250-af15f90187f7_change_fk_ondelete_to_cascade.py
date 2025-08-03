"""change fk ondelete to cascade

Revision ID: af15f90187f7
Revises: 4ee93d97c7bb
Create Date: 2024-11-16 02:50:02.342028

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "af15f90187f7"
down_revision = "4ee93d97c7bb"
branch_labels = None
depends_on = None

fk_configs = [
    {
        "constraint_name": "tenant_alerts_tenant_id_fkey",
        "child_table": "tenant_alerts",
        "parent_table": "tenants",
        "fk_column": "tenant_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "users_groups_group_id_fkey",
        "child_table": "users_groups",
        "parent_table": "groups",
        "fk_column": "group_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "approach_variables_bot_id_fkey",
        "child_table": "approach_variables",
        "parent_table": "bots",
        "fk_column": "bot_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "bot_prompt_templates_bot_id_fkey",
        "child_table": "bot_prompt_templates",
        "parent_table": "bots",
        "fk_column": "bot_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "users_liked_bots_bot_id_fkey",
        "child_table": "users_liked_bots",
        "parent_table": "bots",
        "fk_column": "bot_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "document_folder_paths_ancestor_document_folder_id_fkey",
        "child_table": "document_folder_paths",
        "parent_table": "document_folders",
        "fk_column": "ancestor_document_folder_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "document_folder_paths_descendant_document_folder_id_fkey",
        "child_table": "document_folder_paths",
        "parent_table": "document_folders",
        "fk_column": "descendant_document_folder_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "users_documents_document_id_fkey",
        "child_table": "users_documents",
        "parent_table": "documents",
        "fk_column": "document_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "conversation_turns_conversation_id_fkey",
        "child_table": "conversation_turns",
        "parent_table": "conversations",
        "fk_column": "conversation_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "conversation_data_points_turn_id_fkey",
        "child_table": "conversation_data_points",
        "parent_table": "conversation_turns",
        "fk_column": "turn_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "chat_completion_data_points_chat_completion_id_fkey",
        "child_table": "chat_completion_data_points",
        "parent_table": "chat_completions",
        "fk_column": "chat_completion_id",
        "ref_column": "id",
    },
    {
        "constraint_name": "fk_users_policies_user_id_users_id",
        "child_table": "users_policies",
        "parent_table": "users",
        "fk_column": "user_id",
        "ref_column": "id",
    },
]


def change_fk_ondelete(fk_config, new_ondelete):
    op.drop_constraint(fk_config["constraint_name"], fk_config["child_table"], type_="foreignkey")
    op.create_foreign_key(
        constraint_name=fk_config["constraint_name"],
        source_table=fk_config["child_table"],
        referent_table=fk_config["parent_table"],
        local_cols=[fk_config["fk_column"]],
        remote_cols=[fk_config["ref_column"]],
        onupdate="CASCADE",
        ondelete=new_ondelete,
    )


def upgrade() -> None:
    for fk_config in fk_configs:
        change_fk_ondelete(fk_config, "CASCADE")


def downgrade() -> None:
    for fk_config in fk_configs:
        change_fk_ondelete(fk_config, "RESTRICT")
