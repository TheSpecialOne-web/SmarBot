from typing import Optional

from pydantic import BaseModel, Field

from ..bot import (
    Bot,
    Id as BotId,
    Name as BotName,
)
from ..user import (
    Id as UserId,
    Name as UserName,
)
from .conversation_turn.conversation_turn import (
    ConversationTurn,
    ConversationTurnWithAttachments,
)
from .id import Id, create_id
from .title import Title


class ConversationProps(BaseModel):
    title: Optional[Title]
    user_id: UserId
    bot_id: BotId


class Conversation(ConversationProps):
    id: Id


class ConversationForCreate(BaseModel):
    id: Id = Field(default_factory=create_id)
    user_id: UserId
    bot_id: BotId
    title: Optional[Title] = None


class ConversationWithBot(ConversationProps):
    id: Id
    bot: Bot
    turns: list[ConversationTurn]


class ConversationWithUserAndBot(Conversation):
    user_name: UserName
    bot_name: BotName


class ConversationWithAttachments(ConversationProps):
    id: Id
    conversation_turns: list[ConversationTurnWithAttachments]
