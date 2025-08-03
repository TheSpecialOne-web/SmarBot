from typing import Optional

from pydantic import BaseModel, Field

from ..api_key import api_key as api_key_domain
from ..token import TokenCount
from .content import Content
from .created_at import CreatedAt
from .data_point import ChatCompletionDataPoint
from .feedback.feedback import Feedback
from .id import Id, create_id
from .message import Messages


class ChatCompletionForCreate(BaseModel):
    messages: Messages


class ChatCompletionForUpdate(BaseModel):
    messages: Messages
    answer: Content
    token_count: TokenCount
    data_points: list[ChatCompletionDataPoint]


class ChatCompletion(BaseModel):
    id: Id = Field(default_factory=create_id)
    messages: Messages
    answer: Content
    token_count: TokenCount
    data_points: list[ChatCompletionDataPoint]
    feedback: Optional[Feedback] = None
    created_at: CreatedAt | None = None

    @classmethod
    def create_empty(cls) -> "ChatCompletion":
        return cls(
            messages=Messages(root=[]),
            answer=Content(root=""),
            token_count=TokenCount(root=0.0),
            data_points=[],
        )

    def update(self, chat_completion_for_update: ChatCompletionForUpdate) -> None:
        self.messages = chat_completion_for_update.messages
        self.answer = chat_completion_for_update.answer
        self.token_count = chat_completion_for_update.token_count
        self.data_points = chat_completion_for_update.data_points


class ChatCompletionWithApiKeyId(ChatCompletion):
    api_key_id: api_key_domain.Id
