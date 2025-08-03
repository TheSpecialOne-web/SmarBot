from libs.logging import get_logger
from migrations.infrastructure.postgres import (
    get_bots_by_tenant_id,
    get_conversation_data_points_by_bot_id,
    get_documents_by_bot_id,
    get_tenants,
    update_conversation_data_point_document_id,
)
from process_document.libs.document import encode_basename

logger = get_logger(__name__)
logger.setLevel("INFO")


def add_document_id_to_conversation_data_point():
    try:
        tenants = get_tenants()
    except Exception as e:
        raise Exception(f"Failed to get tenants: {e}")

    for tenant in tenants:
        try:
            bots = get_bots_by_tenant_id(tenant.id)
        except Exception as e:
            raise Exception(f"Failed to get bots by tenant_id: {e}")

        for bot in bots:
            try:
                documents = get_documents_by_bot_id(bot.id)
            except Exception as e:
                raise Exception(f"Failed to get documents by bot_id: {e}")

            try:
                conversation_data_points = get_conversation_data_points_by_bot_id(bot.id)
            except Exception as e:
                raise Exception(f"Failed to get conversation_data_points by bot_id: {e}")

            failed_conversation_data_point_ids = []
            for conversation_data_point in conversation_data_points:
                if conversation_data_point.document_id is not None:
                    continue
                for document in documents:
                    blob_path = f"{encode_basename(document.basename)}.{document.file_extension}"
                    if conversation_data_point.blob_path == blob_path:
                        update_conversation_data_point_document_id(conversation_data_point.id, document.id)
                        break
                failed_conversation_data_point_ids.append(conversation_data_point.id)

            if failed_conversation_data_point_ids:
                logger.warning(
                    f"Failed to update document_id to conversation_data_point. bot_id: {bot.id}, conversation_data_point_ids: {failed_conversation_data_point_ids}"
                )

            logger.info(f"Successfully updated document_id to conversation_data_point. bot_id: {bot.id}")

        logger.info(f"Successfully updated document_id to conversation_data_point. tenant_id: {tenant.id}")

    logger.info("Successfully updated document_id to conversation_data_point.")
