from datetime import datetime
from enum import Enum
from typing import Literal
import uuid

from psycopg2.extras import DictCursor, execute_values
from pydantic import BaseModel

from libs.connection import get_connection
from migrations.types import (
    ModelFamily,
    ModelName,
    Text2ImageModel,
    Text2ImageModelFamily,
)


class ChatLog(BaseModel):
    chat_id: str
    user_id: int
    bot_id: int
    user_input: str
    bot_output: str
    queries: list[str]
    query_input_token: int | None
    query_output_token: int | None
    response_input_token: int | None
    response_output_token: int | None
    created_at: datetime
    updated_at: datetime
    query_generator_model: str | None
    response_generator_model: str | None


class Conversation(BaseModel):
    id: str
    title: str
    bot_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    turns: list["ConversationTurn"]


class ConversationTurn(BaseModel):
    id: str
    conversation_id: str
    user_input: str
    bot_output: str
    queries: list[str]
    query_input_token: int | None
    query_output_token: int | None
    response_input_token: int
    response_output_token: int
    token_count: float | None
    query_generator_model: ModelName | None
    response_generator_model: ModelName
    created_at: datetime
    updated_at: datetime


class ConversationDataPoint(BaseModel):
    id: str
    turn_id: str
    cite_number: int
    chunk_name: str
    content: str
    blob_path: str
    page_number: int
    type: str
    url: str | None
    additional_info: dict | None
    document_id: int | None


class Tenant(BaseModel):
    id: int
    name: str
    alias: str
    index_name: str | None
    container_name: str | None
    additional_platforms: list[str]
    allow_foreign_region: bool


class UserTenant(BaseModel):
    id: int
    user_id: int
    tenant_id: int
    roles: str
    created_at: datetime
    updated_at: datetime


class PdfParser(str, Enum):
    PYPDF = "pypdf"
    DOCUMENT_INTELLIGENCE = "document_intelligence"
    AI_VISION = "ai_vision"
    LLM_DOCUMENT_READER = "llm_document_reader"


class Term(BaseModel):
    id: int
    bot_id: int
    name: str
    description: str


