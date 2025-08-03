from zipfile import BadZipFile

from pypdf.errors import PdfReadError
from timeout_decorator import timeout

from libs.constants import MAX_DEQUEUE_COUNT
from libs.feature_flag import get_feature_flag
from libs.logging import get_logger
from process_document.libs.document import encode_basename

from .libs.bot import SearchMethod
from .postgres.postgres import (
    find_with_ancestors_by_id_and_bot_id,
    get_bot,
    get_document,
    get_document_folder,
    get_root_document_folder_by_bot_id,
    get_tenant,
    update_document_status_to_failed,
)
from .queue_storage.queue_storage import (
    send_message_to_calculate_storage_usage_queue,
    send_message_to_create_embeddings_queue,
    send_message_to_sync_document_path_queue,
)
from .types import DocumentUploadQueue
from .usecase.process_document import IProcessDocumentUseCase, ProcessDocumentUseCase, UrsaProcessDocumentUseCase
from .utils.type_validation import validate_int

logger = get_logger(__name__)
logger.setLevel("INFO")


def execute(message_content: dict, dequeue_count: int = 0):
    queue = DocumentUploadQueue(**message_content)

    try:
        process_document(queue.tenant_id, queue.bot_id, queue.document_id)
    except Exception as e:
        if dequeue_count is not None and dequeue_count >= MAX_DEQUEUE_COUNT:
            update_document_status_to_failed(queue.document_id)
            logger.info("updated document status to failed")
        raise e


