from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    bot as bot_domain,
    question_answer as question_answer_domain,
)

from .base import BaseModel

if TYPE_CHECKING:
    from .conversation_data_point import ConversationDataPoint

question_answer_status = ENUM(
    "pending", "indexed", "failed", "overwriting", name="question_answer_status", create_type=False
)


class QuestionAnswer(BaseModel):
    __tablename__ = "question_answers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(question_answer_status, server_default="pending", nullable=False)

    conversation_data_points: Mapped[list["ConversationDataPoint"]] = relationship(
        "ConversationDataPoint",
        back_populates="question_answer",
    )

    @classmethod
    def from_domain(
        cls,
        domain_model: question_answer_domain.QuestionAnswerForCreate,
        bot_id: bot_domain.Id,
    ):
        return cls(
            id=domain_model.id.root,
            bot_id=bot_id.value,
            question=domain_model.question.root,
            answer=domain_model.answer.root,
            status=domain_model.status,
        )

    def to_domain(self) -> question_answer_domain.QuestionAnswer:
        id = question_answer_domain.Id(root=self.id)
        question = question_answer_domain.Question(root=self.question)
        answer = question_answer_domain.Answer(root=self.answer)
        updated_at = question_answer_domain.UpdatedAt(root=self.updated_at)
        status = question_answer_domain.Status(self.status)
        return question_answer_domain.QuestionAnswer(
            id=id, question=question, answer=answer, updated_at=updated_at, status=status
        )
