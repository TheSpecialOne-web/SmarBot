from logging import getLogger
from typing import Literal, Optional

from pydantic import BaseModel

from .add_allowed_model_families_to_tenants import add_allowed_model_families_to_tenants
from .add_document_folder_id_field_to_search_index import (
    add_document_folder_id_field_to_search_index,
)
from .add_external_data_fields_to_search_index import add_external_data_fields_to_search_index
from .add_is_vectorized_field_to_search_index import (
    add_is_vectorized_field_to_search_index,
)
from .add_model_family_to_bot_templates import migrate_bot_templates_model_family
from .blob_container_for_chat_gpt_default import (
    create_blob_containers_for_chat_gpt_default,
)
from .chat_log_to_conversation import migrate_chat_log_to_conversation
from .conversation_data_points_document_id import (
    add_document_id_to_conversation_data_point,
)
from .correct_token_count import correct_token_count
from .create_tenant_admin_groups_and_general_group import (
    create_tenant_admin_groups_and_general_group,
)
from .create_tenant_container import create_tenant_container
from .init_data_source_id_to_bots import insert_data_source_id_to_bots
from .init_document_folders import (
    init_document_folders,
    init_document_folders_by_bot_ids,
)
from .init_document_folders_startup import init_document_folders_startup
from .make_tenant_user_relationship_many_to_one import (
    make_tenant_user_relationship_many_to_one,
)
from .migrate_index_content import (
    transfer_index_content_by_bot_id,
    transfer_index_content_by_tenant_id,
)
from .migrate_model_to_model_family import migrate_model_to_model_family
from .pdf_parser_for_chat_gpt_default import set_pdf_parser_to_chat_gpt_default_bots
from .set_either_user_policy_or_group_policy_to_user_policy import (
    set_either_user_policy_or_group_policy_to_user_policy,
)
from .term_to_term_v2 import migrate_term_to_term_v2
from .token_count import calculate_token_count
from .transfer_container_by_tenant_id import transfer_container_by_tenant_id
from .update_user_tenant_info_by_tenant_id_and_user_id import (
    update_user_tenant_info_by_tenant_id_and_user_id,
)
from .update_vector_index_schema import update_vector_index_schema

logger = getLogger(__name__)
logger.setLevel("INFO")


