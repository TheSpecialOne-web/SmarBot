from typing import TYPE_CHECKING
import uuid

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    data_point,
    document as document_domain,
)
from api.domain.models.conversation import (
    conversation_data_point as cdt_domain,
    conversation_turn as conversation_turn_domain,
)
from api.domain.models.document import (
    Id as DocumentId,
    feedback as document_feedback_domain,
)
from api.domain.models.question_answer import (
    Answer,
    Id as QuestionAnswerId,
    Question,
)

from .base import BaseModel

if TYPE_CHECKING:
    from .conversation_turn import ConversationTurn
    from .document import Document
    from .question_answer import QuestionAnswer


class ConversationDataPoint(BaseModel):
    __tablename__ = "conversation_data_points"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    turn_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversation_turns.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=True)
    question_answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_answers.id"), nullable=True
    )
    cite_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_name: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    blob_path: Mapped[str] = mapped_column(String(1023), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(255), nullable=False, default="internal")
    url: Mapped[str] = mapped_column(Text, nullable=True)
    additional_info: Mapped[dict] = mapped_column(JSON, nullable=True)

    conversation_turn: Mapped["ConversationTurn"] = relationship(
        "ConversationTurn",
        back_populates="conversation_data_points",
    )

    question_answer: Mapped["QuestionAnswer"] = relationship(
        "QuestionAnswer", back_populates="conversation_data_points"
    )

    document: Mapped["Document"] = relationship("Document", back_populates="conversation_data_points")

    # Define the index
    __table_args__ = (
        Index(
            "idx_turn_id",
            "turn_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    @classmethod
    def from_domain(
        cls,
        domain_model: cdt_domain.ConversationDataPointForCreate,
        turn_id: conversation_turn_domain.Id,
    ) -> "ConversationDataPoint":
        return cls(
            id=domain_model.id.root,
            turn_id=turn_id.root,
            document_id=domain_model.document_id.value if domain_model.document_id else None,
            question_answer_id=domain_model.question_answer_id.root if domain_model.question_answer_id else None,
            cite_number=domain_model.cite_number.root,
            chunk_name=domain_model.chunk_name.root,
            content=domain_model.content.root.replace("\x00", ""),
            blob_path=domain_model.blob_path.root,
            page_number=domain_model.page_number.root,
            type=domain_model.type.value,
            url=domain_model.url.root,
            additional_info=domain_model.additional_info.root if domain_model.additional_info else None,
        )

    def to_domain(self) -> cdt_domain.ConversationDataPoint:
        return cdt_domain.ConversationDataPoint(
            id=cdt_domain.Id(root=self.id),
            turn_id=conversation_turn_domain.Id(root=self.turn_id),
            document_id=DocumentId(value=self.document_id) if self.document_id else None,
            question_answer_id=QuestionAnswerId(root=self.question_answer_id) if self.question_answer_id else None,
            cite_number=data_point.CiteNumber(root=self.cite_number),
            chunk_name=data_point.ChunkName(root=self.chunk_name),
            content=data_point.Content(root=self.content),
            blob_path=data_point.BlobPath(root=self.blob_path),
            page_number=data_point.PageNumber(root=self.page_number),
            type=data_point.Type(self.type),
            url=(data_point.Url(root=self.url) if self.url is not None else data_point.Url(root="")),
            additional_info=(data_point.AdditionalInfo(root=self.additional_info) if self.additional_info else None),
        )

    def to_domain_with_total_good(self, total_good: int) -> cdt_domain.ConversationDataPointWithTotalGood:
        return cdt_domain.ConversationDataPointWithTotalGood(
            id=cdt_domain.Id(root=self.id),
            turn_id=conversation_turn_domain.Id(root=self.turn_id),
            document_id=DocumentId(value=self.document_id) if self.document_id else None,
            question_answer_id=QuestionAnswerId(root=self.question_answer_id) if self.question_answer_id else None,
            cite_number=data_point.CiteNumber(root=self.cite_number),
            chunk_name=data_point.ChunkName(root=self.chunk_name),
            content=data_point.Content(root=self.content),
            blob_path=data_point.BlobPath(root=self.blob_path),
            page_number=data_point.PageNumber(root=self.page_number),
            type=data_point.Type(self.type),
            url=(data_point.Url(root=self.url) if self.url is not None else data_point.Url(root="")),
            additional_info=(data_point.AdditionalInfo(root=self.additional_info) if self.additional_info else None),
            total_good=total_good,
        )

    def to_domain_with_document_feedback_summary(
        self, document_feedback_summary: document_feedback_domain.DocumentFeedbackSummary | None
    ) -> cdt_domain.ConversationDataPointWithDocumentFeedbackSummary:
        return cdt_domain.ConversationDataPointWithDocumentFeedbackSummary(
            id=cdt_domain.Id(root=self.id),
            turn_id=conversation_turn_domain.Id(root=self.turn_id),
            document_id=DocumentId(value=self.document_id) if self.document_id else None,
            question_answer_id=QuestionAnswerId(root=self.question_answer_id) if self.question_answer_id else None,
            cite_number=data_point.CiteNumber(root=self.cite_number),
            chunk_name=data_point.ChunkName(root=self.chunk_name),
            content=data_point.Content(root=self.content),
            blob_path=data_point.BlobPath(root=self.blob_path),
            page_number=data_point.PageNumber(root=self.page_number),
            type=data_point.Type(self.type),
            url=(data_point.Url(root=self.url) if self.url is not None else data_point.Url(root="")),
            additional_info=(data_point.AdditionalInfo(root=self.additional_info) if self.additional_info else None),
            document_feedback_summary=document_feedback_summary,
        )

    def to_domain_with_detail(self) -> cdt_domain.ConversationDataPointWithDetail:
        return cdt_domain.ConversationDataPointWithDetail(
            id=cdt_domain.Id(root=self.id),
            turn_id=conversation_turn_domain.Id(root=self.turn_id),
            document_id=DocumentId(value=self.document_id) if self.document_id else None,
            question_answer_id=QuestionAnswerId(root=self.question_answer_id) if self.question_answer_id else None,
            cite_number=data_point.CiteNumber(root=self.cite_number),
            chunk_name=data_point.ChunkName(root=self.chunk_name),
            content=data_point.Content(root=self.content),
            blob_path=data_point.BlobPath(root=self.blob_path),
            page_number=data_point.PageNumber(root=self.page_number),
            type=data_point.Type(self.type),
            url=(data_point.Url(root=self.url) if self.url is not None else data_point.Url(root="")),
            additional_info=(data_point.AdditionalInfo(root=self.additional_info) if self.additional_info else None),
            document_name=document_domain.Name(value=self.document.basename) if self.document is not None else None,
            document_file_extension=(
                document_domain.FileExtension(self.document.file_extension) if self.document is not None else None
            ),
            document_folders=(
                [
                    document_folder_path.ancestor.to_domain_with_order(document_folder_path.path_length)
                    for document_folder_path in self.document.document_folder.ancestors
                ]
                if self.document is not None
                else None
            ),
            question=(Question(root=self.question_answer.question) if self.question_answer is not None else None),
            answer=(Answer(root=self.question_answer.answer) if self.question_answer is not None else None),
        )
