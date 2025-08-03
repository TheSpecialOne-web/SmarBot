from typing import TYPE_CHECKING
import uuid

from sqlalchemy import JSON, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import api_key, chat_completion, token
from api.domain.models.api_key import Id as ApiKeyId

from .base import BaseModel

if TYPE_CHECKING:
    from .api_key import ApiKey
    from .chat_completion_data_point import ChatCompletionDataPoint


class ChatCompletion(BaseModel):
    __tablename__ = "chat_completions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False)
    messages: Mapped[dict] = mapped_column(JSON, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[float] = mapped_column(Float, nullable=False)
    evaluation: Mapped[str] = mapped_column(Text, nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    data_points: Mapped[list["ChatCompletionDataPoint"]] = relationship(
        "ChatCompletionDataPoint", back_populates="chat_completion", lazy="joined"
    )
    api_key: Mapped["ApiKey"] = relationship(
        "ApiKey",
        back_populates="chat_completions",
    )

    @classmethod
    def from_domain(
        cls,
        api_key_id: ApiKeyId,
        chat_completion: chat_completion.ChatCompletion,
    ) -> "ChatCompletion":
        return cls(
            id=chat_completion.id.root,
            api_key_id=api_key_id.root,
            messages={"messages": [message.model_dump() for message in chat_completion.messages.root]},
            answer=chat_completion.answer.root,
            token_count=chat_completion.token_count.root,
        )

    def to_domain(self) -> chat_completion.ChatCompletion:
        return chat_completion.ChatCompletion(
            id=chat_completion.Id(root=self.id),
            messages=chat_completion.Messages(
                root=[
                    chat_completion.Message(
                        role=chat_completion.Role(message["role"]),
                        content=chat_completion.Content(root=message["content"]),
                    )
                    for message in self.messages["messages"]
                ]
            ),
            answer=chat_completion.Content(root=self.answer),
            token_count=token.TokenCount(root=self.token_count),
            data_points=[data_point.to_domain() for data_point in self.data_points],
            created_at=chat_completion.CreatedAt(root=self.created_at),
            feedback=(
                chat_completion.Feedback(
                    evaluation=chat_completion.Evaluation(self.evaluation) if self.evaluation else None,
                    comment=chat_completion.Comment(root=self.comment) if self.comment else None,
                )
                if self.evaluation or self.comment
                else None
            ),
        )

    def to_domain_with_api_key_id(self) -> chat_completion.ChatCompletionWithApiKeyId:
        return chat_completion.ChatCompletionWithApiKeyId(
            api_key_id=api_key.Id(root=self.api_key_id),
            **self.to_domain().model_dump(),
        )