class Bot(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str
    index_name: str | None
    container_name: str | None
    approach: str
    example_questions: list[str]
    search_method: str | None
    query_generator_model: str | None
    response_generator_model: str
    pdf_parser: PdfParser | None
    enable_web_browsing: bool = False
    data_source_id: str | None
    image_generator_model: str | None


class BotTemplate(BaseModel):
    id: str
    name: str
    description: str
    response_generator_model: str


class Document(BaseModel):
    id: int
    bot_id: int
    basename: str
    file_extension: str
    status: str


class UserAction(BaseModel):
    user_id: int
    bot_id: int
    user_action: Literal["read"] | None
    group_action: Literal["read", "write"]


def get_bot_by_id(id: int) -> Bot:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM bots
        WHERE id = %s
        AND deleted_at IS NULL
    """,
        (id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        raise Exception(f"bot not found by id: {id}")

    bot = Bot(
        id=row["id"],
        tenant_id=row["tenant_id"],
        name=row["name"],
        description=row["description"],
        index_name=row["index_name"],
        container_name=row["container_name"],
        approach=row["approach"],
        example_questions=row["example_questions"],
        search_method=row["search_method"],
        query_generator_model=row["query_generator_model"],
        response_generator_model=row["response_generator_model"],
        pdf_parser=row["pdf_parser"],
        enable_web_browsing=row["enable_web_browsing"],
        data_source_id=row["data_source_id"],
        image_generator_model=row["image_generator_model"] or None,
    )

    return bot


def get_bot_templates() -> list[BotTemplate]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM bot_templates
        WHERE deleted_at IS NULL
    """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    bot_templates = []
    for row in rows:
        bot_templates.append(
            BotTemplate(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                response_generator_model=row["response_generator_model"],
            )
        )
    return bot_templates


def get_chat_logs() -> list[ChatLog]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM chat_logs
        ORDER BY created_at ASC
    """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    chat_logs = []
    for row in rows:
        chat_log = ChatLog(
            chat_id=row["chat_id"],
            user_id=row["user_id"],
            bot_id=row["bot_id"],
            user_input=row["user_input"],
            bot_output=row["bot_output"],
            queries=row["queries"],
            query_input_token=row["query_input_token"],
            query_output_token=row["query_output_token"],
            response_input_token=row["response_input_token"],
            response_output_token=row["response_output_token"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            query_generator_model=row["query_generator_model"] or row["model_name"] or None,
            response_generator_model=row["response_generator_model"] or row["model_name"] or None,
        )
        chat_logs.append(chat_log)

    return chat_logs


def get_conversation_turns(conversation_id: str) -> list[ConversationTurn]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM conversation_turns
        WHERE conversation_id = %s
        ORDER BY created_at ASC
    """,
        (conversation_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    conversation_turns = []
    for row in rows:
        conversation_turn = ConversationTurn(
            id=row["id"],
            conversation_id=row["conversation_id"],
            user_input=row["user_input"],
            bot_output=row["bot_output"],
            queries=row["queries"],
            query_input_token=row["query_input_token"],
            query_output_token=row["query_output_token"],
            response_input_token=row["response_input_token"],
            response_output_token=row["response_output_token"],
            token_count=row["token_count"],
            query_generator_model=row["query_generator_model"],
            response_generator_model=row["response_generator_model"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        conversation_turns.append(conversation_turn)

    return conversation_turns


def get_conversations() -> list[Conversation]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM conversations
        WHERE deleted_at IS NULL
        ORDER BY created_at ASC
    """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    conversations = []
    for row in rows:
        if not row["title"]:
            conversation = Conversation(
                id=row["id"],
                title="",
                bot_id=row["bot_id"],
                user_id=row["user_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                turns=[],
            )
        else:
            conversation = Conversation(
                id=row["id"],
                title=row["title"],
                bot_id=row["bot_id"],
                user_id=row["user_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                turns=[],
            )
        conversations.append(conversation)

    return conversations


def update_conversation_title(conversation_id: str, title: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE conversations
        SET title = %s
        WHERE id = %s
    """,
        (title, conversation_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def create_conversations(conversations: list[Conversation]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    execute_values(
        cur,
        "INSERT INTO conversations (id, title, bot_id, user_id, created_at, updated_at) VALUES %s",
        [
            (
                conversation.id,
                conversation.title,
                conversation.bot_id,
                conversation.user_id,
                conversation.created_at,
                conversation.updated_at,
            )
            for conversation in conversations
        ],
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def create_conversation_turns(turns: list[ConversationTurn]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    execute_values(
        cur,
        "INSERT INTO conversation_turns (id, conversation_id, user_input, bot_output, queries, query_input_token, query_output_token, response_input_token, response_output_token, query_generator_model, response_generator_model, created_at, updated_at) VALUES %s",
        [
            (
                turn.id,
                turn.conversation_id,
                turn.user_input,
                turn.bot_output,
                turn.queries,
                turn.query_input_token,
                turn.query_output_token,
                turn.response_input_token,
                turn.response_output_token,
                turn.query_generator_model,
                turn.response_generator_model,
                turn.created_at,
                turn.updated_at,
            )
            for turn in turns
        ],
    )

    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_conversation_data_points_by_bot_id(bot_id: int) -> list[ConversationDataPoint]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT conversation_data_points.*
        FROM conversation_data_points
        JOIN conversation_turns ON conversation_data_points.turn_id = conversation_turns.id
        JOIN conversations ON conversation_turns.conversation_id = conversations.id
        JOIN bots ON conversations.bot_id = bots.id
        WHERE bots.id = %s AND conversation_data_points.blob_path != '' AND conversation_data_points.type = 'internal' AND conversation_data_points.deleted_at IS NULL;
    """,
        (bot_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    conversation_data_points = []
    for row in rows:
        conversation_data_point = ConversationDataPoint(
            id=row["id"],
            turn_id=row["turn_id"],
            cite_number=row["cite_number"],
            chunk_name=row["chunk_name"],
            content=row["content"],
            blob_path=row["blob_path"],
            page_number=row["page_number"],
            type=row["type"],
            url=row["url"],
            additional_info=row["additional_info"],
            document_id=row["document_id"],
        )
        conversation_data_points.append(conversation_data_point)

    return conversation_data_points


def update_conversation_data_point_document_id(conversation_data_point_id: str, document_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE conversation_data_points
        SET document_id = %s
        WHERE id = %s
    """,
        (document_id, conversation_data_point_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_tenants() -> list[Tenant]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM tenants
        WHERE deleted_at IS NULL
    """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    tenants = []
    for row in rows:
        tenant = Tenant(
            id=row["id"],
            name=row["name"],
            alias=row["alias"],
            index_name=row["index_name"],
            container_name=row["container_name"],
            additional_platforms=row["additional_platforms"] if isinstance(row["additional_platforms"], list) else [],
            allow_foreign_region=row["allow_foreign_region"],
        )
        tenants.append(tenant)

    return tenants


def get_tenant_by_id(id: int) -> Tenant:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM tenants
        WHERE id = %s
        AND deleted_at IS NULL
    """,
        (id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        raise Exception(f"tenant not found by id: {id}")

    tenant = Tenant(
        id=row["id"],
        name=row["name"],
        alias=row["alias"],
        index_name=row["index_name"],
        container_name=row["container_name"],
        additional_platforms=row["additional_platforms"],
        allow_foreign_region=row["allow_foreign_region"],
    )

    return tenant


def get_users_tenants_by_tenant_id(tenant_id: int) -> list[UserTenant]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM users_tenants
        WHERE tenant_id = %s
        AND deleted_at IS NULL
    """,
        (tenant_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    users_tenants = []
    for row in rows:
        user_tenant = UserTenant(
            id=row["id"],
            user_id=row["user_id"],
            tenant_id=row["tenant_id"],
            roles=row["roles"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        users_tenants.append(user_tenant)

    return users_tenants


def get_user_tenant_by_tenant_id_and_user_id(tenant_id: int, user_id: int) -> UserTenant:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM users_tenants
        WHERE tenant_id = %s AND user_id = %s
        AND deleted_at IS NULL
    """,
        (tenant_id, user_id),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    user_tenant = UserTenant(
        id=row["id"],
        user_id=row["user_id"],
        tenant_id=row["tenant_id"],
        roles=row["roles"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

    return user_tenant


def update_roles_in_users_table(user_id: int, roles: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET roles = %s
        WHERE id = %s
    """,
        (roles, user_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def update_tenant_id_in_users_table(tenant_id: int, user_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET tenant_id = %s
        WHERE id = %s
    """,
        (tenant_id, user_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_bots_by_tenant_id(tenant_id: int) -> list[Bot]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM bots
        WHERE tenant_id = %s
        AND deleted_at IS NULL
    """,
        (tenant_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    bots = []
    for row in rows:
        bot = Bot(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            description=row["description"],
            index_name=row["index_name"],
            container_name=row["container_name"],
            approach=row["approach"],
            example_questions=row["example_questions"],
            search_method=row["search_method"],
            query_generator_model=row["query_generator_model"],
            response_generator_model=row["response_generator_model"],
            image_generator_model=row["image_generator_model"] or None,
            pdf_parser=row["pdf_parser"],
            enable_web_browsing=row["enable_web_browsing"],
            data_source_id=row["data_source_id"],
        )
        bots.append(bot)

    return bots


def get_custom_bots() -> list[Bot]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM bots
        WHERE approach != 'chat_gpt_default'
        AND deleted_at IS NULL
    """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    bots: list[Bot] = []
    for row in rows:
        try:
            pdf_parser = PdfParser(row["pdf_parser"])
        except Exception:
            pdf_parser = None
        bot = Bot(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            description=row["description"],
            index_name=row["index_name"],
            container_name=row["container_name"],
            approach=row["approach"],
            example_questions=row["example_questions"],
            search_method=row["search_method"],
            query_generator_model=row["query_generator_model"],
            response_generator_model=row["response_generator_model"],
            pdf_parser=pdf_parser,
            enable_web_browsing=row["enable_web_browsing"],
            data_source_id=row["data_source_id"],
            image_generator_model=row["image_generator_model"] or None,
        )
        bots.append(bot)

    return bots


def get_chat_gpt_bots() -> list[Bot]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM bots
        WHERE approach = 'chat_gpt_default'
        AND deleted_at IS NULL
    """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    bots: list[Bot] = []
    for row in rows:
        try:
            pdf_parser = PdfParser(row["pdf_parser"])
        except Exception:
            pdf_parser = None
        bot = Bot(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            description=row["description"],
            index_name=row["index_name"],
            container_name=row["container_name"],
            approach=row["approach"],
            example_questions=row["example_questions"],
            search_method=row["search_method"],
            query_generator_model=row["query_generator_model"],
            response_generator_model=row["response_generator_model"],
            pdf_parser=pdf_parser,
            enable_web_browsing=row["enable_web_browsing"],
            data_source_id=row["data_source_id"],
            image_generator_model=row["image_generator_model"] or None,
        )
        bots.append(bot)

    return bots


def get_ursa_bots() -> list[Bot]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM bots
        WHERE search_method IN ('ursa', 'ursa_semantic')
        AND deleted_at IS NULL
    """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    bots: list[Bot] = []
    for row in rows:
        try:
            pdf_parser = PdfParser(row["pdf_parser"])
        except Exception:
            pdf_parser = None
        bot = Bot(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            description=row["description"],
            index_name=row["index_name"],
            container_name=row["container_name"],
            approach=row["approach"],
            example_questions=row["example_questions"],
            search_method=row["search_method"],
            query_generator_model=row["query_generator_model"],
            response_generator_model=row["response_generator_model"],
            pdf_parser=pdf_parser,
            enable_web_browsing=row["enable_web_browsing"],
            data_source_id=row["data_source_id"],
            image_generator_model=row["image_generator_model"] or None,
        )
        bots.append(bot)

    return bots


def get_documents_by_bot_id(bot_id: int) -> list[Document]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM documents
        WHERE bot_id = %s
        AND deleted_at IS NULL
    """,
        (bot_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    documents = []
    for row in rows:
        document = Document(
            id=row["id"],
            bot_id=row["bot_id"],
            basename=row["basename"],
            file_extension=row["file_extension"],
            status=row["status"],
        )
        documents.append(document)

    return documents


def get_documents_by_bot_id_v2(bot_id: int) -> list[Document]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM documents
        JOIN document_folders ON documents.document_folder_id = document_folders.id
        WHERE document_folders.bot_id = %s
        AND documents.deleted_at IS NULL
    """,
        (bot_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    documents = []
    for row in rows:
        document = Document(
            id=row["id"],
            bot_id=row["bot_id"],
            basename=row["basename"],
            file_extension=row["file_extension"],
            status=row["status"],
        )
        documents.append(document)

    return documents


def update_bot_container_name(bot_id: int, container_name: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE bots
        SET container_name = %s
        WHERE id = %s
    """,
        (container_name, bot_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def update_bot_pdf_parser(bot_id: int, pdf_parser: PdfParser) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE bots
        SET pdf_parser = %s
        WHERE id = %s
    """,
        (pdf_parser.value, bot_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def update_bot_data_source_id(bot_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE bots
        SET data_source_id = %s
        WHERE id = %s
    """,
        (str(uuid.uuid4()), bot_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def set_index_name(tenant: Tenant) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tenants
        SET index_name = %s
        WHERE id = %s
    """,
        (tenant.alias, tenant.id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def set_container_name(tenant: Tenant) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tenants
        SET container_name = %s
        WHERE id = %s
    """,
        (tenant.alias, tenant.id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_conversation_turns_without_token_count() -> list[ConversationTurn]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM conversation_turns
        WHERE token_count = 0 AND deleted_at IS NULL
    """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    conversation_turns = []
    for row in rows:
        conversation_turn = ConversationTurn(
            id=row["id"],
            conversation_id=row["conversation_id"],
            user_input=row["user_input"],
            bot_output=row["bot_output"],
            queries=row["queries"],
            query_input_token=row["query_input_token"],
            query_output_token=row["query_output_token"],
            response_input_token=row["response_input_token"],
            response_output_token=row["response_output_token"],
            token_count=row["token_count"],
            query_generator_model=(
                ModelName(str(row["query_generator_model"])) if row["query_generator_model"] is not None else None
            ),
            response_generator_model=ModelName(str(row["response_generator_model"])),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        conversation_turns.append(conversation_turn)

    return conversation_turns


def set_token_count_to_conversation_turn(conversation_turn_id: str, token_count: float) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE conversation_turns
        SET token_count = %s
        WHERE id = %s
    """,
        (token_count, conversation_turn_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_terms_by_bot_id(bot_id: int) -> list[Term]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT * FROM terms
        WHERE bot_id = %s
        AND deleted_at IS NULL
    """,
        (bot_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    terms = []
    for row in rows:
        term = Term(
            id=row["id"],
            bot_id=row["bot_id"],
            name=row["name"],
            description=row["description"],
        )
        terms.append(term)

    return terms


def create_term_v2(bot_id: int, names: list[str], description: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO terms_v2 (id,bot_id, names, description) VALUES (%s,%s, %s, %s)
    """,
        (str(uuid.uuid4()), bot_id, names, description),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def update_bots_response_generator_model_family(
    response_generator_model: ModelName,
    response_generator_model_family: ModelFamily,
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE bots
        SET response_generator_model_family = %s
        WHERE response_generator_model = %s
    """,
        (
            response_generator_model_family.value,
            response_generator_model.value,
        ),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def update_bots_image_generator_model_family(
    image_generator_model: Text2ImageModel,
    image_generator_model_family: Text2ImageModelFamily,
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE bots
        SET image_generator_model_family = %s
        WHERE image_generator_model = %s
    """,
        (
            image_generator_model_family.value,
            image_generator_model.value,
        ),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def update_tenant_allowed_model_families(tenant_id: int, allowed_model_families: list[ModelFamily]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tenants
        SET allowed_model_families = %s
        WHERE id = %s
    """,
        ([model_family.value for model_family in allowed_model_families], tenant_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def update_bot_template_response_generator_model_family(
    bot_template_id: str, response_generator_model_family: ModelFamily
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE bot_templates
        SET response_generator_model_family = %s
        WHERE id = %s
    """,
        (response_generator_model_family.value, bot_template_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_user_and_group_actions() -> list[UserAction]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        WITH
            user_actions AS (
                SELECT
                    user_id
                    , bot_id
                    , CASE WHEN bool_or(action = 'write')
                    THEN 'write' ELSE 'read' END AS action
                FROM users
                JOIN users_policies ON users.id = users_policies.user_id
                WHERE users.deleted_at IS NULL
                    AND users_policies.deleted_at IS NULL
                GROUP BY user_id, bot_id
            )
            , group_actions AS (
                SELECT
                    user_id
                    , bot_id
                    , CASE WHEN bool_or(action = 'write')
                    THEN 'write' ELSE 'read' END AS action
                FROM users_groups
                JOIN groups_policies USING (group_id)
                WHERE groups_policies.deleted_at IS NULL
                    AND users_groups.deleted_at IS NULL
                GROUP BY user_id, bot_id
            )
            , joined_actions AS (
                SELECT
                    COALESCE(user_actions.user_id, group_actions.user_id) AS user_id
                    , COALESCE(user_actions.bot_id, group_actions.bot_id) AS bot_id
                    , user_actions.action AS user_action
                    , group_actions.action AS group_action
                FROM user_actions
                FULL OUTER JOIN group_actions USING (user_id, bot_id)
            )
        SELECT joined_actions.* FROM joined_actions
        JOIN bots ON joined_actions.bot_id = bots.id
        WHERE bots.deleted_at IS NULL
            AND (
                (user_action is null AND group_action is not null)
                OR (user_action = 'read' AND group_action = 'write')
            )
    """,
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        UserAction(
            user_id=row["user_id"],
            bot_id=row["bot_id"],
            user_action=row["user_action"],
            group_action=row["group_action"],
        )
        for row in rows
    ]


def insert_user_policy(user_id: int, bot_id: int, action: Literal["read", "write"]):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users_policies (user_id, bot_id, action)
        VALUES (%s, %s, %s)
    """,
        (user_id, bot_id, action),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def update_user_policy(user_id: int, bot_id: int, action: Literal["read", "write"]):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users_policies
        SET action = %s
        WHERE user_id = %s
            AND bot_id = %s
            AND deleted_at IS NULL
    """,
        (action, user_id, bot_id),
    )
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
