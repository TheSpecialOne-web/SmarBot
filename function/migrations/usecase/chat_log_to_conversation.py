import uuid

from migrations.infrastructure.postgres import (
    ChatLog,
    Conversation,
    ConversationTurn,
    create_conversation_turns,
    create_conversations,
    get_chat_logs,
)


def filter_chat_logs_by_chat_id(chat_logs: list[ChatLog], chat_id: str) -> list[ChatLog]:
    ret = []
    for chat_log in chat_logs:
        if chat_log.chat_id == chat_id:
            ret.append(chat_log)
    return ret


def migrate_chat_log_to_conversation():
    try:
        chat_logs = get_chat_logs()
    except Exception as e:
        raise Exception(f"failed to get chat logs: {e}")

    chat_ids = list({chat_log.chat_id for chat_log in chat_logs})
    conversations: list[Conversation] = []  # type: ignore[annotation-unchecked]
    conversation_turns: list[ConversationTurn] = []  # type: ignore[annotation-unchecked]
    for chat_id in chat_ids:
        filtered_chat_logs = filter_chat_logs_by_chat_id(chat_logs, chat_id)
        conversations.append(
            Conversation(
                id=chat_id,  # chat_id を conversation.id に使う
                title="",
                # 以下は chat_logs に含まれる最初のログのものを使う
                user_id=filtered_chat_logs[0].user_id,
                bot_id=filtered_chat_logs[0].bot_id,
                created_at=filtered_chat_logs[0].created_at,
                updated_at=filtered_chat_logs[0].updated_at,
            )
        )
        for chat_log in filtered_chat_logs:
            conversation_turns.append(
                ConversationTurn(
                    id=str(uuid.uuid4()),
                    conversation_id=chat_id,
                    user_input=chat_log.user_input,
                    bot_output=chat_log.bot_output,
                    queries=chat_log.queries,
                    query_input_token=chat_log.query_input_token,
                    query_output_token=chat_log.query_output_token,
                    response_input_token=chat_log.response_input_token,
                    response_output_token=chat_log.response_output_token,
                    query_generator_model=chat_log.query_generator_model,
                    response_generator_model=chat_log.response_generator_model,
                    created_at=chat_log.created_at,
                    updated_at=chat_log.updated_at,
                )
            )

    try:
        create_conversations(conversations)
    except Exception as e:
        raise Exception(f"failed to create conversations: {e}")

    try:
        create_conversation_turns(conversation_turns)
    except Exception as e:
        raise Exception(f"failed to create conversation turns: {e}")