class MigrationQueueMessage(BaseModel):
    type: Literal[
        "chat-log-conversation",
        "create-blob-container-for-chat-gpt-default",
        "pdf-parser-for-chat-gpt-default",
        "transfer_index_content_by_tenant_id",
        "transfer_index_content_by_bot_id",
        "init-data-source-id-to-bots",
        "create-conversation-title",
        "create-tenant-container",
        "migrate-container-by-tenant-id",
        "calculate-token-count",
        "add-document-id-to-conversation-data-point",
        "transfer_users_tenants_info",
        "update-user-tenant-info-by-ids",
        "add-question-answer-id-field-to-search-index",
        "add-document-folder-id-field-to-search-index",
        "add-is-vectorized-field-to-search-index",
        "update-vector-index-schema",
        "term-to-term-v2",
        "correct-token-count",
        "init-document-folders",
        "init-document-folders-by-tenant-id",
        "init-document-folders-by-tenant-id-and-bot-ids",
        "model-to-model-family",
        "add-allowed-model-families-to-tenants",
        "migrate-bot-templates-model-family",
        "set-either-user-policy-or-group-policy-to-user-policy",
        "create-tenant-admin-group-and-general-group",
        "add-external-data-fields-to-search-index",
    ]
    tenant_id: Optional[int] = None
    user_id: Optional[int] = None
    bot_id: Optional[int] = None
    bot_ids: Optional[list[int]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class UseCase:
    def execute(self, message: MigrationQueueMessage) -> None:
        logger.info(f"migration type: {message.type}")
        if message.type == "chat-log-conversation":
            try:
                migrate_chat_log_to_conversation()
            except Exception as e:
                raise Exception(f"failed to migrate chat log to conversation: {e}")
        elif message.type == "create-blob-container-for-chat-gpt-default":
            try:
                create_blob_containers_for_chat_gpt_default()
            except Exception as e:
                raise Exception(f"failed to create blob containers for chat-gpt-default: {e}")

        # tenant index へのデータ移行コマンド
        elif message.type == "transfer_index_content_by_tenant_id":
            try:
                if message.tenant_id is None:
                    raise Exception("tenant id is required")
            except Exception as e:
                raise Exception(f"failed to transfer index content by tenant id: {e}")
            try:
                transfer_index_content_by_tenant_id(message.tenant_id)
            except Exception as e:
                raise Exception(f"failed to transfer index content by tenant id: {e}")
        elif message.type == "transfer_index_content_by_bot_id":
            try:
                if message.bot_id is None:
                    raise Exception("bot id is required")
            except Exception as e:
                raise Exception(f"failed to transfer index content by bot id: {e}")
            try:
                transfer_index_content_by_bot_id(message.bot_id)
            except Exception as e:
                raise Exception(f"failed to transfer index content by bot id: {e}")

        elif message.type == "pdf-parser-for-chat-gpt-default":
            try:
                set_pdf_parser_to_chat_gpt_default_bots()
            except Exception as e:
                raise Exception(f"failed to set pdf parser for chat-gpt-default: {e}")
        elif message.type == "init-data-source-id-to-bots":
            try:
                insert_data_source_id_to_bots()
            except Exception as e:
                raise Exception(f"failed to insert data source id to bots: {e}")
        elif message.type == "create-tenant-container":
            if message.tenant_id is None:
                raise Exception("tenant id is required")
            try:
                create_tenant_container(tenant_id=message.tenant_id)
            except Exception as e:
                raise Exception(f"failed to create tenant container: {e}")
        elif message.type == "migrate-container-by-tenant-id":
            if message.tenant_id is None:
                raise Exception("tenant id is required")
            try:
                transfer_container_by_tenant_id(tenant_id=message.tenant_id)
            except Exception as e:
                raise Exception(f"failed to transfer container by tenant id: {e}")
        elif message.type == "calculate-token-count":
            try:
                calculate_token_count()
            except Exception as e:
                raise Exception(f"failed to calculate token count: {e}")
        elif message.type == "add-document-id-to-conversation-data-point":
            try:
                add_document_id_to_conversation_data_point()
            except Exception as e:
                raise Exception(f"failed to add document id to conversation data point: {e}")
        elif message.type == "transfer_users_tenants_info":
            try:
                make_tenant_user_relationship_many_to_one()
            except Exception as e:
                raise Exception(f"failed to add tenant id to users table: {e}")
        elif message.type == "update-user-tenant-info-by-ids":
            if message.tenant_id is None:
                raise Exception("tenant id is required")
            if message.user_id is None:
                raise Exception("user id is required")
            try:
                update_user_tenant_info_by_tenant_id_and_user_id(tenant_id=message.tenant_id, user_id=message.user_id)
            except Exception as e:
                raise Exception(f"failed to update user tenant info by ids: {e}")
        elif message.type == "add-document-folder-id-field-to-search-index":
            try:
                add_document_folder_id_field_to_search_index()
            except Exception as e:
                raise Exception(f"failed to add document folder id to search index: {e}")
        elif message.type == "add-is-vectorized-field-to-search-index":
            try:
                add_is_vectorized_field_to_search_index()
            except Exception as e:
                raise Exception(f"failed to add is vectorized field to search index: {e}")
        elif message.type == "update-vector-index-schema":
            try:
                update_vector_index_schema()
            except Exception as e:
                raise Exception(f"failed to update vector index schema: {e}")
        elif message.type == "term-to-term-v2":
            try:
                migrate_term_to_term_v2()
            except Exception as e:
                raise Exception(f"failed to migrate term to term v2: {e}")
        elif message.type == "correct-token-count":
            if message.start_date is None:
                raise Exception("start date is required")
            if message.end_date is None:
                raise Exception("end date is required")
            try:
                correct_token_count(start_date=message.start_date, end_date=message.end_date)
            except Exception as e:
                raise Exception(f"failed to correct token count: {e}")

        elif message.type == "init-document-folders":
            try:
                init_document_folders_startup()
            except Exception as e:
                raise Exception(f"failed to init document folders: {e}")
        elif message.type == "init-document-folders-by-tenant-id":
            tenant_id = message.tenant_id
            if tenant_id is None:
                raise Exception("tenant id is required")
            try:
                init_document_folders(tenant_id=tenant_id)
            except Exception as e:
                raise Exception(f"failed to init document folders: {e}")
        elif message.type == "init-document-folders-by-tenant-id-and-bot-ids":
            tenant_id = message.tenant_id
            if tenant_id is None:
                raise Exception("tenant id is required")
            bot_ids = message.bot_ids
            if bot_ids is None:
                raise Exception("bot ids are required")
            try:
                init_document_folders_by_bot_ids(tenant_id=tenant_id, bot_ids=bot_ids)
            except Exception as e:
                raise Exception(f"failed to init document folders: {e}")
        elif message.type == "model-to-model-family":
            try:
                migrate_model_to_model_family()
            except Exception as e:
                raise Exception(f"failed to migrate model to model family: {e}")
        elif message.type == "add-allowed-model-families-to-tenants":
            try:
                add_allowed_model_families_to_tenants()
            except Exception as e:
                raise Exception(f"failed to add allowed model families to tenants: {e}")
        elif message.type == "migrate-bot-templates-model-family":
            try:
                migrate_bot_templates_model_family()
            except Exception as e:
                raise Exception(f"failed to add model family to bot templates: {e}")

        elif message.type == "set-either-user-policy-or-group-policy-to-user-policy":
            try:
                set_either_user_policy_or_group_policy_to_user_policy()
            except Exception as e:
                raise Exception(f"failed to set either user policy or group policy to user policy: {e}")

        elif message.type == "create-tenant-admin-group-and-general-group":
            try:
                create_tenant_admin_groups_and_general_group()
            except Exception as e:
                raise Exception(f"failed to create tenant admin groups and general groups: {e}")
        elif message.type == "add-external-data-fields-to-search-index":
            try:
                add_external_data_fields_to_search_index()
            except Exception as e:
                raise Exception(f"failed to add external data fields to search index: {e}")
        else:
            raise Exception(f"unknown migration type: {message.type}")
