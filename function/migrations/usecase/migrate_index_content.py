from logging import getLogger
import math
import os
import uuid

from migrations.infrastructure.cognitive_search import (
    IndexDocument,
    get_index_document_count,
    get_index_documents,
    upload_documents_to_index_from_batch,
)
from migrations.infrastructure.postgres import (
    Bot,
    Document,
    get_bot_by_id,
    get_bots_by_tenant_id,
    get_documents_by_bot_id,
    get_tenant_by_id,
)
from process_document import SearchMethod

logger = getLogger(__name__)


def search_page_number_from_chunknumber(chunknumber: str) -> int:
    pagenumber = chunknumber.split("-")[0]
    if pagenumber.startswith("p"):
        if "paragraph" in pagenumber:
            # wordの場合
            return int(pagenumber.split("paragraph")[1])
        # PDFの場合
        return int(pagenumber[1:])
    if "sheetnumber" in pagenumber:
        # excelの場合
        return int(pagenumber.split("sheetnumber")[1])
    if "slide" in pagenumber:
        # PPTXの場合
        return int(pagenumber.split("slide")[1])
    raise ValueError(f"uploaded document is invalid: {chunknumber}")


def is_bot_valid(bot: Bot) -> bool:
    bot_id = bot.id
    if bot.approach == "chat_gpt_default":
        logger.info(f"bot_id: {bot_id} is chat_gpt_default.")
        return False
    if bot.search_method in [SearchMethod.URSA.value, SearchMethod.URSA_SEMANTIC.value]:
        logger.info(f"bot_id: {bot_id} is ursa_bot.")
        return False
    if bot.index_name is None:
        logger.info(f"bot_id: {bot_id} has no index_name.")
        return False
    if bot.data_source_id is None:
        logger.info(f"bot_id: {bot_id} has no data_source_id.")
        return False
    return True


def migrate_bot_index_documents_to_tenant_index(
    bot: Bot,
    tenant_index_name: str,
    db_documents: list[Document],
) -> None:
    bot_index_name = bot.index_name
    if bot_index_name is None:
        raise Exception(f"bot_id: {bot.id} has no index_name.")
    index_document_count = get_index_document_count(bot_index_name)

    skip = 0
    LIMIT = 1000
    num_iterations = math.ceil(index_document_count / LIMIT)
    bot_index_documents: list[dict] = []
    for _ in range(num_iterations):
        bot_index_documents.clear()

        try:
            bot_index_documents = get_index_documents(
                index_name=bot_index_name,
                order_by="createddate asc",
                top=LIMIT,
                skip=skip,
            )
        except Exception as e:
            raise Exception(f"Failed to get documents of {bot_index_name}: {e}")

        try:
            tenant_index_documents = convert_bot_index_documents_to_tenant_index_documents(
                bot=bot,
                bot_index_documents=bot_index_documents,
                db_documents=db_documents,
            )
        except Exception as e:
            raise Exception(f"Failed to convert bot_index_documents to tenant_index_documents: {e}")

        try:
            upload_documents_to_index_from_batch(tenant_index_name, tenant_index_documents)
        except Exception as e:
            raise Exception(f"Failed to upload to tenant_index: {e}")

        skip += LIMIT


