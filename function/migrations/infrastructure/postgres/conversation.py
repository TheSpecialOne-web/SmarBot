from datetime import datetime

from sqlalchemy import select, update

from libs.session import Session

from .models.conversation import Conversation as ConversationModel
from .models.conversation_turn import ConversationTurn as ConversationTurnModel
from .postgres import Conversation, ConversationTurn, ModelName


def get_conversations_by_bot_id(
    bot_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
) -> list[Conversation]:
    with Session() as session:
        conversations = (
            session.execute(
                select(ConversationModel)
                .where(ConversationModel.bot_id == bot_id)
                .outerjoin(ConversationTurnModel, ConversationModel.id == ConversationTurnModel.conversation_id)
                .where(ConversationTurnModel.created_at >= start_datetime)
                .where(ConversationTurnModel.created_at <= end_datetime)
            )
            .scalars()
            .all()
        )
        return [
            Conversation(
                id=str(conversation.id),
                title=conversation.title or "",
                bot_id=conversation.bot_id,
                user_id=conversation.user_id,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                turns=[
                    ConversationTurn(
                        id=str(turn.id),
                        conversation_id=str(turn.conversation_id),
                        user_input=turn.user_input,
                        bot_output=turn.bot_output,
                        queries=turn.queries,
                        query_input_token=turn.query_input_token,
                        query_output_token=turn.query_output_token,
                        response_input_token=turn.response_input_token,
                        response_output_token=turn.response_output_token,
                        token_count=turn.token_count,
                        query_generator_model=ModelName(turn.query_generator_model),
                        response_generator_model=ModelName(turn.response_generator_model),
                        created_at=turn.created_at,
                        updated_at=turn.updated_at,
                    )
                    for turn in conversation.conversation_turns
                ],
            )
            for conversation in conversations
        ]


def update_conversation_turn_token_count(
    conversation_turn_id: str,
    token_count: float,
) -> None:
    with Session() as session:
        session.execute(
            update(ConversationTurnModel)
            .where(ConversationTurnModel.id == conversation_turn_id)
            .values(token_count=token_count)
        )
        session.commit()