@timeout(25 * 60)  # 25 minutes
def process_document(tenant_id: int, bot_id: int, document_id: int):
    # tenantの取得 ----------------------------------------
    tenant = get_tenant(tenant_id)
    logger.info(f"tenant: {tenant!s}")

    # botの取得 ----------------------------------------
    bot = get_bot(tenant_id, bot_id)
    logger.info(f"bot: {bot!s}")

    # root_document_folderの取得 ----------------------------------------
    root_document_folder = get_root_document_folder_by_bot_id(bot_id)
    logger.info(f"root_document_folder: {root_document_folder!s}")

    # documentの取得 ----------------------------------------
    document = get_document(bot_id, document_id)
    logger.info(f"document: {document!s}")

    # bot_idが一致しているか確認 ----------------------------------------
    if bot["id"] != document["bot_id"]:
        raise Exception("bot_id is not equal")

    # SearchMethodに応じて処理クラス取得 ----------------------------------------
    process_document_usecase: IProcessDocumentUseCase
    is_ursa = bot["search_method"] in [SearchMethod.URSA.value, SearchMethod.URSA_SEMANTIC.value]
    if bot["search_method"] in {
        SearchMethod.BM25.value,
        SearchMethod.VECTOR.value,
        SearchMethod.HYBRID.value,
        SearchMethod.SEMANTIC_HYBRID.value,
    }:
        process_document_usecase = ProcessDocumentUseCase()
    elif is_ursa:
        process_document_usecase = UrsaProcessDocumentUseCase()
    else:
        raise Exception(f"search_method is not supported: {bot['search_method']}")

    # ファイルから文字抽出 ----------------------------------------
    FLAG_KEY = "blob-container-renewal"
    flag = get_feature_flag(FLAG_KEY, tenant_id, tenant["name"], default=True)
    container_name = tenant["container_name"] if flag else bot["container_name"]

    # Blobのパスを作成 ----------------------------------------
    blob_prefix = f"{bot_id}/" if flag else ""
    if root_document_folder["id"] != document["document_folder_id"]:
        blob_prefix += f"{document['document_folder_id']}/"
    if document["external_id"] is not None:
        blob_prefix = blob_prefix + f"{document['id']}/"

    blob_name = (
        f"{document['basename']}.{document['file_extension']}"
        if flag
        else f"{encode_basename(document['basename'])}.{document['file_extension']}"
    )

    blob_path = f"{blob_prefix}{blob_name}"

    blob_path = blob_path.replace("\\", "%5C")  # 九電のファイル名に含まれるバックスラッシュをエンコード

    try:
        uploaded_files = process_document_usecase.get_files(
            tenant=tenant,
            bot_id=bot["id"],
            container_name=container_name,
            blob_path=blob_path,
            file_extension=document["file_extension"],
            pdf_parser=bot["pdf_parser"],
        )
        logger.info(f"got {len(uploaded_files)} pages from blob")
    except PdfReadError:
        logger.warning("failed to get document: PdfReadError")
        update_document_status_to_failed(document_id)
        return
    except BadZipFile:
        logger.warning("failed to get document: BadZipFile")
        update_document_status_to_failed(document_id)
        return
    # チャンク切り ----------------------------------------
    chunks = process_document_usecase.convert_files_to_chunks(
        uploaded_files,
        document["file_extension"],
        text_chunk_size=validate_int(bot["approach_variables"].get("text_chunk_size", None)),
        chunk_overlap=validate_int(bot["approach_variables"].get("chunk_overlap", None)),
        table_chunk_size=validate_int(bot["approach_variables"].get("table_chunk_size", None)),
        pdf_parser=bot["pdf_parser"],
    )
    logger.info(f"converted files to {len(chunks)} chunks")

    search_service_endpoint = (
        tenant["search_service_endpoint"] if not is_ursa else bot["approach_variables"].get("search_service_endpoint")
    )
    if search_service_endpoint is None:
        raise Exception("search_service_endpoint is not set")

    document_folder_id = document["document_folder_id"]
    if document_folder_id is None:
        raise Exception("document_folder_id is not set")
    document_folder = get_document_folder(document_folder_id)
    document_folder_id_for_index = document_folder_id if document_folder_id != root_document_folder["id"] else None

    folder_path = ""
    if document_folder_id_for_index is not None:
        document_folder_with_ancestors = find_with_ancestors_by_id_and_bot_id(document_folder_id_for_index, bot_id)
        folder_names = [
            document_folder["name"]
            for document_folder in document_folder_with_ancestors["ancestor_folders"]
            if document_folder["name"] is not None
        ]
        if document_folder_with_ancestors["name"] is not None:
            folder_names.append(document_folder_with_ancestors["name"])

        folder_path = "/".join(folder_names)
        if folder_path:
            folder_path += "/"
    document_path = f"{folder_path}{document['basename']}"

    # チャンクの追加 ----------------------------------------
    if is_ursa:
        process_document_usecase.upload_documents_to_index(
            endpoint=search_service_endpoint,
            index_name=bot["index_name"],
            search_method=bot["search_method"],
            chunks=chunks,
            basename=document["basename"],
            file_extension=document["file_extension"],
            memo=document["memo"],
            document_id=document_id,
            document_folder_id=document_folder_id_for_index,
            external_id=document["external_id"],
            parent_external_id=document_folder["external_id"],
        )
        logger.info(f"uploaded documents to index: {bot['index_name']}")
    else:
        process_document_usecase.upload_documents_to_tenant_index(
            search_service_endpoint,
            index_name=tenant["index_name"],
            chunks=chunks,
            bot_id=bot_id,
            data_source_id=bot["data_source_id"],
            document_id=document_id,
            document_folder_id=document_folder_id_for_index,
            basename=document["basename"],
            document_path=document_path,
            blob_path=blob_path,
            file_extension=document["file_extension"],
            memo=document["memo"],
            external_id=document["external_id"],
            parent_external_id=document_folder["external_id"],
        )
        logger.info(f"uploaded documents to index: {tenant['index_name']}")

    # エンべディングを作成するためのメッセージを送信 ----------------------------------------
    search_method = SearchMethod(bot["search_method"])
    if search_method.should_create_embeddings():
        send_message_to_create_embeddings_queue(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_id=document_id,
        )
        logger.info("sent message to create embeddings queue")
        return

    # 外部データの場合は、外部データのパスを同期するためのメッセージを送信 ----------------------------------------
    is_external = document["external_id"] is not None
    if is_external:
        send_message_to_sync_document_path_queue(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_folder_id=str(document_folder["id"]),
            document_ids=[document_id],
        )
        logger.info("sent message to sync document path queue")
    else:
        # documentのstatusをcompletedにする ----------------------------------------
        process_document_usecase.update_document_status_to_completed(document_id)
        logger.info("updated document status to completed")

    send_message_to_calculate_storage_usage_queue(
        tenant_id=tenant_id,
        bot_id=bot_id,
        document_id=document_id,
    )
    logger.info("sent message to calculate storage usage queue")

    logger.info("finished processing documents")