def convert_bot_index_documents_to_tenant_index_documents(
    bot: Bot,
    bot_index_documents: list[dict],
    db_documents: list[Document],
) -> list[IndexDocument]:
    bot_id = bot.id
    if bot.data_source_id is None:
        raise Exception(f"bot_id: {bot_id} has no data_source_id.")
    data_source_id = bot.data_source_id

    # 移行するデータを作る
    sections: list[IndexDocument] = []
    for document_in_bot_index in bot_index_documents:
        # file_name, file_extension, blob_path, question, content_vector, chunknumber
        try:
            file_name = document_in_bot_index["sourcename"]
            _, file_extension = os.path.splitext(document_in_bot_index["pagename"])
            blob_path = f"{document_in_bot_index['sourceid']}{file_extension}"
            question = document_in_bot_index["question"] if "question" in document_in_bot_index else None
            question_answer_id = (
                document_in_bot_index["question_answer_id"] if "question_answer_id" in document_in_bot_index else None
            )
            title_vector = document_in_bot_index["titleVector"] if "titleVector" in document_in_bot_index else []
            content_vector = document_in_bot_index["contentVector"] if "contentVector" in document_in_bot_index else []
            chunknumber = document_in_bot_index["chunknumber"]
        except Exception as e:
            raise Exception(f"failed to get properties: {e}")

        # document_id
        postgres_document_to_transfer = next(
            (
                bot_document_in_postgres
                for bot_document_in_postgres in db_documents
                if (
                    bot_document_in_postgres.basename == file_name
                    and bot_document_in_postgres.file_extension == file_extension[1:]
                    and bot_document_in_postgres.bot_id == bot_id
                )
            ),
            None,
        )
        if postgres_document_to_transfer is None:
            continue
        try:
            document_id = postgres_document_to_transfer.id
        except Exception as e:
            raise e

        # page_number
        try:
            page_number = search_page_number_from_chunknumber(chunknumber)
        except ValueError:
            continue
        except Exception as e:
            raise Exception(f"failed to search page number: {e}")

        new_section: IndexDocument = {
            "id": str(uuid.uuid4()),
            "bot_id": bot_id,
            "data_source_id": data_source_id,
            "question_answer_id": question_answer_id,
            "document_id": document_id,
            "content": document_in_bot_index["content"],
            "blob_path": blob_path,
            "file_name": file_name,
            "file_extension": file_extension[1:],
            "page_number": page_number,
            "created_at": document_in_bot_index["createddate"],
            "updated_at": document_in_bot_index["updateddate"],
            "question": question,
            "title_vector": title_vector,
            "content_vector": content_vector,
        }

        sections.append(new_section)

    return sections


def transfer_index_content_by_tenant_id(tenant_id: int) -> None:
    tenant = get_tenant_by_id(tenant_id)
    tenant_index_name = tenant.index_name
    if tenant_index_name is None:
        raise Exception(f"tenant_id: {tenant.id} has no index_name.")

    tenant_bots = get_bots_by_tenant_id(tenant_id)

    # 全botのvalidation
    valid_bots: list[Bot] = []
    for bot in tenant_bots:
        if not is_bot_valid(bot):
            logger.warning(f"bot_id: {bot.id} is invalid.")
            continue
        valid_bots.append(bot)

    # valid_botsのindexをtenantのindexに移行する
    for bot in valid_bots:
        bot_id = bot.id

        if bot.index_name is None:
            logger.warning(f"bot_id: {bot_id} has no index_name.")
            continue

        bot_documents_in_postgres = get_documents_by_bot_id(bot_id)
        migrate_bot_index_documents_to_tenant_index(
            bot=bot,
            tenant_index_name=tenant_index_name,
            db_documents=bot_documents_in_postgres,
        )


def transfer_index_content_by_bot_id(bot_id: int) -> None:
    # botのvalidation
    bot = get_bot_by_id(bot_id)
    if not is_bot_valid(bot):
        raise Exception(f"bot_id: {bot_id} is invalid.")
    if bot.index_name is None:
        raise Exception(f"bot_id: {bot_id} has no index_name.")

    # tenantのvalidation
    tenant = get_tenant_by_id(bot.tenant_id)
    if tenant.index_name is None:
        raise Exception(f"tenant_id: {tenant.id} has no index_name.")

    # migration元のデータを取得
    bot_documents_in_postgres = get_documents_by_bot_id(bot_id)

    migrate_bot_index_documents_to_tenant_index(
        bot=bot,
        tenant_index_name=tenant.index_name,
        db_documents=bot_documents_in_postgres,
    )
