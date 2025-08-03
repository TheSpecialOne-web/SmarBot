import uuid

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import data_point, document, question_answer
from api.domain.models.chat_completion import (
    Id as ChatCompletionId,
    data_point as chat_completion_data_point,
)

from .base import BaseModel
from .chat_completion import ChatCompletion


class ChatCompletionDataPoint(BaseModel):
    __tablename__ = "chat_completion_data_points"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_completion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_completions.id"),
        nullable=False,
    )
    document_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("documents.id"), nullable=True)
    question_answer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_answers.id"), nullable=True
    )
    cite_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_name: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    blob_path: Mapped[str] = mapped_column(String(1023), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    additional_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False, default="internal")

    chat_completion: Mapped[ChatCompletion] = relationship(
        "ChatCompletion",
        back_populates="data_points",
    )

    @classmethod
    def from_domain(
        cls,
        chat_completion_id: ChatCompletionId,
        chat_completion_data_point: chat_completion_data_point.ChatCompletionDataPoint,
    ) -> "ChatCompletionDataPoint":
        return cls(
            id=chat_completion_data_point.id.root,
            chat_completion_id=chat_completion_id.root,
            document_id=(
                chat_completion_data_point.document_id.value
                if chat_completion_data_point.document_id is not None
                else None
            ),
            question_answer_id=(
                chat_completion_data_point.question_answer_id.root
                if chat_completion_data_point.question_answer_id is not None
                else None
            ),
            cite_number=chat_completion_data_point.cite_number.root,
            chunk_name=chat_completion_data_point.chunk_name.root,
            content=chat_completion_data_point.content.root.replace("\x00", ""),
            blob_path=chat_completion_data_point.blob_path.root,
            page_number=chat_completion_data_point.page_number.root,
            additional_info=(
                chat_completion_data_point.additional_info.root
                if chat_completion_data_point.additional_info is not None
                else None
            ),
            url=chat_completion_data_point.url.root if chat_completion_data_point.url is not None else None,
            type=chat_completion_data_point.type.value,
        )

    def to_domain(self) -> chat_completion_data_point.ChatCompletionDataPoint:
        return chat_completion_data_point.ChatCompletionDataPoint(
            id=chat_completion_data_point.Id(root=self.id),
            document_id=document.Id(value=self.document_id) if self.document_id is not None else None,
            question_answer_id=(
                question_answer.Id(root=self.question_answer_id) if self.question_answer_id is not None else None
            ),
            cite_number=data_point.CiteNumber(root=self.cite_number),
            chunk_name=data_point.ChunkName(root=self.chunk_name),
            content=data_point.Content(root=self.content),
            blob_path=data_point.BlobPath(root=self.blob_path),
            page_number=data_point.PageNumber(root=self.page_number),
            additional_info=(
                data_point.AdditionalInfo(root=self.additional_info) if self.additional_info is not None else None
            ),
            url=data_point.Url(root=self.url) if self.url is not None else data_point.Url(root=""),
            type=data_point.Type(self.type),
        )
