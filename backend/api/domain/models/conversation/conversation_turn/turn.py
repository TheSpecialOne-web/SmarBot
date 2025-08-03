from typing import Optional

from pydantic import BaseModel, RootModel

from ...bot.max_conversation_turns import MaxConversationTurns
from ...chat_completion import (
    Content,
    Message as ChatCompletionMessage,
    Role,
)
from ...tenant.basic_ai_max_conversation_turns import BasicAiMaxConversationTurns
from .message import Message


class Turn(BaseModel):
    bot: Optional[Message]
    user: Message


class Turns(RootModel):
    root: list[Turn]

    def cut_by_max_ceonversartion_turns(
        self, max_conversation_turns: MaxConversationTurns | BasicAiMaxConversationTurns | None
    ) -> "Turns":
        if max_conversation_turns is not None:
            return Turns(root=self.root[-max_conversation_turns.root :])
        return self

    def add_turn(self, turn: Turn) -> None:
        self.root.append(turn)

    def to_messages(self) -> list[ChatCompletionMessage]:
        messages = []

        for turn in self.root:
            messages.append(
                ChatCompletionMessage(
                    role=Role.USER,
                    content=Content(root=turn.user.root),
                )
            )
            if turn.bot is not None:
                messages.append(
                    ChatCompletionMessage(
                        role=Role.ASSISTANT,
                        content=Content(root=turn.bot.root),
                    )
                )
        return messages
